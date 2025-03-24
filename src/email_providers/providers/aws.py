from typing import Optional, Dict, Any, List
import logging
from fastapi import HTTPException
from pydantic import EmailStr

import boto3
from botocore.exceptions import ClientError

from email_providers.base import BaseEmailProvider, TemplateRenderer

from email_providers.models import BaseEmailConfig
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class AWSConfig(BaseEmailConfig):
    """Configuration for AWS SES email provider."""
    EMAIL_PROVIDER: str = "aws"
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SENDER_EMAIL: EmailStr


class AWSEmailProvider(BaseEmailProvider):
    """Email service using AWS SES."""

    def __init__(
            self,
            template_renderer: TemplateRenderer,
            aws_region: str,
            aws_access_key_id: Optional[str] = None,
            aws_secret_access_key: Optional[str] = None,
            sender_email: str = None
    ) -> None:
        """Initialize the AWS SES email client.

        Args:
            template_renderer: Template renderer instance
            aws_region: AWS region name
            aws_access_key_id: AWS access key ID (optional for IAM roles)
            aws_secret_access_key: AWS secret access key (optional for IAM roles)
            sender_email: Email address to send from
        """
        super().__init__(template_renderer)
        self.sender_email = sender_email

        try:
            # Create SES client with credentials if provided, otherwise use IAM role
            if aws_access_key_id and aws_secret_access_key:
                self.client = boto3.client(
                    'ses',
                    region_name=aws_region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                self.client = boto3.client('ses', region_name=aws_region)
        except Exception as e:
            logger.error(f"Failed to initialize AWS SES client: {str(e)}")
            self.client = None

    @classmethod
    def from_config(cls, template_renderer: TemplateRenderer, config: AWSConfig) -> 'AWSEmailProvider':
        """Create an instance from configuration dictionary.

        Args:
            template_renderer: Template renderer instance
            config: Configuration dictionary

        Returns:
            Configured AWSEmailProvider instance
        """
        return cls(
            template_renderer=template_renderer,
            aws_region=config.get("AWS_REGION", "us-east-1"),
            aws_access_key_id=config.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=config.get("AWS_SECRET_ACCESS_KEY"),
            sender_email=config.get("AWS_SENDER_EMAIL", "")
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
        """Send an email via AWS SES.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML content of the email
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            attachments: List of attachments (not supported by basic SES)

        Returns:
            Dictionary with message_id and status

        Raises:
            HTTPException: If email fails to send
        """
        if not self.client:
            logger.error("AWS SES client is not initialized")
            raise HTTPException(status_code=500, detail="Email service is not available")

        try:
            message = {
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_content,
                        'Charset': 'UTF-8'
                    }
                }
            }

            email_params = {
                'Source': self.sender_email,
                'Destination': {
                    'ToAddresses': to_emails
                },
                'Message': message
            }

            if cc_emails:
                email_params['Destination']['CcAddresses'] = cc_emails

            if bcc_emails:
                email_params['Destination']['BccAddresses'] = bcc_emails

            # Note: SES basic API doesn't support attachments directly
            # For attachments, you would need to use the MIME API or SMTP interface
            if attachments:
                logger.warning("Attachments not supported with basic SES API - ignoring attachments")

            response = self.client.send_email(**email_params)

            logger.info(f"Email sent to {', '.join(to_emails)}, Message ID: {response['MessageId']}")
            return {
                "message_id": response['MessageId'],
                "status": "sent"
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS SES error: {error_code} - {error_message}")
            raise HTTPException(status_code=500, detail=f"Failed to send email: {error_message}")
        except Exception as e:
            logger.error(f"Failed to send email via AWS SES: {str(e)}")
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
        """Send a templated email via AWS SES.

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
