import logging
import json
from backend.service.base import ServiceMixin
from backend.utils.base import jwt_required
from backend.entrypoints.custom_http import http
from backend.schemas import projects as projects_schemas
from werkzeug import Response

logger = logging.getLogger(__name__)


class ProjectsServiceMixin(ServiceMixin):

    @jwt_required()
    @http("GET", "/v1/projects")
    def get_projects(self, request):

        jwt_data = request.jwt_data

        # verified because the user hasn't accepted the invitation yet!
        projects = self.storage.projects.get_all_verified(jwt_data["user_id"])

        return Response(
            projects_schemas.GetProjectsResponse().dumps({"projects": [
            {
                "id": project["id"],
                "name": project["name"],
                "created_datetime_utc": project["created_datetime_utc"].isoformat(),
            } for project in projects
        ]}),
            mimetype="application/json",
        )

    @jwt_required()
    @http("POST", "/v1/projects/complete")
    def is_project_setup_completed(self, request):

        jwt_data = request.jwt_data

        request_data = projects_schemas.GetProjectSetupCompletedRequest().load(
            json.loads(request.data)
        )

        projects = self.storage.projects.get_all_verified(jwt_data['user_id'])

        is_project_created = False
        for project in projects:
            if project["checkout_session_id"] == request_data['session_id']:
                return is_project_created

        return Response(
            projects_schemas.GetProjectSetupCompletedResponse().dumps(
                {"completed": is_project_created}
            ),
            mimetype="application/json",
        )
