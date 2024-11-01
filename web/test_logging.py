import pytest
from unittest.mock import MagicMock, AsyncMock, PropertyMock

from fastapi import FastAPI, Request, Response
from typing import Callable
from uuid import uuid4, UUID

from .logging import RequestLoggingMiddleware


class TestRequestLoggingMiddleware:
    @pytest.fixture
    def mock_callable(self):
        return AsyncMock(spec=Callable)

    @pytest.fixture
    def mock_request(self):
        return PropertyMock(spec=Request)

    @pytest.mark.asyncio
    async def test_dispatch_and_log_request(self, mock_request, mock_callable):
        middleware = RequestLoggingMiddleware(FastAPI())

        mock_callable.return_value = Response(status_code=200)

        mock_request.url.path = "/api/slack/interactivity"
        mock_request.query_params = "epic=gamer"
        mock_request.method = "GET"
        mock_request.client.host = "1.1.1.1"
        mock_request.headers = {"User-Agent": "SomeUserAgent"}

        request_logging = await middleware._log_request(mock_request)
        response = await middleware.dispatch(mock_request, mock_callable)

        assert request_logging["path"] == "/api/slack/interactivity?epic=gamer"
        assert request_logging["method"] == "GET"
        assert request_logging["origin_ip"] == "1.1.1.1"
        assert request_logging["user_agent"] == "SomeUserAgent"

        assert UUID(response.headers["X-TRACE-ID"])

    @pytest.mark.asyncio
    async def test_log_response(self, mock_callable, mock_request):
        trace_id = str(uuid4())

        mock_callable.return_value = Response(status_code=200)

        middleware = RequestLoggingMiddleware(FastAPI())

        _, response_logging = await middleware._log_response(
            mock_callable, mock_request, trace_id
        )

        assert response_logging["status"] == 200
        assert response_logging["elapsed_time"] is not None

    @pytest.mark.asyncio
    async def test_execute_request(self, mock_callable, mock_request):
        trace_id = str(uuid4())

        mock_callable.return_value = Response(status_code=200)

        middleware = RequestLoggingMiddleware(FastAPI())

        res = await middleware._execute_request(mock_callable, mock_request, trace_id)

        assert res.headers.get("X-TRACE-ID") == trace_id
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_execute_request_error(self, mock_callable, mock_request):
        trace_id = str(uuid4())

        mock_callable.side_effect = Exception

        middleware = RequestLoggingMiddleware(FastAPI())

        res = await middleware._execute_request(mock_callable, mock_request, trace_id)

        assert res.headers.get("X-TRACE-ID") == trace_id
        assert res.status_code == 500
