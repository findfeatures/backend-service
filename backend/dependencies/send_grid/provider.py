import logging
import os

from nameko import config
from nameko.extensions import DependencyProvider
from sendgrid import Mail, SendGridAPIClient


path = os.path.dirname(__file__)

"""
Currently this dependency uses HTML rather than templates but its pretty trivial
to add template support instead. (Templates are the templates defined in the send_grid
UI which can be dynamically changed)
"""

logger = logging.getLogger(__name__)


class SendGridWrapper:
    def __init__(self, key, web_app_address):
        self.client = SendGridAPIClient(key)
        self.web_app_address = web_app_address
        self.from_email = "FindFeatures@findfeatures.io"

    def _send_mail(self, to_mail, subject, html_content):

        message = Mail(
            from_email=self.from_email,
            to_emails=to_mail,
            subject=subject,
            html_content=html_content,
        )

        try:
            self.client.send(message)
        except Exception as e:
            logger.exception(e)

    def send_signup_verification(self, to_email, token):

        url = (
            f"{self.web_app_address}/email-verification?token={token}&email={to_email}"
        )

        html = f'FindFeatures: Click here to activate your account <br><a href="{url}">{url}</a>'
        self._send_mail(to_email, "FindFeatures: Verify your email!", html)


class SendGrid(DependencyProvider):
    def __init__(self, **options):
        self.options = options
        self.key = None
        self.web_app_address = None

    def setup(self):
        self.key = config.get("SENDGRID_KEY")
        self.web_app_address = config.get("WEB_APP_ADDRESS")

    def get_dependency(self, worker_ctx):
        return SendGridWrapper(self.key, self.web_app_address)
