from backend.dependencies.database.collections import Collection
from backend.dependencies.database.models import AuditLog
from munch import Munch


class AuditLogs(Collection):
    name = "audit_logs"
    model = AuditLog

    def create_log(self, project_id, log_type, meta_data):

        with self.db.get_session() as session:
            new_log = AuditLog(
                project_id=project_id, log_type=log_type, meta_data=meta_data
            )
            session.add(new_log)


class AuditLogType:
    @staticmethod
    def create_project(project_name, user_id):
        return Munch().fromDict(
            {
                "log_type": "CREATE_PROJECT",
                "meta_data": {"project_name": project_name, "user_id": user_id},
            }
        )

    @staticmethod
    def subscription_started(subscription_plan_id):
        return Munch().fromDict(
            {
                "log_type": "SUBSCRIPTION_STARTED",
                "meta_data": {"subscription_plan_id": subscription_plan_id},
            }
        )
