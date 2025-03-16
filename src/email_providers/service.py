from typing import List, Optional, Any, Dict, Protocol, Type
import logging
from pydantic import EmailStr

from .providers import providers as email_providers
from .base import TemplateRenderer

logger = logging.getLogger(__name__)


class EmailProvider(Protocol):
    """Protocol defining the interface for email providers."""

    async def send_email(
            self,
            to_emails: List[EmailStr],
            subject: str,
            html_content: str,
            cc_emails: Optional[List[EmailStr]] = None,
            bcc_emails: Optional[List[EmailStr]] = None,
            attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send an email via the provider."""
        ...

    async def send_template_email(
            self,
            to_emails: List[EmailStr],
            template_name: str,
            template_data: Dict[str, Any],
            subject: Optional[str] = None,
            cc_emails: Optional[List[EmailStr]] = None,
            bcc_emails: Optional[List[EmailStr]] = None
    ) -> Dict[str, Any]:
        """Send a templated email via the provider."""
        ...


class EmailService:
    """
    Factory for creating and using email providers.

    This service determines which email provider to use based on configuration
    and provides a unified interface for sending emails.
    """

    PROVIDERS = email_providers

    def __init__(self, config: Dict[str, Any]):
        """Initialize the email service with the appropriate provider.

        Args:
            config: Dictionary containing configuration for email providers
        """
        self.template_renderer = TemplateRenderer.from_config(config)

        provider_name = config.get("EMAIL_PROVIDER").lower()

        if provider_name not in self.PROVIDERS:
            raise ValueError(f"Invalid email provider {provider_name}")

        provider_class = self.PROVIDERS[provider_name]

        self.provider = provider_class.from_config(
            template_renderer=self.template_renderer,
            config=config
        )

        logger.info(f"Email service initialized with {provider_name} provider")

    async def send_email(self, *args, **kwargs):
        """Send an email using the configured provider."""
        return await self.provider.send_email(*args, **kwargs)

    async def send_template_email(self, *args, **kwargs):
        """Send a templated email using the configured provider."""
        return await self.provider.send_template_email(*args, **kwargs)

    @classmethod
    def register_provider(cls, name: str, provider_class: Type):
        """Register a new email provider class.

        Args:
            name: Name of the provider
            provider_class: Provider class that implements EmailProvider protocol

        Returns:
            None
        """
        cls.PROVIDERS[name.lower()] = provider_class

    def get_provider(self):
        """Get the current email provider instance.

        Returns:
            Current email provider instance
        """
        return self.provider


def create_email_service(config) -> EmailService:
    """Create an email service from a configuration dictionary
    """

    return EmailService(config)
