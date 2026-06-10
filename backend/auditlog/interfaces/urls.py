from django.urls import path

from auditlog.interfaces import api

urlpatterns = [
    path("events/", api.events_list_view, name="api-admin-audit-events"),
    path("events/<int:event_id>/", api.event_detail_view, name="api-admin-audit-event-detail"),
    path("actions/", api.actions_view, name="api-admin-audit-actions"),
]
