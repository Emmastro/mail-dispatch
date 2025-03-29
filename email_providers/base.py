import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import jinja2
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class TemplateRenderer:
    """Template renderer for email templates using Jinja2."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize the template renderer with Jinja2 environment.

        Args:
            template_dir: Path to template directory. If None, uses default path.
        """
        if template_dir and isinstance(template_dir, str):
            template_dir = Path(template_dir)

        if template_dir is None:
            # First try the default relative to project root (./templates/emails)
            project_root = Path.cwd()
            default_template_dir = project_root / "templates" / "emails"

            if default_template_dir.exists() and default_template_dir.is_dir():
                template_dir = default_template_dir
            else:
                # Fallback to a directory relative to the library
                template_dir = Path(__file__).parent.parent / "templates" / "emails"
                logger.warning(
                    f"No template directory provided and default directory not found at {default_template_dir}. "
                    f"Falling back to library directory: {template_dir}"
                )

        self.template_dir = template_dir
        # Create the directory if it doesn't exist
        template_dir.mkdir(parents=True, exist_ok=True)

        # Set up Jinja2 environment
        try:
            self.env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize Jinja2 environment with directory {template_dir}: {str(e)}")
            raise ValueError(f"Failed to initialize template environment: {str(e)}")

    def render_template(self, template_name: str, template_data: Dict[str, Any]) -> str:
        """Render a template with provided data.

        Args:
            template_name: Name of the template file without extension
            template_data: Dictionary of data to render the template with

        Returns:
            Rendered HTML content

        Raises:
            HTTPException: If template not found
        """
        try:
            template = self.env.get_template(f"{template_name}.html")
            return template.render(**template_data)
        except jinja2.exceptions.TemplateNotFound:
            template_path = self.template_dir / f"{template_name}.html"
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_name}' not found at {template_path}"
            )
        except Exception as e:
            logger.error(f"Error rendering template '{template_name}': {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to render template: {str(e)}")

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'TemplateRenderer':
        """Create a template renderer from configuration.

        Args:
            config: Configuration dictionary

        Returns:
            TemplateRenderer instance
        """
        template_dir = config.get("EMAIL_TEMPLATE_DIR")

        if template_dir and not os.path.isabs(template_dir):
            # Relative to project root
            project_root = Path.cwd()
            template_dir = project_root / template_dir
            logger.info(f"Converting relative template path to absolute: {template_dir}")

        return cls(template_dir=template_dir)


class BaseEmailProvider:
    """Base class for all email providers with common functionality."""

    def __init__(self, template_renderer: TemplateRenderer):
        """Initialize base email provider.

        Args:
            template_renderer: Template renderer instance
        """
        self.template_renderer = template_renderer

    def _get_default_subject(self) -> str:
        """Get default subject based on template name and data.
        """
        return "Default subject"

    @classmethod
    def from_config(cls, template_renderer: TemplateRenderer, config: Dict[str, Any]) -> 'BaseEmailProvider':
        """Create an instance from configuration dictionary.

        Args:
            template_renderer: Template renderer instance
            config: Configuration dictionary

        Returns:
            Configured provider instance

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement from_config()")
