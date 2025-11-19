import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.tasks.celery_app import celery_app


@celery_app.task(name="send_email", max_retries=3, default_retry_delay=30)
def send_email(to_email: str, subject: str, html_content: str, text_content: str = ""):
    """
    Send email via SMTP.

    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text fallback
    """

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email

        # Add text and HTML parts
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)

        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Send email
        # Only send if SMTP settings are configured
        if settings.SMTP_HOST and settings.SMTP_PORT:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
            return {"status": "sent", "to": to_email}
        else:
            print(f"Mock sending email to {to_email}: {subject}")
            return {"status": "mock_sent", "to": to_email}

    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        raise


@celery_app.task(name="send_verification_email")
def send_verification_email(user_email: str, verification_token: str):
    """Send email verification email"""

    verification_url = (
        f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                background-color: #4CAF50; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 4px;
                display: inline-block;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Welcome to ExamAI Pro!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
            <p>
                <a href="{verification_url}" class="button">Verify Email</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Welcome to ExamAI Pro!
    
    Please verify your email by visiting: {verification_url}
    
    This link will expire in 24 hours.
    """

    return send_email.delay(
        to_email=user_email,
        subject="Verify your ExamAI Pro account",
        html_content=html_content,
        text_content=text_content,
    )


@celery_app.task(name="send_exam_ready_notification")
def send_exam_ready_notification(user_email: str, exam_title: str, exam_id: str):
    """Send notification when exam generation is complete"""

    exam_url = f"{settings.FRONTEND_URL}/exams/{exam_id}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Your study notes are ready! 📚</h2>
            <p>Great news! Your AI-generated study notes for <strong>{exam_title}</strong> are now available.</p>
            <p>
                <a href="{exam_url}" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                    View Study Notes
                </a>
            </p>
            <p>Start studying now and ace your exam!</p>
            <p>Good luck!</p>
            <p>- ExamAI Pro Team</p>
        </div>
    </body>
    </html>
    """

    return send_email.delay(
        to_email=user_email,
        subject=f"Your study notes for '{exam_title}' are ready!",
        html_content=html_content,
    )
