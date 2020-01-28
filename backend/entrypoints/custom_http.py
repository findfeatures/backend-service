import json
from functools import partial
from types import FunctionType

from backend.exceptions import (
    AuthorizationHeaderMissing,
    UnauthorizedRequest,
)
from backend.exceptions.stripe import UnableToCreateCheckoutSession
from backend.exceptions.users import (
    UserAlreadyExists,
    UserNotAuthorised,
    UserNotVerified,
)

from marshmallow import ValidationError
from nameko import config
from nameko.exceptions import BadRequest, safe_for_serialization
from nameko.extensions import register_entrypoint
from nameko.web.handlers import HttpRequestHandler
from werkzeug import Response


class CustomHttpEntrypoint(HttpRequestHandler):

    # standard mapped errors which are always caught
    standard_mapped_errors = {
        ValidationError: (400, "VALIDATION_ERROR"),
        UserNotAuthorised: (401, "USER_NOT_AUTHORISED"),
        BadRequest: (400, "BAD_REQUEST"),
        AuthorizationHeaderMissing: (400, "AUTHORIZATION_HEADER_MISSING"),
        UnauthorizedRequest: (401, "UNAUTHORISED_REQUEST"),
    }

    mapped_errors = {
        UserAlreadyExists: (409, "USER_ALREADY_EXISTS"),
        UserNotVerified: (418, "USER_NOT_VERIFIED"),
        UnableToCreateCheckoutSession: (500, "UNABLE_TO_CREATE_CHECKOUT_SESSION"),
    }

    def __init__(self, method, url, expected_exceptions=(), **kwargs):
        super().__init__(method, url, expected_exceptions=expected_exceptions)

        cors = config.get("DEFAULT_CORS", "*").split(",")

        self.allowed_origin = kwargs.get("origin", cors)
        self.allowed_methods = kwargs.get("methods", ["*"])
        self.allow_credentials = kwargs.get("credentials", True)

        self.standard_mapped_errors_tuple = tuple(self.standard_mapped_errors.keys())

        self.auth_required = kwargs.get("auth_required", False)

    def handle_request(self, request):
        self.request = request

        if request.method == "OPTIONS":
            return self.response_from_result(result="")

        if self.auth_required:
            try:
                auth_token = self._get_auth_token_from_header(request)
                request.auth_token = auth_token
            except (
                UnauthorizedRequest,
                AuthorizationHeaderMissing,
            ) as exc:
                return self.response_from_exception(exc)

        return super().handle_request(request)

    def response_from_result(self, *args, **kwargs):
        response = super(CustomHttpEntrypoint, self).response_from_result(*args, **kwargs)
        response = self._add_cors(response)
        return response

    def response_from_exception(self, exc):
        status_code, error_code = 500, "UNEXPECTED_ERROR"

        if isinstance(exc, self.expected_exceptions) or isinstance(
            exc, self.standard_mapped_errors_tuple
        ):
            if type(exc) in self.standard_mapped_errors:
                status_code, error_code = self.standard_mapped_errors[type(exc)]
            elif type(exc) in self.mapped_errors:
                status_code, error_code = self.mapped_errors[type(exc)]
            else:
                status_code = 400
                error_code = "BAD_REQUEST"

        response = Response(
            json.dumps({"error": error_code, "message": safe_for_serialization(exc)}),
            status=status_code,
            mimetype="application/json",
        )
        response = self._add_cors(response)

        return response

    def _add_cors(self, response):
        response.headers.add(
            "Access-Control-Allow-Headers",
            self.request.headers.get("Access-Control-Request-Headers"),
        )
        response.headers.add(
            "Access-Control-Allow-Credentials", str(self.allow_credentials).lower()
        )
        response.headers.add(
            "Access-Control-Allow-Methods", ",".join(self.allowed_methods)
        )
        response.headers.add(
            "Access-Control-Allow-Origin", ",".join(self.allowed_origin)
        )
        return response

    @staticmethod
    def _get_auth_token_from_header(request):
        token = request.headers.get("Authorization")

        if not token:
            raise AuthorizationHeaderMissing("Authorization header is required.")

        # if token == "web-app" then this request is from the web-app
        # when we change and add actual tokens this would be authenticated here
        if token != "web-app":
            raise UnauthorizedRequest("Request is unauthorized.")

        return token

    @classmethod
    def decorator(cls, *args, **kwargs):
        """
        We're overriding the decorator classmethod to allow it to register an options
        route for each standard REST call. This saves us from manually defining OPTIONS
        routes for each CORs enabled endpoint
        """

        def registering_decorator(fn, args, kwargs):
            instance = cls(*args, **kwargs)
            register_entrypoint(fn, instance)
            if instance.method in ("GET", "POST", "DELETE", "PUT", "HEAD") and (
                "*" in instance.allowed_methods
                or instance.method in instance.allowed_methods
            ):
                options_args = ["OPTIONS"] + list(args[1:])
                options_instance = cls(*options_args, **kwargs)
                register_entrypoint(fn, options_instance)
            return fn

        if len(args) == 1 and isinstance(args[0], FunctionType):
            # usage without arguments to the decorator:
            # @foobar
            # def spam():
            #     pass
            return registering_decorator(args[0], args=(), kwargs={})
        else:
            # usage with arguments to the decorator:
            # @foobar('shrub', ...)
            # def spam():
            #     pass
            return partial(registering_decorator, args=args, kwargs=kwargs)


http = CustomHttpEntrypoint.decorator
