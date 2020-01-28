from backend.dependencies.database.collections import Collection
from backend.dependencies.database.models import UserNotification


class UserNotifications(Collection):
    name = "user_notifications"
    model = UserNotification

    def create_notification(self, user_id, notification_type, meta_data):

        with self.db.get_session() as session:
            new_notification = UserNotification(
                user_id=user_id,
                notification_type=notification_type,
                meta_data=meta_data,
            )
            session.add(new_notification)
