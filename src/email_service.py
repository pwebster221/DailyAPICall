"""Email service for sending daily astrological insights"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime
import structlog
from src.config import settings
from src.models import EmailContent

logger = structlog.get_logger(__name__)


class EmailService:
    """Service for sending formatted emails via SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.email_from
        self.to_email = settings.email_to
    
    async def send_daily_insight(
        self,
        email_content: EmailContent,
        additional_recipients: Optional[List[str]] = None
    ) -> bool:
        """
        Send the daily astrological insight email
        
        Args:
            email_content: Formatted email content from OpenAI assistant
            additional_recipients: Optional list of additional recipients
        
        Returns:
            True if email sent successfully, False otherwise
        """
        logger.info(
            "Sending daily insight email",
            subject=email_content.subject,
            to=self.to_email
        )
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = email_content.subject
            message["From"] = self.from_email
            
            # Set recipients
            recipients = [self.to_email]
            if additional_recipients:
                recipients.extend(additional_recipients)
            message["To"] = ", ".join(recipients)
            
            # Add timestamp header
            message["X-Sacred-Journey-Date"] = datetime.now().isoformat()
            
            # Create plain text and HTML parts
            text_part = MIMEText(email_content.plain_text, "plain")
            html_part = MIMEText(email_content.full_html, "html")
            
            # Attach parts
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True
            )
            
            logger.info(
                "Email sent successfully",
                recipients_count=len(recipients)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send email",
                error=str(e),
                subject=email_content.subject
            )
            return False
    
    async def send_error_notification(
        self,
        error_message: str,
        stage: str,
        execution_id: str
    ) -> bool:
        """
        Send error notification to administrators
        
        Args:
            error_message: Description of the error
            stage: Pipeline stage where error occurred
            execution_id: Pipeline execution ID
        
        Returns:
            True if notification sent successfully
        """
        logger.info("Sending error notification")
        
        try:
            message = MIMEMultipart()
            message["Subject"] = f"[Sacred Journey Pipeline Error] {stage} Failed"
            message["From"] = self.from_email
            message["To"] = self.from_email  # Send to self for admin notification
            
            body = f"""
            Sacred Journey Pipeline Error Report
            =====================================
            
            Execution ID: {execution_id}
            Failed Stage: {stage}
            Timestamp: {datetime.now().isoformat()}
            
            Error Details:
            {error_message}
            
            Please check the logs for more information.
            The pipeline will retry according to the configured retry policy.
            
            ---
            This is an automated notification from the Sacred Journey Pipeline.
            """
            
            message.attach(MIMEText(body, "plain"))
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True
            )
            
            logger.info("Error notification sent")
            return True
            
        except Exception as e:
            logger.error("Failed to send error notification", error=str(e))
            return False
    
    async def send_test_email(self) -> bool:
        """
        Send a test email to verify configuration
        
        Returns:
            True if test email sent successfully
        """
        logger.info("Sending test email")
        
        try:
            message = MIMEMultipart()
            message["Subject"] = "Sacred Journey Pipeline - Test Email"
            message["From"] = self.from_email
            message["To"] = self.to_email
            
            body = """
            This is a test email from the Sacred Journey Pipeline.
            
            If you're receiving this, your email configuration is working correctly!
            
            Configuration Details:
            - SMTP Host: {}
            - SMTP Port: {}
            - From: {}
            - To: {}
            
            The pipeline is ready to send daily astrological insights.
            
            Blessed be your journey,
            Sacred Journey Pipeline
            """.format(
                self.smtp_host,
                self.smtp_port,
                self.from_email,
                self.to_email
            )
            
            message.attach(MIMEText(body, "plain"))
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True
            )
            
            logger.info("Test email sent successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to send test email", error=str(e))
            return False


class EmailTemplates:
    """HTML email templates for beautiful formatting"""
    
    @staticmethod
    def get_base_template() -> str:
        """Get the base HTML template"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
            <style>
                body {{
                    font-family: 'Georgia', serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #764ba2;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #667eea;
                    margin-top: 30px;
                }}
                .transit {{
                    background: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .archetype {{
                    display: inline-block;
                    background: #764ba2;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 20px;
                    margin: 5px;
                    font-size: 0.9em;
                }}
                .guidance {{
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
                .meditation {{
                    background: #f0f4f8;
                    border: 2px dashed #667eea;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    font-style: italic;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 0.9em;
                }}
                .symbol {{
                    font-size: 1.5em;
                    color: #764ba2;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {content}
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def format_daily_insight(email_content: EmailContent) -> str:
        """Format the daily insight with the template"""
        content = f"""
        <h1>{email_content.greeting}</h1>
        
        <div class="overview">
            <h2>Today's Cosmic Weather</h2>
            <p>{email_content.daily_overview}</p>
        </div>
        
        <div class="transits">
            <h2>Planetary Movements</h2>
            {"".join(f'<div class="transit">{transit}</div>' for transit in email_content.transit_narratives)}
        </div>
        
        <div class="archetypes">
            <h2>Activated Archetypes</h2>
            <p>{email_content.archetypal_insights}</p>
        </div>
        
        <div class="guidance">
            <h2>Practical Guidance</h2>
            <p>{email_content.practical_guidance}</p>
        </div>
        """
        
        if email_content.meditation_suggestion:
            content += f"""
            <div class="meditation">
                <h2>Today's Meditation</h2>
                <p>{email_content.meditation_suggestion}</p>
            </div>
            """
        
        content += f"""
        <div class="footer">
            <p>{email_content.closing}</p>
            <p>Sacred Journey • Daily Astrological Insights</p>
        </div>
        """
        
        template = EmailTemplates.get_base_template()
        return template.format(
            subject=email_content.subject,
            content=content
        )
