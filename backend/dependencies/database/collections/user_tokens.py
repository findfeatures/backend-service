from backend.dependencies.database.collections import Collection
from backend.dependencies.database.models import UserToken
from backend.exceptions.user_tokens import InvalidToken


class UserTokens(Collection):
    name = "user_tokens"
    model = UserToken

    def create(self, user_id, token):
        new_token = UserToken(user_id=user_id, token=token)

        with self.db.get_session() as session:
            session.add(new_token)

    def verify_token(self, user_id, token):
        token_from_db = (
            self.db.session.query(UserToken)
            .filter_by(user_id=user_id)
            .order_by(UserToken.created_datetime_utc.desc())
            .first()
        )

        if not token_from_db:
            raise InvalidToken(f"No token in db for user {user_id}")

        if token != token_from_db.token:
            raise InvalidToken("token is invalid")
