# Mail Dispatch

A modular email provider system that allows seamless switching between multiple email service providers.

## Features

- Multiple provider support: SendGrid, AWS SES, Azure Communication Services, and Google Cloud Pub/Sub
- Template-based emails using Jinja2
- Easy provider switching through configuration
- Async API for modern Python applications
- Comprehensive testing utilities

## Installation

### Using pip

```bash
pip install mail-dispatch
```

### Using Poetry

```bash
poetry add mail-dispatch
```

## Requirements

- Python 3.13+
- Dependencies will be automatically installed

## Quick Start

### 1. Configure Environment Variables

Copy the `.env.example` file to `.env` and update with your provider credentials:

```bash
cp .env.example .env
```

### 2. Create Email Templates

Create your email templates using Jinja2 syntax. Store them in a directory of your choice (default is `./templates/emails`).

Example template (`welcome.html`):

```html
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {{ company_name }}</title>
</head>
<body>
    <h1>Welcome to {{ company_name }}!</h1>
    <p>Hello {{ user_name }},</p>
    <p>Thank you for joining us. We're excited to have you on board!</p>
</body>
</html>
```

### 3. Initialize the Email Service

```python
import os
from dotenv import load_dotenv
from email_providers import create_email_service

# Load environment variables
load_dotenv()

# Configure the email service with sendgrid 
config = {
    "EMAIL_PROVIDER": os.getenv("EMAIL_PROVIDER"),
    "EMAIL_TEMPLATE_DIR": os.getenv("EMAIL_TEMPLATE_DIR"),
    # Provider-specific config will be loaded based on EMAIL_PROVIDER
    "EMAIL_SENDGRID_API_KEY": os.getenv("EMAIL_SENDGRID_API_KEY"),
    "EMAIL_DEFAULT_FROM_EMAIL": os.getenv("EMAIL_DEFAULT_FROM_EMAIL"),
}

# Create the email service
email_service = create_email_service(config)
```

### 4. Send Emails

#### Send a Simple Email

```python
import asyncio
from pydantic import EmailStr

async def send_simple_email():
    result = await email_service.send_email(
        to_emails=["recipient@example.com"],
        subject="Hello from Mail Dispatch",
        html_content="<p>This is a test email sent with Mail Dispatch.</p>",
        cc_emails=["cc@example.com"],
        bcc_emails=["bcc@example.com"]
    )
    print(f"Email sent with ID: {result['message_id']}")

asyncio.run(send_simple_email())
```

#### Send a Template Email

```python
import asyncio
from pydantic import EmailStr

async def send_template_email():
    result = await email_service.send_template_email(
        to_emails=["recipient@example.com"],
        template_name="welcome",
        template_data={
            "company_name": "Acme Corporation",
            "user_name": "John Doe"
        },
        subject="Welcome to Acme Corporation"
    )
    print(f"Template email sent with ID: {result['message_id']}")

asyncio.run(send_template_email())
```

## Email Provider Configuration

### SendGrid

```python
config = {
    "EMAIL_PROVIDER": "sendgrid",
    "EMAIL_SENDGRID_API_KEY": "your_sendgrid_api_key",
    "EMAIL_DEFAULT_FROM_EMAIL": "sender@example.com"
}
```

### AWS SES

```python
config = {
    "EMAIL_PROVIDER": "aws",
    "AWS_REGION": "us-east-1",
    "AWS_ACCESS_KEY_ID": "your_access_key_id",
    "AWS_SECRET_ACCESS_KEY": "your_secret_access_key",
    "AWS_SENDER_EMAIL": "sender@example.com"
}
```

### Azure Communication Services

```python
config = {
    "EMAIL_PROVIDER": "azure",
    "AZURE_COMMUNICATION_CONNECTION_STRING": "your_connection_string",
    "AZURE_SENDER_EMAIL": "sender@example.com"
}
```

### Google Cloud Pub/Sub

```python
config = {
    "EMAIL_PROVIDER": "gcp",
    "GCP_PROJECT_ID": "your_project_id",
    "GCP_PUBSUB_EMAIL_TOPIC": "email-notifications",
    "GCP_SENDER_EMAIL": "sender@example.com",
    "GCP_SERVICE_ACCOUNT_JSON": "path/to/service-account-key.json"
}
```

## Custom Email Templates

By default, templates are loaded from `./templates/emails`. You can specify a custom location:

```python
config = {
    "EMAIL_PROVIDER": "sendgrid",
    "EMAIL_SENDGRID_API_KEY": "your_api_key",
    "EMAIL_DEFAULT_FROM_EMAIL": "sender@example.com",
    "EMAIL_TEMPLATE_DIR": "/path/to/your/templates"
}
```

## Running Tests

```bash
# Run unit tests
pytest

# Run integration tests (requires provider credentials)
RUN_INTEGRATION_TESTS=true pytest
```

## Adding a Custom Provider

You can extend the system with custom providers:

```python
from email_providers import BaseEmailProvider, TemplateRenderer, EmailService

class CustomEmailProvider(BaseEmailProvider):
    # Implement your custom provider
    
    @classmethod
    def from_config(cls, template_renderer, config):
        return cls(
            template_renderer=template_renderer,
            # Your custom configuration
        )
    
    async def send_email(self, to_emails, subject, html_content, **kwargs):
        # Implement send_email method
        
    async def send_template_email(self, to_emails, template_name, template_data, **kwargs):
        # Implement send_template_email method

# Register your custom provider
EmailService.register_provider("custom", CustomEmailProvider)

# Use your custom provider
config = {
    "EMAIL_PROVIDER": "custom",
    # Custom provider config
}
email_service = create_email_service(config)
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.