import asyncio
import unittest
from typing import Dict, Any

from src.email_providers import TemplateRenderer, create_email_service


class BaseEmailServiceTest(unittest.TestCase):
    """Base class for email service tests. Does not run any tests itself."""

    # This will be overridden by subclasses
    CONFIG: Dict[str, Any] = {}

    # Provider name to be set by subclasses
    PROVIDER_NAME = "base"


    def setUp(self):
        """Set up test environment."""
        self.template_renderer = TemplateRenderer()

        # Create the email service with the provider-specific config
        self.email_service = create_email_service(self.CONFIG)

    def tearDown(self):
        """Clean up after tests."""
        pass

    def run_async(self, coroutine):
        """Helper method to run an async function in a unittest test."""
        return asyncio.run(coroutine)
