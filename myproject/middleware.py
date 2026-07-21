import logging
import time
import uuid


logger = logging.getLogger("myapp.requests")


class RequestLoggingMiddleware:
    """Log application requests without recording query strings or form data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = uuid.uuid4().hex[:12]
        started_at = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - started_at) * 1000
        user_id = request.user.pk if getattr(request, "user", None) and request.user.is_authenticated else "anonymous"

        logger.info(
            "request_completed request_id=%s method=%s path=%s status=%s duration_ms=%.1f client_ip=%s user_id=%s cf_ray=%s",
            request.request_id,
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            self._client_ip(request),
            user_id,
            request.META.get("HTTP_CF_RAY", "-"),
        )
        response["X-Request-ID"] = request.request_id
        return response

    def process_exception(self, request, exception):
        logger.exception(
            "request_failed request_id=%s method=%s path=%s client_ip=%s exception=%s",
            getattr(request, "request_id", "unknown"),
            request.method,
            request.path,
            self._client_ip(request),
            exception.__class__.__name__,
        )

    @staticmethod
    def _client_ip(request):
        # Nginx overwrites X-Real-IP before proxying, so an external client
        # cannot control this value when requests arrive through Nginx.
        return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR", "unknown")
