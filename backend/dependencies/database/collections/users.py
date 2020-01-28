import datetime

from backend.dependencies.database.collections import Collection
from backend.dependencies.database.models import User
from backend.utils.base import sa_to_dict
from sqlalchemy.orm import exc as orm_exc


class Users(Collection):
    name = "users"
    model = User

    @sa_to_dict(sensitive_fields=["password"])
    def get(self, user_id):

        user = self.db.session.query(User).get(user_id)

        if not user:
            raise orm_exc.NoResultFound(f"No user with id {user_id} found")

        return user

    @sa_to_dict(sensitive_fields=["password"])
    def get_from_email(self, email):

        user = self.db.session.query(User).filter_by(email=email).one_or_none()

        if not user:
            raise orm_exc.NoResultFound(f"No user with email {email} found")

        return user

    def create(self, email, password, display_name):
        new_user = User(email=email, password=password, display_name=display_name)
        with self.db.get_session() as session:
            session.add(new_user)
        return new_user.id

    def delete(self, user_id):
        with self.db.get_session() as session:
            user = session.query(User).filter_by(id=user_id).one()
            user.deleted_datetime_utc = datetime.datetime.utcnow()

    def is_correct_password(self, email, password):
        user = self.db.session.query(User).filter_by(email=email).one_or_none()

        if not user or user.deleted_datetime_utc is not None:
            return False

        return user.password == password

    def update_verified(self, user_id, verified):
        with self.db.get_session() as session:
            user = session.query(User).get(user_id)

            if not user:
                raise orm_exc.NoResultFound(f"No user with id {user_id} found")

            user.verified = verified
