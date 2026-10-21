import logging
from typing import Any

from django.http import Http404, JsonResponse
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from common.api.responses import build_payload

logger = logging.getLogger(__name__)


class BusinessError(exceptions.APIException):
    def __init__(
        self,
        message: str,
        code: int = 40000,
        http_status: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None,
    ):
        self.detail = message
        self.biz_code = code
        self.status_code = http_status
        self.data = data
        super().__init__(message)


def flatten_error_detail(detail: Any) -> str:
    if isinstance(detail, dict):
        for key, value in detail.items():
            message = flatten_error_detail(value)
            return f"{key}: {message}" if key != "non_field_errors" else message
    if isinstance(detail, (list, tuple)) and detail:
        return flatten_error_detail(detail[0])
    return str(detail)


def api_exception_handler(exc, context):
    request = context.get("request")

    if isinstance(exc, BusinessError):
        return Response(
            build_payload(exc.data, str(exc.detail), exc.biz_code, request),
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        logger.exception(
            "Unhandled API exception: %s %s",
            request.method if request else "-",
            request.path if request else "-",
        )
        return Response(
            build_payload(None, "服务器开小差了，请稍后重试", 10000, request),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = 10000
    message = "请求失败"
    data = response.data

    if isinstance(exc, exceptions.ValidationError):
        code, message = 10001, flatten_error_detail(response.data)
    elif isinstance(exc, exceptions.NotAuthenticated):
        code, message = 20001, "请先登录"
    elif isinstance(exc, exceptions.AuthenticationFailed):
        code, message = 20001, "登录状态无效或已过期"
    elif isinstance(exc, exceptions.PermissionDenied):
        code, message = 20003, "没有权限执行此操作"
    elif isinstance(exc, Http404) or isinstance(exc, exceptions.NotFound):
        code, message = 10002, "请求的资源不存在"
    elif isinstance(exc, exceptions.MethodNotAllowed):
        code, message = 10003, "请求方法不支持"
    elif isinstance(exc, exceptions.ParseError):
        code, message = 10004, "请求数据格式有误"
    elif isinstance(exc, exceptions.Throttled):
        code, message = 10029, "操作过于频繁，请稍后再试"
    elif isinstance(exc, exceptions.NotAcceptable):
        code, message = 10006, "无法处理请求的响应格式"
    elif isinstance(exc, exceptions.UnsupportedMediaType):
        code, message = 10015, "不支持的请求媒体类型"

    response.data = build_payload(data, message, code, request)
    return response


def api_not_found_view(request, exception=None):
    if request.path.startswith("/api/"):
        payload = build_payload(None, "请求的资源不存在", 10002)
        return JsonResponse(payload, status=404, json_dumps_params={"ensure_ascii": False})
    from django.views.defaults import page_not_found

    return page_not_found(request, exception)
