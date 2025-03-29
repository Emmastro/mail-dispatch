"""
Pytest configuration file.

This file contains fixtures that are available to all test modules.
"""
import os
import pytest
from pathlib import Path

from email_providers import TemplateRenderer


@pytest.fixture
def template_dir():
    """Return the path to the sample templates directory."""
    base_path = Path(__file__).parent.parent
    template_dir = base_path / "src" / "templates" / "samples"

    # Ensure the directory exists
    if not template_dir.exists():
        template_dir.mkdir(parents=True, exist_ok=True)

        # Create the static directory for CSS
        static_dir = template_dir / "static"
        static_dir.mkdir(exist_ok=True)

    return template_dir


@pytest.fixture
def template_renderer(template_dir):
    """Create a template renderer with the test template directory."""
    return TemplateRenderer(template_dir=template_dir)


@pytest.fixture
def mock_settings():
    """Provide mock settings for integration tests."""

    class Settings:
        RUN_INTEGRATION_TESTS = os.environ.get("RUN_INTEGRATION_TESTS", "false").lower() == "true"
        EMAIL_DEFAULT_TEST_RECIPIENT = os.environ.get("TEST_EMAIL_RECIPIENT", "test@example.com")

        # SendGrid settings
        EMAIL_SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
        EMAIL_DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")

        # AWS settings
        AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
        AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
        AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

        # Azure settings
        AZURE_COMMUNICATION_CONNECTION_STRING = os.environ.get("AZURE_COMMUNICATION_CONNECTION_STRING", "")

        # GCP settings
        GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
        GCP_PUBSUB_EMAIL_TOPIC = os.environ.get("GCP_PUBSUB_EMAIL_TOPIC", "email-notifications")
        GCP_SERVICE_ACCOUNT_JSON = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "")

    return Settings()


@pytest.fixture
def sample_email_templates():
    """Sample email template data for testing."""
    return {
        "test": {
            'subject': 'Test Email Subject',
            'recipient_name': 'John Doe',
            'message': 'This is a test message content for the email template.',
            'action_required': True,
            'action_url': 'https://example.com/action',
            'action_text': 'Click Here',
            'current_year': 2025
        },
        "notification": {
            'subject': 'Important Notification',
            'message': 'Your account needs attention.',
            'details': {
                'Account': 'user123',
                'Status': 'Needs verification',
                'Due Date': 'March 20, 2025'
            },
            'action_url': 'https://example.com/verify',
            'action_text': 'Verify Now',
            'current_year': 2025
        },
        "welcome": {
            'company_name': 'Acme Corporation',
            'user_name': 'Alice Smith',
            'login_url': 'https://acme.example.com/login',
            'current_year': 2025
        }
    }