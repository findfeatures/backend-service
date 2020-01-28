from marshmallow import Schema, fields


class CreateStripeCheckoutSessionProjectDataRequest(Schema):
    name = fields.String(required=True)


class CreateStripeCheckoutSessionRequest(Schema):
    plan = fields.String(required=True)
    success_url = fields.String(required=True)
    cancel_url = fields.String(required=True)
    project_data = fields.Nested(
        CreateStripeCheckoutSessionProjectDataRequest, required=True
    )


class CreateStripeCheckoutSessionResponse(Schema):
    session_id = fields.String(required=True)
