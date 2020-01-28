import datetime
import json
import logging
from uuid import uuid4

import jwt
from backend.entrypoints.custom_http import http
from backend.exceptions.user_tokens import InvalidToken
from backend.exceptions.users import (
    UserAlreadyExists,
    UserNotAuthorised,
    UserNotVerified,
)
from backend.schemas import users as users_schemas
from backend.service.base import ServiceMixin
from backend.utils.base import generate_token, jwt_required
from nameko import config
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc
from werkzeug import Response


logger = logging.getLogger(__name__)


class UsersServiceMixin(ServiceMixin):
    @http(
        "POST",
        "/v1/user/auth",
        expected_exceptions=(UserNotVerified, UserNotAuthorised),
    )
    def auth_user(self, request):
        user_auth_details = users_schemas.AuthUserRequest().load(
            json.loads(request.data)
        )

        email = user_auth_details["email"]
        password = user_auth_details["password"]

        is_correct_password = self.storage.users.is_correct_password(email, password)

        if not is_correct_password:
            raise UserNotAuthorised("user not authorised for this request")

        # not the most ideal code but i want to keep the
        # requests here to storage quite easy to test
        # and maintain
        user_details = self.storage.users.get_from_email(email)

        if not user_details["verified"]:
            raise UserNotVerified("user is not verified")

        jwt_result = {
            "JWT": jwt.encode(
                {
                    "user_id": user_details["id"],
                    "email": user_details["email"],
                    # exp is number of seconds since epoch. 1 day expiry
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
                },
                config.get("JWT_SECRET"),
                algorithm="HS256",
            ).decode("utf-8")
        }

        return Response(
            users_schemas.UserAuthResponse().dumps(jwt_result),
            mimetype="application/json",
        )

    @http("HEAD", "/v1/user/<email>", expected_exceptions=(UserAlreadyExists,))
    def check_user_exists(self, request, email):
        try:
            self.storage.users.get_from_email(email)
            raise UserAlreadyExists()
        except orm_exc.NoResultFound:
            pass

        return Response(mimetype="application/json")

    @http("POST", "/v1/user", expected_exceptions=(UserAlreadyExists,))
    def create_user(self, request):
        create_user_details = users_schemas.CreateUserRequest().load(
            json.loads(request.data)
        )

        try:
            user_id = self.storage.users.create(
                create_user_details["email"],
                create_user_details["password"],
                create_user_details["display_name"],
            )

            token = generate_token(str(uuid4().hex))

            self.storage.user_tokens.create(user_id, token)

            self.send_grid.send_signup_verification(create_user_details["email"], token)

        except exc.IntegrityError:
            raise UserAlreadyExists(
                f'email {create_user_details["email"]} already exists'
            )

        return Response(mimetype="application/json")

    @http("POST", "/v1/user/token", expected_exceptions=(UserNotAuthorised,))
    def verify_user_token(self, request):

        user_token_details = users_schemas.VerifyUserTokenRequest().load(
            json.loads(request.data)
        )

        try:
            user = self.storage.users.get_from_email(user_token_details["email"])

            self.storage.user_tokens.verify_token(
                user["id"], user_token_details["token"]
            )

            self.storage.users.update_verified(user["id"], True)

        except (orm_exc.NoResultFound, InvalidToken):
            raise UserNotAuthorised("user not authorised for this request")

        return Response(mimetype="application/json")

    @http("POST", "/v1/user/resend-email", expected_exceptions=(UserNotAuthorised,))
    def resend_user_token_email(self, request):
        user_resend_details = users_schemas.ResendUserTokenEmailRequest().load(
            json.loads(request.data)
        )
        email = user_resend_details["email"]
        password = user_resend_details["password"]

        try:
            is_correct_password = self.storage.users.is_correct_password(
                email, password
            )

            if not is_correct_password:
                raise UserNotAuthorised("user not authorised for this request")

            # because we check password above, this will not error
            user = self.storage.users.get_from_email(email)

            # if user already verified, then raise here
            if user["verified"]:
                raise UserNotAuthorised("user not authorised for this request")

            token = generate_token(str(uuid4().hex))
            self.storage.user_tokens.create(user["id"], token)
            self.send_grid.send_signup_verification(user["email"], token)

        except UserNotAuthorised as exc:
            raise exc

        return Response(mimetype="application/json")

    @jwt_required()
    @http("GET", "/v1/user/notifications")
    def get_user_notifications(self, request):

        # todo: get user notifications!!!
        notifications = []

        return Response(
            users_schemas.GetUserNotificationsResponse().dumps(
                {"notifications": notifications}
            ),
            mimetype="application/json",
        )
