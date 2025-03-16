from typing import Dict, Any, List, Optional

from azure.communication.email import EmailClient
from fastapi import HTTPException
from pydantic import EmailStr

from src.email_providers.base import BaseEmailProvider, TemplateRenderer
import logging

logger = logging.getLogger(__name__)

class AzureEmailProvider(BaseEmailProvider):
    """Email service using Azure Communication Services."""

    def __init__(
            self,
            template_renderer: TemplateRenderer,
            connection_string: str,
            sender_address: str
    ) -> None:
        """Initialize the Azure email client.

        Args:
            template_renderer: Template renderer instance
            connection_string: Azure Communication Services connection string
            sender_address: Email address to send from
        """
        super().__init__(template_renderer)
        self.connection_string = connection_string
        self.sender_address = sender_address

        try:
            self.client = EmailClient.from_connection_string(self.connection_string)
        except Exception as e:
            logger.error(f"Failed to initialize Azure Email client: {str(e)}")
            self.client = None

    @classmethod
    def from_config(cls, template_renderer: TemplateRenderer, config: Dict[str, Any]) -> 'AzureEmailProvider':
        """Create an instance from configuration dictionary.

        Args:
            template_renderer: Template renderer instance
            config: Configuration dictionary

        Returns:
            Configured AzureEmailProvider instance
        """
        return cls(
            template_renderer=template_renderer,
            connection_string=config.get("AZURE_COMMUNICATION_CONNECTION_STRING", ""),
            sender_address=config.get("AZURE_SENDER_EMAIL", "")
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
        """Send an email via Azure Communication Services.

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
            logger.error("Email client is not initialized")
            raise HTTPException(status_code=500, detail="Email service is not available")

        try:
            message = {
                "content": {
                    "subject": subject,
                    "html": html_content
                },
                "recipients": {
                    "to": [{"address": email} for email in to_emails]
                },
                "senderAddress": self.sender_address
            }

            if cc_emails:
                message["recipients"]["cc"] = [{"address": email} for email in cc_emails]

            if bcc_emails:
                message["recipients"]["bcc"] = [{"address": email} for email in bcc_emails]

            if attachments:
                message["attachments"] = attachments

            poller = self.client.begin_send(message)
            result = poller.result()

            logger.info(f"Email sent to {', '.join(to_emails)}, Message ID: {result.message_id}")
            return {
                "message_id": result.message_id,
                "status": "sent"
            }

        except Exception as e:
            logger.error(f"Failed to send email via Azure: {str(e)}")
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
        """Send a templated email via Azure.

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
