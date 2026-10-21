import uuid

from common.request_context import request_id_var


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = (request.headers.get("X-Request-ID") or "").strip()
        request_id = incoming[:64] if incoming else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        request.request_id = request_id
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)
