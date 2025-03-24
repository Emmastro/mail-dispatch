import os
import unittest
from unittest.mock import patch, MagicMock

from tests.base import BaseEmailServiceTest


class SendGridEmailServiceTest(BaseEmailServiceTest):
    """Test SendGrid email provider."""

    PROVIDER_NAME = "sendgrid"
    MOCK_CLIENT_PATH = 'sendgrid.SendGridAPIClient'
    MOCK_RESPONSE_STATUS = 202  # SendGrid uses 202 for success
    MOCK_MESSAGE_ID_HEADER = 'X-Message-Id'

    CONFIG = {
        "EMAIL_PROVIDER": "sendgrid",
        "EMAIL_SENDGRID_API_KEY": "test_api_key",
        "EMAIL_DEFAULT_FROM_EMAIL": "test@example.com"
    }

    # def setup_integration_test_config(self):
    #     """Prepare configuration for SendGrid integration tests."""
    #     from unittest import mock
    #     settings = mock.Mock()
    #
    #     if not hasattr(settings, 'EMAIL_SENDGRID_API_KEY') or not settings.EMAIL_SENDGRID_API_KEY:
    #         return None
    #
    #     return {
    #         "EMAIL_PROVIDER": "sendgrid",
    #         "EMAIL_SENDGRID_API_KEY": settings.EMAIL_SENDGRID_API_KEY,
    #         "EMAIL_DEFAULT_FROM_EMAIL": settings.EMAIL_DEFAULT_FROM_EMAIL
    #     }

    def setup_integration_test_config(self):
        """Prepare configuration for SendGrid integration tests using real environment variables."""
        api_key = os.environ.get("EMAIL_SENDGRID_API_KEY")
        from_email = os.environ.get("EMAIL_DEFAULT_FROM_EMAIL")

        if not api_key:
            return None

        return {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_SENDGRID_API_KEY": api_key,
            "EMAIL_DEFAULT_FROM_EMAIL": from_email or "test@example.com"
        }

    @unittest.skipIf(not hasattr(unittest.mock.Mock(), 'RUN_INTEGRATION_TESTS') or
                     not unittest.mock.Mock().RUN_INTEGRATION_TESTS,
                     "Integration tests are disabled")
    def test_integration_send_email(self):
        """Integration test for sending an email with SendGrid."""
        integration_config = self.setup_integration_test_config()
        print(integration_config)
        if not integration_config:
            self.skipTest("SendGrid API key is not set")

        from email_providers import create_email_service
        email_service = create_email_service(integration_config)

        result = self.run_async(
            email_service.send_email(
                to_emails= [integration_config['EMAIL_DEFAULT_TEST_RECIPIENT']],
                subject="Integration Test Email",
                html_content="<p>This is a test email from the integration test.</p>"
            )
        )

        self.assertIn("message_id", result)
        self.assertEqual(result["status"], "sent")


class AWSEmailServiceTest(BaseEmailServiceTest):
    """Test AWS SES email provider."""

    PROVIDER_NAME = "aws"
    MOCK_CLIENT_PATH = 'boto3.client'

    # AWS SES specific mock setup
    def setup_mock_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_response = {'MessageId': self.MOCK_MESSAGE_ID}
        mock_client.send_email.return_value = mock_response
        mock_client_class.return_value = mock_client

        self.email_service.provider.client = mock_client
        return mock_client, mock_response

    CONFIG = {
        "EMAIL_PROVIDER": "aws",
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "test_access_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret_key",
        "AWS_SENDER_EMAIL": "test@example.com"
    }

    def setup_integration_test_config(self):
        """Prepare configuration for AWS SES integration tests."""
        from unittest import mock
        settings = mock.Mock()

        if not hasattr(settings, 'AWS_ACCESS_KEY_ID') or not settings.AWS_ACCESS_KEY_ID:
            return None

        return {
            "EMAIL_PROVIDER": "aws",
            "AWS_REGION": settings.AWS_REGION,
            "AWS_ACCESS_KEY_ID": settings.AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": settings.AWS_SECRET_ACCESS_KEY,
            "AWS_SENDER_EMAIL": settings.AWS_SENDER_EMAIL
        }


class AzureEmailServiceTest(BaseEmailServiceTest):
    """Test Azure Communication Services email provider."""

    PROVIDER_NAME = "azure"
    MOCK_CLIENT_PATH = 'azure.communication.email.EmailClient.from_connection_string'

    # Azure specific mock setup
    def setup_mock_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_poller = MagicMock()
        mock_result = MagicMock()
        mock_result.message_id = self.MOCK_MESSAGE_ID
        mock_poller.result.return_value = mock_result
        mock_client.begin_send.return_value = mock_poller
        mock_client_class.return_value = mock_client

        self.email_service.provider.client = mock_client
        return mock_client, mock_result

    CONFIG = {
        "EMAIL_PROVIDER": "azure",
        "AZURE_COMMUNICATION_CONNECTION_STRING": "test_connection_string",
        "AZURE_SENDER_EMAIL": "test@example.com"
    }

    def setup_integration_test_config(self):
        """Prepare configuration for Azure integration tests."""
        from unittest import mock
        settings = mock.Mock()

        if not hasattr(settings, 'AZURE_COMMUNICATION_CONNECTION_STRING') or \
                not settings.AZURE_COMMUNICATION_CONNECTION_STRING:
            return None

        return {
            "EMAIL_PROVIDER": "azure",
            "AZURE_COMMUNICATION_CONNECTION_STRING": settings.AZURE_COMMUNICATION_CONNECTION_STRING,
            "AZURE_SENDER_EMAIL": settings.AZURE_SENDER_EMAIL
        }


class GCPEmailServiceTest(BaseEmailServiceTest):
    """Test Google Cloud Platform email provider using Pub/Sub."""

    PROVIDER_NAME = "gcp"
    MOCK_CLIENT_PATH = 'google.cloud.pubsub_v1.PublisherClient'

    # GCP specific mock setup
    def setup_mock_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_future = MagicMock()
        mock_future.result.return_value = self.MOCK_MESSAGE_ID
        mock_client.publish.return_value = mock_future
        mock_client_class.return_value = mock_client

        self.email_service.provider.publisher = mock_client
        return mock_client, mock_future

    # Override for GCP's slightly different response format
    def test_send_email(self):
        """Test sending a simple email with GCP Pub/Sub."""
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
            self.assertEqual(result["status"], "published")  # GCP uses "published" instead of "sent"
            mock_client.publish.assert_called_once()

    CONFIG = {
        "EMAIL_PROVIDER": "gcp",
        "GCP_PROJECT_ID": "test-project",
        "GCP_PUBSUB_EMAIL_TOPIC": "test-topic",
        "GCP_SENDER_EMAIL": "test@example.com"
    }

    def setup_integration_test_config(self):
        """Prepare configuration for GCP integration tests."""
        from unittest import mock
        settings = mock.Mock()

        if not hasattr(settings, 'GCP_PROJECT_ID') or not settings.GCP_PROJECT_ID:
            return None

        return {
            "EMAIL_PROVIDER": "gcp",
            "GCP_PROJECT_ID": settings.GCP_PROJECT_ID,
            "GCP_PUBSUB_EMAIL_TOPIC": settings.GCP_PUBSUB_EMAIL_TOPIC,
            "GCP_SENDER_EMAIL": settings.GCP_SENDER_EMAIL,
            "GCP_SERVICE_ACCOUNT_JSON": settings.GCP_SERVICE_ACCOUNT_JSON
        }