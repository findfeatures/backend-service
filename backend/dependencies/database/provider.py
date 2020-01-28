from backend.dependencies.database.collections.audit_logs import AuditLogs
from backend.dependencies.database.collections.projects import Projects
from backend.dependencies.database.collections.stripe_sessions_completed import (
    StripeSessionsCompleted,
)
from backend.dependencies.database.collections.user_notifications import (
    UserNotifications,
)
from backend.dependencies.database.collections.user_tokens import UserTokens
from backend.dependencies.database.collections.users import Users
from backend.dependencies.database.models import Base
from ddtrace import Pin
from nameko import config
from nameko_sqlalchemy import Database


class StorageWrapper:
    def __init__(self, db, collections):
        self.db = db
        self.collections = collections
        self.register_collections()

    def register_collections(self):
        for collection in self.collections:
            setattr(self, collection.name, collection(self.db))

    def health_check(self):
        self.db.session.execute("SELECT 1 FROM users LIMIT 1")


class Storage(Database):
    collections = [
        Users,
        UserTokens,
        Projects,
        StripeSessionsCompleted,
        UserNotifications,
        AuditLogs,
    ]

    def __init__(self):
        engine_options = {
            "pool_timeout": config.get("DB_POOL_TIMEOUT", 30),
            "pool_recycle": config.get("DB_POOL_RECYCLE", -1),
            "pool_size": config.get("DB_POOL_SIZE", 5),
            "max_overflow": config.get("DB_MAX_OVERFLOW", 10),
            "pool_pre_ping": config.get("DB_POOL_PRE_PING", False),
        }
        super().__init__(declarative_base=Base, engine_options=engine_options)

    def setup(self):
        super().setup()
        Pin.override(self.engine, service="backend-service")

    def get_dependency(self, worker_ctx):
        db = super().get_dependency(worker_ctx)

        return StorageWrapper(db, self.collections)
