import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

from email_providers import create_email_service


def load_config_from_env(env_file: Path = None) -> Dict[str, Any]:
    """Load configuration from environment variables.

    Args:
        env_file: Path to .env file

    Returns:
        Configuration dictionary
    """
    if env_file and env_file.exists():
        load_dotenv(dotenv_path=env_file)
    else:
        load_dotenv()

    import os

    # Extract all relevant environment variables
    config = {}
    for key in os.environ:
        if any(key.startswith(prefix) for prefix in [
            "EMAIL_", "AWS_", "AZURE_", "GCP_"
        ]):
            config[key] = os.environ[key]

    return config


def send_email_command(args):
    """Send a simple email command."""
    config = load_config_from_env(args.env_file)

    # Create email service
    email_service = create_email_service(config)

    # Parse recipients
    to_emails = args.to.split(',')
    cc_emails = args.cc.split(',') if args.cc else None
    bcc_emails = args.bcc.split(',') if args.bcc else None

    # Parse attachments
    attachments = []
    if args.attachment:
        for attachment_path in args.attachment:
            path = Path(attachment_path)
            if path.exists():
                with open(path, 'rb') as f:
                    content = f.read()
                attachments.append({
                    'filename': path.name,
                    'content': content,
                    'content_type': 'application/octet-stream'  # Fallback
                })
            else:
                print(f"Warning: Attachment {attachment_path} not found, skipping.")

    # Send email
    result = asyncio.run(email_service.send_email(
        to_emails=to_emails,
        subject=args.subject,
        html_content=args.content,
        cc_emails=cc_emails,
        bcc_emails=bcc_emails,
        attachments=attachments if attachments else None
    ))

    print(json.dumps(result, indent=2))


def send_template_email_command(args):
    """Send a templated email command."""
    config = load_config_from_env(args.env_file)

    # Create email service
    email_service = create_email_service(config)

    # Parse recipients
    to_emails = args.to.split(',')
    cc_emails = args.cc.split(',') if args.cc else None
    bcc_emails = args.bcc.split(',') if args.bcc else None

    # Parse template data
    template_data = {}
    if args.data:
        try:
            template_data = json.loads(args.data)
        except json.JSONDecodeError:
            print("Error: Template data must be valid JSON")
            sys.exit(1)

    # Send template email
    result = asyncio.run(email_service.send_template_email(
        to_emails=to_emails,
        template_name=args.template,
        template_data=template_data,
        subject=args.subject,
        cc_emails=cc_emails,
        bcc_emails=bcc_emails
    ))

    print(json.dumps(result, indent=2))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Mail Dispatch CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--env-file', type=Path, help="Path to .env file")

    # Send email command
    send_parser = subparsers.add_parser('send', parents=[parent_parser], help="Send a simple email")
    send_parser.add_argument('--to', required=True, help="Comma-separated list of recipients")
    send_parser.add_argument('--subject', required=True, help="Email subject")
    send_parser.add_argument('--content', required=True, help="Email HTML content")
    send_parser.add_argument('--cc', help="Comma-separated list of CC recipients")
    send_parser.add_argument('--bcc', help="Comma-separated list of BCC recipients")
    send_parser.add_argument('--attachment', action='append',
                             help="Path to attachment (can be specified multiple times)")
    send_parser.set_defaults(func=send_email_command)

    # Send template email command
    template_parser = subparsers.add_parser('template', parents=[parent_parser], help="Send a templated email")
    template_parser.add_argument('--to', required=True, help="Comma-separated list of recipients")
    template_parser.add_argument('--template', required=True, help="Template name")
    template_parser.add_argument('--data', help="JSON template data")
    template_parser.add_argument('--subject', help="Email subject (overrides template default)")
    template_parser.add_argument('--cc', help="Comma-separated list of CC recipients")
    template_parser.add_argument('--bcc', help="Comma-separated list of BCC recipients")
    template_parser.set_defaults(func=send_template_email_command)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()