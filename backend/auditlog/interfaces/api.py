from __future__ import annotations

from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from auditlog.application import query_service
from auditlog.interfaces.permissions import IsStaffAuditReader
from auditlog.interfaces.serializers import AuditEventSerializer


@api_view(["GET"])
@permission_classes([IsStaffAuditReader])
def events_list_view(request):
    """Обрабатывает API-представление для events list.

    Args:
        request: HTTP-запрос с контекстом пользователя и входными данными.

    Returns:
        Результат вычислений, сформированный в ходе выполнения функции.
    """
    try:
        filters = query_service.parse_filters(request.query_params)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=http_status.HTTP_400_BAD_REQUEST)

    items, next_cursor = query_service.list_events(filters)
    serializer = AuditEventSerializer(items, many=True)
    return Response({"items": serializer.data, "nextCursor": next_cursor})


@api_view(["GET"])
@permission_classes([IsStaffAuditReader])
def event_detail_view(_request, event_id: int):
    """Обрабатывает API-представление для event detail.

    Args:
        _request: HTTP-запрос, не используемый напрямую в теле функции.
        event_id: Идентификатор event.

    Returns:
        Результат вычислений, сформированный в ходе выполнения функции.
    """
    item = query_service.get_event(event_id)
    if not item:
        return Response({"error": "Не найдено"}, status=http_status.HTTP_404_NOT_FOUND)
    serializer = AuditEventSerializer(item)
    return Response({"item": serializer.data})


@api_view(["GET"])
@permission_classes([IsStaffAuditReader])
def actions_view(request):
    """Обрабатывает API-представление для actions.

    Args:
        request: HTTP-запрос с контекстом пользователя и входными данными.

    Returns:
        Результат вычислений, сформированный в ходе выполнения функции.
    """
    try:
        filters = query_service.parse_filters(request.query_params)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=http_status.HTTP_400_BAD_REQUEST)

    items = query_service.list_action_counts(filters)
    return Response({"items": items})
