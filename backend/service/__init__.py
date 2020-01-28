from backend.service.health_check import HealthCheckServiceMixin
from backend.service.projects import ProjectsServiceMixin
from backend.service.stripe import StripeServiceMixin
from backend.service.users import UsersServiceMixin


class BackendService(
    HealthCheckServiceMixin, ProjectsServiceMixin, UsersServiceMixin, StripeServiceMixin
):
    pass
