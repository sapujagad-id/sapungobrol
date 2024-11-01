import time
import traceback

from typing import Callable

from fastapi import FastAPI, Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
    ) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:

        request_id: str = str(uuid4())

        with logger.contextualize(trace_id=request_id):
            logging_dict = {"trace_id": request_id}

            response, response_dict = await self._log_response(
                call_next, request, request_id
            )
            request_dict = await self._log_request(request)
            logging_dict["request"] = request_dict
            logging_dict["response"] = response_dict

            logger.bind(**logging_dict).info("Incoming request")

        return response

    async def _log_request(self, request: Request) -> str:
        """Logs request part
         Arguments:
        - request: Request

        """

        path = request.url.path
        if request.query_params:
            path += f"?{request.query_params}"

        request_logging = {
            "method": request.method,
            "path": path,
            "origin_ip": request.client.host,
            "user_agent": request.headers.get("User-Agent"),
        }

        return request_logging

    async def _log_response(
        self, call_next: Callable, request: Request, request_id: str
    ) -> Response:
        """Logs response part

        Arguments:
        - call_next: Callable (To execute the actual path function and get response back)
        - request: Request
        - request_id: str (uuid)
        Returns:
        - response: Response
        - response_logging: str
        """

        start_time = time.time()
        response = await self._execute_request(call_next, request, request_id)
        finish_time = time.time()

        execution_time = finish_time - start_time  # in milliseconds

        response_logging = {
            "status": response.status_code,
            "elapsed_time": f"{execution_time:0.4f}s",
        }

        return response, response_logging

    async def _execute_request(
        self, call_next: Callable, request: Request, request_id: str
    ) -> Response:
        """Executes the actual path function using call_next.
        It also injects "X-API-Request-ID" header to the response.

        Arguments:
        - call_next: Callable (To execute the actual path function
                     and get response back)
        - request: Request
        - request_id: str (uuid)
        Returns:
        - response: Response
        """
        try:
            response: Response = await call_next(request)

            # Kickback X-Request-ID
            response.headers["X-TRACE-ID"] = request_id
            return response

        except Exception as e:
            logger.bind(stacktrace=traceback.format_exception(e)).error(
                "Unhandled error"
            )

            response = Response(status_code=500, content="Something went wrong")
            response.headers["X-TRACE-ID"] = request_id

            return response
