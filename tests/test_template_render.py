import unittest
from pathlib import Path
import datetime

from fastapi import HTTPException

from email_providers import TemplateRenderer


class TemplateRendererTest(unittest.TestCase):
    """Tests for the template renderer using real templates."""

    def setUp(self):
        """Set up the template renderer with real template files."""
        # Set up paths to template directories
        self.base_path = Path(__file__).parent.parent
        self.template_dir = self.base_path / "src" / "templates" / "samples"
        self.renderer = TemplateRenderer(template_dir=self.template_dir)

    def test_render_test_template(self):
        """Test rendering the test.html template with real data."""
        template_data = {
            'subject': 'Test Email Subject',
            'recipient_name': 'John Doe',
            'message': 'This is a test message content for the email template.',
            'action_required': True,
            'action_url': 'https://example.com/action',
            'action_text': 'Click Here',
            'current_year': datetime.datetime.now().year
        }

        rendered_html = self.renderer.render_template('test', template_data)

        # Verify that template variables were properly replaced
        self.assertIn('<title>Test Email Subject</title>', rendered_html)
        self.assertIn('Hello John Doe', rendered_html)
        self.assertIn('This is a test message content', rendered_html)
        self.assertIn('href="https://example.com/action"', rendered_html)
        self.assertIn('>Click Here<', rendered_html)
        self.assertIn(f'&copy; {datetime.datetime.now().year} Your Company', rendered_html)

    def test_template_not_found(self):
        """Test the behavior when a template is not found."""
        with self.assertRaises(HTTPException) as context:
            self.renderer.render_template('missing_template', {})

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Template missing_template not found")

    def test_from_config_with_path(self):
        """Test creating a renderer from config with a template path."""
        test_path = self.base_path / "src" / "templates" / "samples"
        config = {
            "EMAIL_TEMPLATE_DIR": str(test_path)
        }

        renderer = TemplateRenderer.from_config(config)

        # Test that the renderer works with the configured path
        template_data = {
            'subject': 'Config Test',
            'recipient_name': 'Jane Smith',
            'message': 'Testing configuration path.',
            'current_year': 2025
        }

        rendered_html = renderer.render_template('test', template_data)
        self.assertIn('<title>Config Test</title>', rendered_html)
        self.assertIn('Hello Jane Smith', rendered_html)