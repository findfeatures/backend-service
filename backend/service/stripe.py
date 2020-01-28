import logging
import time

import stripe
import json
from backend.dependencies.database.models import StripeSessionCompletedStatusEnum
from backend.dependencies.redis.provider import NonBlockingLock
from backend.entrypoints import stripe as nameko_stripe
from backend.exceptions.projects import CheckoutSessionAlreadyExists
from backend.exceptions.stripe import UnableToCreateCheckoutSession
from backend.service.base import ServiceMixin
from sqlalchemy.orm import exc as orm_exc
from backend.dependencies.database.collections.audit_logs import AuditLogType
from backend.utils.base import jwt_required
from werkzeug import Response
from backend.schemas import stripe as stripe_schemas
from backend.entrypoints.custom_http import http
logger = logging.getLogger(__name__)


class StripeServiceMixin(ServiceMixin):
    @nameko_stripe.consume(
        {
            "type": "checkout.session.completed",
            "created": {
                # Check for events created in the last 6 number of hours.
                "gte": int(time.time() - 6 * 60 * 60)
            },
            "limit": 100,
        },
        polling_period=10,
    )
    def stripe_process_checkout_completed(self, event):
        # this is probably really fragile and needs to be refactored better.
        event_id = event["id"]
        session_id = event["data"]["object"]["id"]
        subscription_plan_id = event["data"]["object"]["display_items"][0]["plan"]["id"]

        # time to live in milliseconds (30 seconds)
        lock = NonBlockingLock(
            self.redis,
            f"stripe-process-checkout-lock:{event_id}",
            ttl=30 * 1000,
            lock_id=event_id,
        )

        with lock:
            try:
                db_event = self.storage.stripe_sessions_completed.get_event(event_id)

                if db_event["status"] == StripeSessionCompletedStatusEnum.finished:
                    logger.info(
                        f"skipping checkout.session.completed"
                        f" with id {event_id} as already finished processing"
                    )
                    return
            except orm_exc.NoResultFound:
                logger.info(
                    f"processing checkout.session.completed"
                    f" id {event_id} for the first time"
                )

                self.storage.stripe_sessions_completed.create(
                    event_id, session_id, event
                )

                project_id = self.storage.projects.get_project_id_from_stripe_session_id(
                    session_id
                )

                subscription_started = AuditLogType.subscription_started(
                    subscription_plan_id
                )
                self.storage.audit_logs.create_log(
                    project_id,
                    subscription_started.log_type,
                    subscription_started.meta_data,
                )

            self.storage.stripe_sessions_completed.mark_as_finished(event_id)
            logger.info(f"finished processing event with id {event_id}")

    @jwt_required()
    @http(
        "POST",
        "/v1/stripe/checkout-session",
        expected_exceptions=(UnableToCreateCheckoutSession,),
    )
    def create_stripe_checkout_session(self, request):
        jwt_data = request.jwt_data

        checkout_session_details = stripe_schemas.CreateStripeCheckoutSessionRequest().load(
            json.loads(request.data)
        )

        project_name = checkout_session_details["project_data"]["name"]
        user_id = jwt_data['user_id']

        project_id = self.storage.projects.create_project(user_id, project_name)

        create_project_audit_log = AuditLogType.create_project(project_name, user_id)

        self.storage.audit_logs.create_log(
            project_id,
            create_project_audit_log.log_type,
            create_project_audit_log.meta_data,
        )

        try:
            session = self.stripe.checkout.Session.create(
                customer_email=checkout_session_details["email"],
                payment_method_types=["card"],
                subscription_data={"items": [{"plan": checkout_session_details["plan"]}]},
                success_url=checkout_session_details["success_url"]
                + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=checkout_session_details["cancel_url"],
            )

            # raises CheckoutSessionAlreadyExists if project already has session id
            self.storage.projects.set_checkout_session_id(
                project_id, session.id
            )

        except (stripe.error.StripeError, CheckoutSessionAlreadyExists) as e:
            logger.error(e)
            raise UnableToCreateCheckoutSession(
                "Failed to create a new checkout session for user"
            )

        return Response(
            stripe_schemas.CreateStripeCheckoutSessionResponse().dumps(
                {"session_id": session.id}
            ),
            mimetype="application/json",
        )
