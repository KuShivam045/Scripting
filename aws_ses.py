import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# AWS SES SMTP server configuration
SMTP_SERVER = 'email-smtp.ap-south-1.amazonaws.com'
SMTP_PORT = 587  # Use 587 for TLS
USERNAME = 'Your_AWS_ACCESS_KEY_ID'
PASSWORD = 'Your_AWS_SECRET_ACCESS_KEY'

# Make sure to replace this with a VERIFIED email address
SENDER = 'shivam@mail.shivaay.cloud'  # Replace with your verified email address

# Email content
SUBJECT = "Bulk Email Example"
BODY = """Dear User,

This is a bulk email test using AWS SES SMTP.

Best Regards,
Your Company
"""

# List of recipient emails
recipient_list = [
    'shivaay6668@gmail.com',
    'kushivam045@gmail.com',
    'kumarshivam1211953@gmail.com',
    'kumarshivam9318@gmail.com',
    # Add more emails as needed
]

def send_bulk_email():
    try:
        # Establish an SMTP connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(USERNAME, PASSWORD)
        
        for recipient in recipient_list:
            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = SENDER
            msg['To'] = recipient
            msg['Subject'] = SUBJECT

            # Attach the email body
            msg.attach(MIMEText(BODY, 'plain'))

            # Convert the message to string
            email_message = msg.as_string()

            # Send the email
            server.sendmail(SENDER, recipient, email_message)
            print(f"Email sent to {recipient}")
        
        # Close the SMTP connection
        server.quit()

    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    send_bulk_email()
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# AWS SES SMTP server configuration
SMTP_SERVER = 'email-smtp.ap-south-1.amazonaws.com'
SMTP_PORT = 587  # Use 587 for TLS
USERNAME = 'Your_AWS_ACCESS_KEY_ID'
PASSWORD = 'Your_AWS_SECRET_ACCESS_KEY'

# Make sure to replace this with a VERIFIED email address
SENDER = 'shivam@mail.shivaay.cloud'  # Replace with your verified email address

# Email content
SUBJECT = "Bulk Email Example"
BODY = """Dear User,

This is a bulk email test using AWS SES SMTP.

Best Regards,
Your Company
"""

# List of recipient emails
recipient_list = [
    'shivaay6668@gmail.com',
    'kushivam045@gmail.com',
    'kumarshivam1211953@gmail.com',
    'kumarshivam9318@gmail.com',
    # Add more emails as needed
]

def send_bulk_email():
    try:
        # Establish an SMTP connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(USERNAME, PASSWORD)
        
        for recipient in recipient_list:
            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = SENDER
            msg['To'] = recipient
            msg['Subject'] = SUBJECT

            # Attach the email body
            msg.attach(MIMEText(BODY, 'plain'))

            # Convert the message to string
            email_message = msg.as_string()

            # Send the email
            server.sendmail(SENDER, recipient, email_message)
            print(f"Email sent to {recipient}")
        
        # Close the SMTP connection
        server.quit()

    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    send_bulk_email()
