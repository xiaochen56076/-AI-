from collections import OrderedDict
from typing import Any

from rest_framework.response import Response

from common.request_context import get_request_id


def build_payload(
    data: Any = None,
    message: str = "操作成功",
    code: int = 0,
    request=None,
) -> OrderedDict:
    request_id = getattr(request, "request_id", None) or get_request_id()
    return OrderedDict(
        [
            ("code", code),
            ("message", message),
            ("data", data),
            ("request_id", request_id),
        ]
    )


def success(
    data: Any = None, message: str = "操作成功", request=None, status: int = 200
) -> Response:
    return Response(build_payload(data, message, 0, request), status=status)


def created(data: Any = None, message: str = "创建成功", request=None) -> Response:
    return success(data, message, request, status=201)


def paginated(
    paginator,
    results,
    message: str = "获取成功",
    request=None,
) -> Response:
    data = OrderedDict(
        [
            ("total", paginator.page.paginator.count),
            ("page", paginator.page.number),
            ("page_size", paginator.get_page_size(request)),
            ("results", results),
        ]
    )
    return success(data, message, request)
