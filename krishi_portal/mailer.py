import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(recipient, subject, body, reply_to=None, attachment=None):
    """Send an email through the configured SMTP account."""
    config = current_app.config
    username = config["SMTP_USERNAME"]
    password = config["SMTP_PASSWORD"]
    if not all((config["SMTP_HOST"], username, password, recipient)):
        current_app.logger.warning("SMTP email skipped: SMTP credentials are incomplete.")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = username
    message["To"] = recipient
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(body)
    if attachment:
        path, filename, mime_type = attachment
        maintype, subtype = mime_type.split("/", 1)
        with open(path, "rb") as file:
            message.add_attachment(file.read(), maintype=maintype, subtype=subtype, filename=filename)

    try:
        smtp_class = smtplib.SMTP_SSL if config["SMTP_USE_SSL"] else smtplib.SMTP
        with smtp_class(config["SMTP_HOST"], config["SMTP_PORT"], timeout=15) as smtp:
            if config["SMTP_USE_TLS"] and not config["SMTP_USE_SSL"]:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        current_app.logger.exception("Unable to deliver SMTP notification.")
        return False


def send_admin_email(subject, body, reply_to=None):
    return send_email(current_app.config["ADMIN_EMAIL"], subject, body, reply_to=reply_to)
