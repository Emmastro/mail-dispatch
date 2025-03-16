import asyncio
import unittest
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

from pydantic import EmailStr

from src.email_providers import TemplateRenderer, create_email_service


class BaseEmailServiceTest(unittest.TestCase):
    """Base class for email service tests with common test methods."""

    # Configuration to be overridden by subclasses
    CONFIG: Dict[str, Any] = {}

    # Provider specific attributes to be set by subclasses
    PROVIDER_NAME: str = "base"
    MOCK_CLIENT_PATH: str = ""

    # Common test email addresses
    TEST_RECIPIENT: EmailStr = "test@example.com"
    TEST_SENDER: EmailStr = "sender@example.com"

    # Response setup for mocks - can be overridden by subclasses
    MOCK_RESPONSE_STATUS: int = 200
    MOCK_MESSAGE_ID_HEADER: str = "X-Message-Id"
    MOCK_MESSAGE_ID: str = "test-message-id"
    RESPONSE_STATUS_SUCCESS: str = "sent"

    # Test data
    TEMPLATE_NAME: str = "test"
    TEMPLATE_DATA: Dict[str, Any] = {
        "subject": "Test Notification",
        "message": "This is a test message",
        "action_url": "https://example.com/action",
        "action_text": "Take Action"
    }

    def setUp(self):
        """Set up test environment."""
        self.template_renderer = TemplateRenderer()
        self.email_service = create_email_service(self.CONFIG)

    def tearDown(self):
        """Clean up after tests."""
        pass

    def run_async(self, coroutine):
        """Run an async function in a unittest test."""
        return asyncio.run(coroutine)

    def setup_mock_client(self, mock_client_class):
        """Set up mock client for email provider."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = self.MOCK_RESPONSE_STATUS
        mock_response.headers = {self.MOCK_MESSAGE_ID_HEADER: self.MOCK_MESSAGE_ID}
        mock_client.send.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Set the mock client in the provider
        self.email_service.provider.client = mock_client

        return mock_client, mock_response

    def test_send_email(self):
        """Test sending a simple email."""
        if not self.MOCK_CLIENT_PATH:
            self.skipTest("No mock client path provided")

        with patch(self.MOCK_CLIENT_PATH) as mock_client_class:
            mock_client, _ = self.setup_mock_client(mock_client_class)

            result = self.run_async(
                self.email_service.send_email(
                    to_emails=[self.TEST_RECIPIENT],
                    subject="Test Subject",
                    html_content="<p>Test Content</p>"
                )
            )

            self.assertEqual(result["message_id"], self.MOCK_MESSAGE_ID)
            self.assertEqual(result["status"], self.RESPONSE_STATUS_SUCCESS)
            mock_client.send.assert_called_once()

    def test_send_template_email(self):
        """Test sending a template email."""
        if not self.MOCK_CLIENT_PATH:
            self.skipTest("No mock client path provided")

        with patch(self.MOCK_CLIENT_PATH) as mock_client_class:
            mock_client, _ = self.setup_mock_client(mock_client_class)

            result = self.run_async(
                self.email_service.send_template_email(
                    to_emails=[self.TEST_RECIPIENT],
                    template_name=self.TEMPLATE_NAME,
                    template_data=self.TEMPLATE_DATA
                )
            )

            self.assertEqual(result["message_id"], self.MOCK_MESSAGE_ID)
            self.assertEqual(result["status"], self.RESPONSE_STATUS_SUCCESS)
            mock_client.send.assert_called_once()

    def test_send_email_with_cc_bcc(self):
        """Test sending an email with CC and BCC recipients."""
        if not self.MOCK_CLIENT_PATH:
            self.skipTest("No mock client path provided")

        with patch(self.MOCK_CLIENT_PATH) as mock_client_class:
            mock_client, _ = self.setup_mock_client(mock_client_class)

            result = self.run_async(
                self.email_service.send_email(
                    to_emails=[self.TEST_RECIPIENT],
                    subject="Test Subject",
                    html_content="<p>Test Content</p>",
                    cc_emails=["cc@example.com"],
                    bcc_emails=["bcc@example.com"]
                )
            )

            self.assertEqual(result["message_id"], self.MOCK_MESSAGE_ID)
            self.assertEqual(result["status"], self.RESPONSE_STATUS_SUCCESS)
            mock_client.send.assert_called_once()

    def setup_integration_test_config(self) -> Optional[Dict[str, Any]]:
        """Prepare configuration for integration tests.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement setup_integration_test_config")