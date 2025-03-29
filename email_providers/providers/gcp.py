import base64
import json
import logging
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from pydantic import EmailStr

from google.cloud import pubsub_v1

from email_providers.base import BaseEmailProvider, TemplateRenderer
from email_providers.models import BaseEmailConfig

logger = logging.getLogger(__name__)

class GCPConfig(BaseEmailConfig):
    """Configuration for Google Cloud Pub/Sub email provider."""
    EMAIL_PROVIDER: str = "gcp"
    GCP_PROJECT_ID: str
    GCP_PUBSUB_EMAIL_TOPIC: str = "email-notifications"
    GCP_SERVICE_ACCOUNT_JSON: Optional[str] = None


class GCPEmailProvider(BaseEmailProvider):
    """Email service using Google Cloud Pub/Sub for email delivery."""

    def __init__(
            self,
            template_renderer: TemplateRenderer,
            project_id: str,
            topic_name: str,
            sender_email: str,
            service_account_json: Optional[str] = None
    ) -> None:
        """Initialize the GCP Pub/Sub client for email delivery.

        Args:
            template_renderer: Template renderer instance
            project_id: GCP project ID
            topic_name: Pub/Sub topic name for email delivery
            sender_email: Email address to send from
            service_account_json: Path to service account JSON file (optional)
        """
        super().__init__(template_renderer)
        self.project_id = project_id
        self.topic_name = topic_name
        self.sender_email = sender_email
        self.topic_path = f"projects/{project_id}/topics/{topic_name}"

        try:
            if service_account_json:
                self.publisher = pubsub_v1.PublisherClient.from_service_account_json(service_account_json)
            else:
                self.publisher = pubsub_v1.PublisherClient()
        except Exception as e:
            logger.error(f"Failed to initialize GCP Pub/Sub client: {str(e)}")
            self.publisher = None

    @classmethod
    def from_config(cls, template_renderer: TemplateRenderer, config: GCPConfig) -> 'GCPEmailProvider':
        """Create an instance from configuration dictionary.

        Args:
            template_renderer: Template renderer instance
            config: Configuration dictionary

        Returns:
            Configured GCPEmailProvider instance
        """
        return cls(
            template_renderer=template_renderer,
            project_id=config.get("GCP_PROJECT_ID", ""),
            topic_name=config.get("GCP_PUBSUB_EMAIL_TOPIC", ""),
            sender_email=config.get("EMAIL_DEFAULT_FROM_EMAIL", ""),
            service_account_json=config.get("GCP_SERVICE_ACCOUNT_JSON")
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
        """Send an email via GCP Pub/Sub.

        Note: This assumes a Pub/Sub subscriber that processes email messages.

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
        if not self.publisher:
            logger.error("GCP Pub/Sub client is not initialized")
            raise HTTPException(status_code=500, detail="Email service is not available")

        try:
            # Construct email message
            email_message = {
                "from": self.sender_email,
                "to": to_emails,
                "subject": subject,
                "html_content": html_content
            }

            if cc_emails:
                email_message["cc"] = cc_emails

            if bcc_emails:
                email_message["bcc"] = bcc_emails

            if attachments:
                # Convert binary content to base64 for JSON serialization
                serializable_attachments = []
                for attachment in attachments:
                    content = attachment.get("content", b"")
                    if isinstance(content, bytes):
                        content = base64.b64encode(content).decode('utf-8')

                    serializable_attachments.append({
                        "filename": attachment.get("filename", "attachment.txt"),
                        "content": content,
                        "content_type": attachment.get("content_type", "text/plain"),
                        "is_base64": True
                    })
                email_message["attachments"] = serializable_attachments

            # Convert message to JSON and encode as bytes
            message_data = json.dumps(email_message).encode("utf-8")

            # Publish message to Pub/Sub
            future = self.publisher.publish(self.topic_path, data=message_data)
            message_id = future.result()  # Wait for message to be published

            logger.info(f"Email message published to {self.topic_path}, Message ID: {message_id}")
            return {
                "message_id": message_id,
                "status": "published"
            }

        except Exception as e:
            logger.error(f"Failed to publish email message via GCP Pub/Sub: {str(e)}")
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
        """Send a templated email via GCP Pub/Sub.

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
