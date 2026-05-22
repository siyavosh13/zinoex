import smtplib
import random
import string
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


def generate_verification_code() -> str:
    """Generate a 6-digit verification code."""
    return ''.join(random.choices(string.digits, k=6))


async def send_verification_email(email: str, code: str) -> None:
    """Send verification email with 6-digit code."""
    try:
        # ساخت پیام
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your Verification Code"
        msg["From"] = settings.SMTP_USER
        msg["To"] = email

        # متن ساده
        text_content = f"""
Your verification code is: {code}

This code expires in 10 minutes.
If you did not request this, please ignore this email.
        """

        # متن HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                padding: 40px; border-radius: 12px; text-align: center;">
        
        <h1 style="color: #4ade80; margin-bottom: 10px;">Verification Code</h1>
        <p style="color: #94a3b8; margin-bottom: 30px;">
            Enter this code to verify your account
        </p>
        
        <div style="background: rgba(74, 222, 128, 0.1); 
                    border: 2px solid #4ade80;
                    border-radius: 12px; 
                    padding: 20px 40px; 
                    display: inline-block;
                    margin-bottom: 30px;">
            <span style="font-size: 42px; 
                         font-weight: bold; 
                         color: #4ade80; 
                         letter-spacing: 12px;">
                {code}
            </span>
        </div>
        
        <p style="color: #64748b; font-size: 14px;">
            ⏱ This code expires in <strong style="color: #f59e0b;">10 minutes</strong>
        </p>
        <p style="color: #64748b; font-size: 12px; margin-top: 20px;">
            If you did not create an account, please ignore this email.
        </p>
    </div>
</body>
</html>
        """

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # ✅ اتصال با STARTTLS (پورت 587) - برای Gmail/Outlook/...
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()   # 🔐 رمزنگاری
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, email, msg.as_string())

        logger.info(f"Verification email sent successfully to {email}")

    except smtplib.SMTPAuthenticationError:
        logger.error(f"SMTP Authentication failed for {email}")
        raise Exception("Email authentication failed. Check SMTP credentials.")

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {email}: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error sending email to {email}: {str(e)}")
        raise Exception(f"Email service error: {str(e)}")
