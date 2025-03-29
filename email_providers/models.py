from pathlib import Path
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

class BaseEmailConfig(BaseModel):
    """Base configuration for all email providers."""
    EMAIL_TEMPLATE_DIR: Optional[str] = None # TODO: validate that this directory exists
    EMAIL_DEFAULT_FROM_EMAIL: EmailStr

    @field_validator('EMAIL_TEMPLATE_DIR')
    def validate_template_dir(cls, v):
        """Validate that the template directory exists or can be created."""
        if v is None:
            return v

        # Handle relative paths - we don't convert here as we'll do that in TemplateRenderer
        path = Path(v)
        if path.exists() and not path.is_dir():
            raise ValueError(f"Template path exists but is not a directory: {path}")
        return v

    class Config:
        extra = "allow"  # Allow extra fields not defined in the model
