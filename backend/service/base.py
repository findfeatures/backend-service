from backend.dependencies.database.provider import Storage
from backend.dependencies.redis.provider import Redis
from backend.dependencies.send_grid.provider import SendGrid
from backend.dependencies.stripe.provider import Stripe


class ServiceMixin:
    name = "backend"

    storage = Storage()
    send_grid = SendGrid()
    stripe = Stripe()
    redis = Redis()
