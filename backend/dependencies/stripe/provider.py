import stripe
from nameko import config
from nameko.extensions import DependencyProvider


class Stripe(DependencyProvider):
    def __init__(self):
        self.client = None
        self.api_key = None

    def setup(self):
        self.api_key = config.get("STRIPE").get("API_KEY")

    def start(self):
        self.client = stripe
        self.client.api_key = self.api_key
        self.client.max_network_retries = 3

    def stop(self):
        self.client = None

    def kill(self):
        self.client = None

    def get_dependency(self, worker_ctx):
        return self.client
