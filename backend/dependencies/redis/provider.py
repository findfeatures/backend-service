import walrus
from nameko import config
from nameko.extensions import DependencyProvider


class NonBlockingLock(walrus.Lock):
    def __enter__(self):
        self.acquire(block=False)


class Redis(DependencyProvider):
    def __init__(self, **options):
        self.client = None
        self.options = {"decode_responses": True}
        self.options.update(options)

    def setup(self):
        self.redis_uri = config.get("REDIS_URL", "redis://127.0.0.1:6379/0")

    def start(self):
        self.client = walrus.Database().from_url(self.redis_uri, **self.options)

    def stop(self):
        self.client = None

    def kill(self):
        self.client = None

    def get_dependency(self, worker_ctx):
        return self.client
