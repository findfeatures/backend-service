from marshmallow import Schema, fields


class GetProjectResponse(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    created_datetime_utc = fields.String(required=True)


class GetProjectsResponse(Schema):
    projects = fields.Nested(GetProjectResponse, many=True, required=True)


class GetProjectSetupCompletedRequest(Schema):
    session_id = fields.String(required=True)


class GetProjectSetupCompletedResponse(Schema):
    completed = fields.Boolean(required=True)


class CreateProjectRequest(Schema):
    name = fields.String(required=True)