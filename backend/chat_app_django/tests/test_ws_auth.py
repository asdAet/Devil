"""Tests for opaque websocket auth tokens and middleware restoration."""

from __future__ import annotations

from asgiref.sync import async_to_sync
from asgiref.typing import (
    ASGIReceiveCallable,
    ASGIReceiveEvent,
    ASGISendEvent,
    WebSocketDisconnectEvent,
    WebSocketScope,
)
import json
import tempfile
from typing import Any, cast
from django.contrib.auth.models import AnonymousUser
from django.core.cache.backends.filebased import FileBasedCache
from django.test import Client, TestCase
from unittest.mock import patch

from chat_app_django import ws_auth as ws_auth_module
from chat_app_django.ws_auth import (
    issue_authenticated_ws_auth_token,
    issue_guest_ws_auth_token,
)
from chat_app_django.ws_auth_middleware import WebSocketTokenAuthMiddleware
from users.application import auth_service
from users.models import User


class ChannelWebSocketScope(WebSocketScope, total=False):
    channel: str
    url_route: Any
    path_remaining: str
    cookies: dict[str, str]
    session: Any
    user: Any


class WebSocketTokenAuthMiddlewareTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            login="ws_auth_user",
            password="pass12345",
        )

    def _run_middleware(self, *, query_string: str, user=None):
        captured_scope: dict[str, object] = {}

        async def app(scope: ChannelWebSocketScope, receive: ASGIReceiveCallable, send) -> None:
            captured_scope.update(scope)

        async def receive() -> ASGIReceiveEvent:
            event: WebSocketDisconnectEvent = {
                "type": "websocket.disconnect",
                "code": 1000,
                "reason": "",
            }
            return event

        async def send(_message: ASGISendEvent) -> None:
            return None

        middleware = WebSocketTokenAuthMiddleware(app)
        scope: ChannelWebSocketScope = {
            "type": "websocket",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "scheme": "ws",
            "path": "/ws/",
            "raw_path": b"/ws/",
            "query_string": query_string.encode("utf-8"),
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "subprotocols": [],
            "extensions": {},
            "channel": "test.websocket",
            "url_route": {"args": (), "kwargs": {}},
            "path_remaining": "",
            "cookies": {},
            "session": {},
            "user": user if user is not None else AnonymousUser(),
        }
        async_to_sync(middleware)(cast(Any, scope), receive, send)
        return captured_scope

    def test_authenticated_token_restores_scope_user(self):
        client = Client()
        client.force_login(self.user)
        session_key = client.session.session_key
        assert session_key is not None

        token = issue_authenticated_ws_auth_token(
            user_id=self.user.pk,
            session_key=session_key,
        )

        scope = self._run_middleware(query_string=f"wst={token}")
        restored_user = scope.get("user")

        self.assertIsNotNone(restored_user)
        self.assertTrue(getattr(restored_user, "is_authenticated", False))
        self.assertEqual(getattr(restored_user, "pk", None), self.user.pk)

    def test_guest_token_restores_guest_session_key(self):
        client = Client()
        response = client.get("/api/auth/presence-session/")
        self.assertEqual(response.status_code, 200)
        session_key = client.session.session_key
        assert session_key is not None

        token = issue_guest_ws_auth_token(session_key=session_key)
        scope = self._run_middleware(query_string=f"wst={token}")

        self.assertEqual(scope.get("ws_guest_session_key"), session_key)

    def test_invalidated_session_does_not_restore_user(self):
        client = Client()
        client.force_login(self.user)
        session_key = client.session.session_key
        assert session_key is not None

        token = issue_authenticated_ws_auth_token(
            user_id=self.user.pk,
            session_key=session_key,
        )
        client.logout()

        scope = self._run_middleware(query_string=f"wst={token}")
        restored_user = scope.get("user")

        self.assertFalse(getattr(restored_user, "is_authenticated", False))

    def test_login_endpoint_token_restores_user_immediately(self):
        auth_service.register_user(
            login="wsauthlogin",
            password="pass12345",
            password_confirm="pass12345",
            name="WS Auth Login User",
            email="wsauthlogin@example.com",
        )

        client = Client(enforce_csrf_checks=True)
        csrf_response = client.get("/api/auth/csrf/")
        self.assertEqual(csrf_response.status_code, 200)
        csrf_token = csrf_response.cookies["csrftoken"].value

        login_response = client.post(
            "/api/auth/login/",
            data=json.dumps(
                {
                    "identifier": "wsauthlogin",
                    "password": "pass12345",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(login_response.status_code, 200)

        token = login_response.json().get("wsAuthToken")
        self.assertTrue(token)

        scope = self._run_middleware(query_string=f"wst={token}")
        restored_user = scope.get("user")

        self.assertIsNotNone(restored_user)
        self.assertTrue(getattr(restored_user, "is_authenticated", False))

    def test_tokens_round_trip_across_distinct_shared_cache_instances(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            issuer_cache = FileBasedCache(cache_dir, {})
            resolver_cache = FileBasedCache(cache_dir, {})

            with patch(
                "chat_app_django.ws_auth._get_ws_auth_cache",
                side_effect=[issuer_cache, resolver_cache],
            ):
                token = ws_auth_module.issue_authenticated_ws_auth_token(
                    user_id=self.user.pk,
                    session_key="shared-session-key",
                )
                claims = ws_auth_module.resolve_ws_auth_claims(token)

        self.assertEqual(
            claims,
            ws_auth_module.WebSocketAuthClaims(
                kind="auth",
                session_key="shared-session-key",
                user_id=self.user.pk,
            ),
        )
