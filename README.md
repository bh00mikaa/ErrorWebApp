# System Alert Dashboard

## Overview
The System Alert Dashboard is a lightweight, self-hosted Flask web application designed to provide immediate email notifications for critical system events or errors. It offers a simple, intuitive interface for managing a list of email recipients and sending out alerts with a customizable message. This project is ideal for small-scale monitoring, personal projects, or environments where a quick and easy alert system is needed without relying on complex external services.

## Features
* **Email Alerting:** Send system alerts to a predefined list of recipients via email.
* **Recipient Management:** Easily add or remove email addresses through a simple web interface.
* **Secure Configuration:** Utilizes `.env` files for securely loading sensitive information (sender email credentials, secret keys), keeping them out of your codebase.
* **Input Validation:** Basic validation for email formats and message length to ensure reliable operation.
* **Flask-based:** Built with Flask, offering a familiar and extensible framework for web development.


