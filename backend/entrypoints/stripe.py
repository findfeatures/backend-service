import time

import stripe
from nameko import config
from nameko.extensions import Entrypoint


class NamekoStripe(Entrypoint):
    def __init__(self, event_args, polling_period=10):
        self.event_args = event_args
        self.polling_period = polling_period

        self.stripe = None

        super(NamekoStripe, self).__init__()

    def setup(self):
        self.stripe = stripe
        self.stripe.api_key = config.get("STRIPE").get("API_KEY")

    def start(self):
        self.container.spawn_managed_thread(self.run, identifier="NamekoStripe.run")

    def run(self):
        while True:
            self.stripe.events = self.stripe.Event.list(**self.event_args)

            for event in self.stripe.events.auto_paging_iter():
                self.handle_message(event)

            time.sleep(self.polling_period)

    def handle_message(self, event):
        args = (event,)
        kwargs = {}
        self.container.spawn_worker(self, args, kwargs)


consume = NamekoStripe.decorator
