"""Contains chat API routing."""

from django.urls import include, path

from . import api

urlpatterns = [
    path("public-room/", api.public_room, name="api-public-room"),
    path("direct/start/", api.direct_start, name="api-direct-start"),
    path("direct/chats/", api.direct_chats, name="api-direct-chats"),
    path("search/global/", api.global_search, name="api-global-search"),
    path("rooms/unread/", api.unread_counts, name="api-unread-counts"),
    path("rooms/<int:room_id>/", include("roles.interfaces.urls")),
    path("rooms/<int:room_id>/messages/search/", api.search_messages, name="api-search-messages"),
    path("rooms/<int:room_id>/messages/<int:message_id>/reactions/<str:emoji>/", api.message_reaction_remove, name="api-message-reaction-remove"),
    path("rooms/<int:room_id>/messages/<int:message_id>/reactions/", api.message_reactions, name="api-message-reactions"),
    path("rooms/<int:room_id>/messages/<int:message_id>/", api.message_detail, name="api-message-detail"),
    path("rooms/<int:room_id>/messages/", api.room_messages, name="api-room-messages"),
    path("rooms/<int:room_id>/attachments/", api.upload_attachments, name="api-upload-attachments"),
    path("rooms/<int:room_id>/read/", api.mark_read_view, name="api-mark-read"),
    path("rooms/<int:room_id>/", api.room_details, name="api-room-details"),
]

