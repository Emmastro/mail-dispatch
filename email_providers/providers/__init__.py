from .azure import AzureEmailProvider
from .sendgrid import SendGridEmailProvider
from .aws import AWSEmailProvider
from .gcp import GCPEmailProvider

providers = {
        "azure": AzureEmailProvider,
        "sendgrid": SendGridEmailProvider,
        "aws": AWSEmailProvider,
        "gcp": GCPEmailProvider
}

__all__ = ['SendGridEmailProvider', 'AzureEmailProvider', 'AWSEmailProvider', 'GCPEmailProvider', 'providers']