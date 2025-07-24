import os
import secrets
import re
from flask import Flask, render_template, request, redirect, url_for, flash
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# SECURE: Load secret key from environment or generate a secure one
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    # Generate a secure random key if not provided
    app.secret_key = secrets.token_hex(32)
    print("⚠️  WARNING: Using auto-generated secret key. Set FLASK_SECRET_KEY in .env for production!")

# SECURE: Load sensitive data from environment variables
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
CLIENT_FILE = os.environ.get('CLIENT_FILE', 'clients.txt')  # Allow customization

def validate_config():
    """Validate that required environment variables are set."""
    missing_vars = []
    if not SENDER_EMAIL:
        missing_vars.append('SENDER_EMAIL')
    if not SENDER_PASSWORD:
        missing_vars.append('SENDER_PASSWORD')
    
    if missing_vars:
        print("❌ CONFIGURATION ERROR:")
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease create a .env file with:")
        for var in missing_vars:
            print(f"{var}=your_value_here")
        print("\nExample .env file structure:")
        print("FLASK_SECRET_KEY=your_secure_random_key")
        print("SENDER_EMAIL=your_email@gmail.com")
        print("SENDER_PASSWORD=your_app_password")
        exit(1)

def validate_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_recipients():
    """Get list of email recipients from file."""
    if not os.path.exists(CLIENT_FILE):
        return []
    try:
        with open(CLIENT_FILE, "r", encoding='utf-8') as f:
            recipients = [line.strip() for line in f.readlines() if line.strip()]
            # Filter out any invalid emails that might have been saved
            return [email for email in recipients if validate_email(email)]
    except Exception as e:
        print(f"❌ Error reading client file: {e}")
        return []

def save_recipients(recipients):
    """Save recipients list to file."""
    try:
        # Remove duplicates while preserving order, then sort
        unique_emails = list(dict.fromkeys(recipients))
        unique_emails.sort(key=str.lower)
        
        with open(CLIENT_FILE, "w", encoding='utf-8') as f:
            f.write("\n".join(unique_emails))
        
        print(f"✅ Updated client list: {len(unique_emails)} recipients")
        return True
    except Exception as e:
        print(f"❌ Error saving client file: {e}")
        return False

def send_email_to_all(message):
    """Send email alert to all recipients."""
    recipients = get_recipients()
    if not recipients:
        raise ValueError("No recipients configured. Please add recipients first.")

    msg = EmailMessage()
    msg['Subject'] = f"System Alert: {message[:50]}{'...' if len(message) > 50 else ''}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients)
    msg.set_content(f"System Alert Notification:\n\n{message}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent successfully to {len(recipients)} recipient(s)")
    except smtplib.SMTPAuthenticationError:
        raise ValueError("Email authentication failed. Please check your Gmail App Password.")
    except smtplib.SMTPException as e:
        raise ValueError(f"SMTP error occurred: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error sending email: {str(e)}")

# Validate configuration on startup
validate_config()

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html', sender=SENDER_EMAIL, recipients=get_recipients())

@app.route('/send-alert', methods=['POST'])
def trigger_email():
    """Handle sending email alerts."""
    message = request.form.get('error', '').strip()
    
    if not message:
        flash("Error: Message cannot be empty.", "error")
        return redirect(url_for('index'))
    
    if len(message) > 5000:  # Reasonable limit for email content
        flash("Error: Message is too long (max 5000 characters).", "error")
        return redirect(url_for('index'))

    recipients = get_recipients()
    if not recipients:
        flash("Error: No recipients configured. Please add recipients first.", "error")
        return redirect(url_for('index'))

    try:
        send_email_to_all(message)
        flash(f"Alert sent successfully to {len(recipients)} recipient(s)!", "success")
    except Exception as e:
        flash(f"Failed to send email: {str(e)}", "error")
        print(f"❌ Email send error: {e}")
    
    return redirect(url_for('index'))

@app.route('/update-clients', methods=['POST'])
def update_clients():
    """Handle adding/removing email recipients."""
    new_email = request.form.get('new_email', '').strip().lower()
    remove_email = request.form.get('remove_email', '').strip().lower()
    current_emails = get_recipients()
    changed = False

    # Add new email
    if new_email:
        # Validate email format
        if not validate_email(new_email):
            flash(f"Invalid email format: {new_email}", "error")
        elif new_email.lower() in [email.lower() for email in current_emails]:
            flash(f"{new_email} is already in the recipient list.", "error")
        else:
            current_emails.append(new_email)
            flash(f"Added {new_email} to the recipient list.", "success")
            changed = True

    # Remove email
    if remove_email:
        original_count = len(current_emails)
        current_emails = [email for email in current_emails if email.lower() != remove_email]
        
        if len(current_emails) < original_count:
            flash(f"Removed {remove_email} from the recipient list.", "success")
            changed = True
        else:
            flash(f"{remove_email} was not found in the recipient list.", "error")

    # Save changes
    if changed:
        if save_recipients(current_emails):
            pass  # Success message already shown above
        else:
            flash("Error saving recipient list. Please try again.", "error")

    return redirect(url_for('index'))

@app.route('/delete-clients')
def delete_clients():
    """Delete all recipients."""
    try:
        if os.path.exists(CLIENT_FILE):
            os.remove(CLIENT_FILE)
            flash("All recipients deleted successfully.", "success")
            print("✅ Client list deleted")
        else:
            flash("No recipient list found to delete.", "error")
    except Exception as e:
        flash(f"Error deleting recipient list: {str(e)}", "error")
        print(f"❌ Error deleting client file: {e}")
    
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    flash("An internal error occurred. Please try again.", "error")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=5050, 
        debug=os.environ.get('FLASK_ENV') == 'development'
    )