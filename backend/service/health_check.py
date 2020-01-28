from backend.service.base import ServiceMixin
from nameko.web.handlers import http


class HealthCheckServiceMixin(ServiceMixin):
    @http("GET", "/health-check")
    def health_check(self, request):
        self.storage.health_check()
        return 200, "OK"
