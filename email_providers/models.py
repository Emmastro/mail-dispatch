from typing import Optional
from pydantic import BaseModel, EmailStr

class BaseEmailConfig(BaseModel):
    """Base configuration for all email providers."""
    EMAIL_TEMPLATE_DIR: Optional[str] = None # TODO: validate that this directory exists
    EMAIL_DEFAULT_FROM_EMAIL: EmailStr

    class Config:
        extra = "allow"  # Allow extra fields not defined in the model