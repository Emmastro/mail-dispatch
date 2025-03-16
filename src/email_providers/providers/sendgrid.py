import base64
from typing import Dict, Any, List, Optional

import sendgrid
from fastapi import HTTPException
from pydantic import EmailStr
from python_http_client import HTTPError
from sendgrid import Email, To, Content, Mail, Attachment as SGAttachment

from src.email_providers import BaseEmailProvider, TemplateRenderer, logger

class SendGridEmailProvider(BaseEmailProvider):
    """Email service using SendGrid."""

    def __init__(
            self,
            template_renderer: TemplateRenderer,
            api_key: str,
            sender_email: str
    ) -> None:
        """Initialize the SendGrid email client.

        Args:
            template_renderer: Template renderer instance
            api_key: SendGrid API key
            sender_email: Email address to send from
        """
        super().__init__(template_renderer)
        self.api_key = api_key
        self.sender_email = sender_email

        try:
            self.client = sendgrid.SendGridAPIClient(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize SendGrid client: {str(e)}")
            self.client = None

    @classmethod
    def from_config(cls, template_renderer: TemplateRenderer, config: Dict[str, Any]) -> 'SendGridEmailProvider':
        """Create an instance from configuration dictionary.
        # TODO: the config Dict should be a pydantic basemodel and require all relevant fields.
        Args:
            template_renderer: Template renderer instance
            config: Configuration dictionary

        Returns:
            Configured SendGridEmailProvider instance
        """
        return cls(
            template_renderer=template_renderer,
            api_key=config.get("EMAIL_SENDGRID_API_KEY", ""),
            sender_email=config.get("EMAIL_DEFAULT_FROM_EMAIL", "")
        )

    async def send_email(
            self,
            to_emails: List[EmailStr],
            subject: str,
            html_content: str,
            cc_emails: Optional[List[EmailStr]] = None,
            bcc_emails: Optional[List[EmailStr]] = None,
            attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send an email via SendGrid.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML content of the email
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            attachments: List of attachments

        Returns:
            Dictionary with message_id and status

        Raises:
            HTTPException: If email fails to send
        """
        if not self.client:
            logger.error("SendGrid client is not initialized")
            raise HTTPException(status_code=500, detail="Email service is not available")

        try:
            from_email = Email(self.sender_email)
            to_email = [To(email) for email in to_emails]
            content = Content("text/html", html_content)
            mail = Mail(from_email=from_email, subject=subject, to_emails=to_email, html_content=content)

            if cc_emails:
                for cc_email in cc_emails:
                    mail.add_cc(Email(cc_email))

            if bcc_emails:
                for bcc_email in bcc_emails:
                    mail.add_bcc(Email(bcc_email))

            if attachments:
                for attachment_data in attachments:
                    attachment = SGAttachment()
                    attachment.file_content = base64.b64encode(attachment_data.get("content", b"")).decode()
                    attachment.file_name = attachment_data.get("filename", "attachment.txt")
                    attachment.file_type = attachment_data.get("content_type", "text/plain")
                    attachment.disposition = "attachment"
                    mail.add_attachment(attachment)

            # Send the email
            response = self.client.send(mail)

            logger.info(f"Email sent to {', '.join(to_emails)}, Status: {response.status_code}")
            return {
                "message_id": response.headers.get('X-Message-Id', 'unknown'),
                "status": "sent" if 200 <= response.status_code < 300 else "failed"
            }

        except HTTPError as e:
            logger.error(f"SendGrid API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    async def send_template_email(
            self,
            to_emails: List[EmailStr],
            template_name: str,
            template_data: Dict[str, Any],
            subject: Optional[str] = None,
            cc_emails: Optional[List[EmailStr]] = None,
            bcc_emails: Optional[List[EmailStr]] = None
    ) -> Dict[str, Any]:
        """Send a templated email via SendGrid.

        Args:
            to_emails: List of recipient email addresses
            template_name: Name of the template
            template_data: Data for template rendering
            subject: Email subject (optional)
            cc_emails: List of CC email addresses (optional)
            bcc_emails: List of BCC email addresses (optional)

        Returns:
            Dictionary with message_id and status
        """
        html_content = self.template_renderer.render_template(template_name, template_data)
        if not subject:
            subject = self._get_default_subject()

        return await self.send_email(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails
        )
