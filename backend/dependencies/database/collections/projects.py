from backend.dependencies.database.collections import Collection
from backend.dependencies.database.models import (
    Project,
    StripeSessionCompleted,
    StripeSessionCompletedStatusEnum,
    UserProject,
)
from backend.exceptions.projects import CheckoutSessionAlreadyExists
from backend.utils.base import _sa_to_dict


class Projects(Collection):
    name = "projects"
    model = Project

    def get_total_projects(self, user_id):
        return len(self.get_all_verified(user_id))

    def get_all_verified(self, user_id):
        # filters out projects which user isn't verified for and
        # where not paid yet.
        projects_data = (
            self.db.session.query(Project)
            .join(UserProject)
            .join(
                StripeSessionCompleted,
                StripeSessionCompleted.session_id == Project.checkout_session_id,
                isouter=True,
            )
            .filter(
                UserProject.user_id == user_id,
                UserProject.verified.is_(True),
                StripeSessionCompleted.id.isnot(None),
                StripeSessionCompleted.status
                == StripeSessionCompletedStatusEnum.finished,
            )
            .order_by(UserProject.created_datetime_utc)
            .all()
        )
        result = []

        for project in projects_data:
            result.append(_sa_to_dict(project))

        return result

    def set_checkout_session_id(self, project_id, checkout_session_id):

        with self.db.get_session() as session:
            project = session.query(Project).get(project_id)

            if project.checkout_session_id:
                raise CheckoutSessionAlreadyExists(
                    f"checkout_session_id is already defined for {project_id}"
                )

            project.checkout_session_id = checkout_session_id

    def create_project(self, user_id, name):

        with self.db.get_session() as session:
            project = Project(name=name)
            session.add(project)
            session.add(UserProject(user_id=user_id, project=project, verified=True))
        return project.id

    def get_project_id_from_stripe_session_id(self, session_id):
        project = (
            self.db.session.query(Project)
            .filter_by(checkout_session_id=session_id)
            .one()
        )
        return project.id
