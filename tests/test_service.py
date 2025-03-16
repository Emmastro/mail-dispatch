import unittest
from unittest import mock
from unittest.mock import patch, MagicMock

from src.email_providers import create_email_service, TemplateRenderer
from tests.base import BaseEmailServiceTest

settings = mock.Mock()


class TemplateRendererTest(unittest.TestCase):
    """Test for the template renderer."""

    # TODO: the examples here should be general purpose and about test. work_order is too specific to a usecase
    def test_template_renderer(self):
        """Test template rendering."""
        renderer = TemplateRenderer()

        html = renderer.render_template('work_order_notification', {
            'work_order_id': 123,
            'status': 'In Progress',
            'description': 'Test',
            'assigned_to': 'John'
        })
        self.assertIn('Work Order #123', html)
        self.assertIn('In Progress', html)

        # Test invitation template
        html = renderer.render_template('user_invitation', {
            'invite_link': 'https://test.com',
            'company_name': 'Test Corp',
            'current_year': 2025
        })
        self.assertIn('Test Corp', html)
        self.assertIn('https://test.com', html)


# TODO: the tests here should be moved to the BaseServiceTest. This class should only provide
#  the configuration, and use the tests written in  BaseServiceTest.
class SendGridEmailServiceTest(BaseEmailServiceTest):
    """Test SendGrid email provider."""

    PROVIDER_NAME = "sendgrid"

    CONFIG = {
        "EMAIL_PROVIDER": "sendgrid",
        "EMAIL_SENDGRID_API_KEY": "test_api_key",
        "EMAIL_DEFAULT_FROM_EMAIL": "test@example.com"
    }

    @patch('sendgrid.SendGridAPIClient')
    def test_send_email(self, mock_client_class):
        """Test sending a simple email with SendGrid."""
        # Set up the mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test-message-id'}
        mock_client.send.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Set the mock client in the provider
        self.email_service.provider.client = mock_client

        # Run the async test
        result = self.run_async(
            self.email_service.send_email(
                to_emails=[settings.EMAIL_DEFAULT_TEST_RECIPIENT],
                subject="Test Subject",
                html_content="<p>Test Content</p>"
            )
        )

        # Verify the result
        self.assertEqual(result["message_id"], "test-message-id")
        self.assertEqual(result["status"], "sent")

        # Verify the mock was called
        mock_client.send.assert_called_once()

    @patch('sendgrid.SendGridAPIClient')
    def test_send_template_email(self, mock_client_class):
        """Test sending a template email with SendGrid."""
        # Set up the mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test-template-id'}
        mock_client.send.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Set the mock client in the provider
        self.email_service.provider.client = mock_client

        # Run the async test
        result = self.run_async(
            self.email_service.send_template_email(
                to_emails=[settings.EMAIL_DEFAULT_TEST_RECIPIENT],
                template_name="work_order_notification",
                template_data={
                    'work_order_id': 123,
                    'status': 'In Progress',
                    'description': 'Test',
                    'assigned_to': 'John'
                }
            )
        )

        # Verify the result
        self.assertEqual(result["message_id"], "test-template-id")
        self.assertEqual(result["status"], "sent")

        # Verify the mock was called
        mock_client.send.assert_called_once()

    @unittest.skipIf(not settings.RUN_INTEGRATION_TESTS, "Integration tests are disabled")
    def test_integration_send_email(self):
        """Integration test for sending an email with SendGrid."""
        # Skip if SendGrid API key is not set
        if not settings.EMAIL_SENDGRID_API_KEY:
            self.skipTest("SendGrid API key is not set")

        # Override CONFIG for integration tests
        integration_config = {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_SENDGRID_API_KEY": settings.EMAIL_SENDGRID_API_KEY,
            "EMAIL_DEFAULT_FROM_EMAIL": settings.EMAIL_DEFAULT_FROM_EMAIL
        }

        email_service = create_email_service(integration_config)

        # Run the test
        result = self.run_async(
            email_service.send_email(
                to_emails=[settings.EMAIL_DEFAULT_TEST_RECIPIENT],
                subject="Integration Test Email",
                html_content="<p>This is a test email from the integration test.</p>"
            )
        )

        # Verify the result
        self.assertIn("message_id", result)
        self.assertEqual(result["status"], "sent")

    @unittest.skipIf(not settings.RUN_INTEGRATION_TESTS, "Integration tests are disabled")
    def test_integration_send_template_email(self):
        """Integration test for sending a template email with SendGrid."""
        # Skip if SendGrid API key is not set
        if not settings.EMAIL_SENDGRID_API_KEY:
            self.skipTest("SendGrid API key is not set")

        # Override CONFIG for integration tests
        integration_config = {
            "EMAIL_PROVIDER": "sendgrid",
            "EMAIL_SENDGRID_API_KEY": settings.EMAIL_SENDGRID_API_KEY,
            "EMAIL_DEFAULT_FROM_EMAIL": settings.EMAIL_DEFAULT_FROM_EMAIL
        }

        # Create a new service with the real config
        email_service = create_email_service(integration_config)

        # Run the test
        result = self.run_async(
            email_service.send_template_email(
                to_emails=[settings.EMAIL_DEFAULT_TEST_RECIPIENT],
                template_name="work_order_notification",
                template_data={

                }
            )
        )

        # Verify the result
        self.assertIn("message_id", result)
        self.assertEqual(result["status"], "sent")



if __name__ == '__main__':
    unittest.main()