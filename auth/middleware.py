import re

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from jose import jwt
from loguru import logger


class AuthMiddleware:
    def __init__(self, app: FastAPI, jwt_secret_key: str, login_url: str = "/login", included_routes: list[str] = None):
        self.app = app
        self.jwt_secret_key = jwt_secret_key
        self.login_url = login_url
        self.included_routes = included_routes or []

        self.regex_patterns = []
        for route in self.included_routes:
            if "{" in route and "}" in route:  
                pattern = re.sub(r"{[^}]+}", r"[^/]+", route)
                pattern = f"^{pattern}$"
                self.regex_patterns.append(re.compile(pattern))  

    def is_route_included(self, path: str) -> bool:
        """
        Check if the given path matches any route in the included_routes list.
        """
        for route in self.included_routes:
            if self._is_wildcard_match(route, path):
                return True
            if self._is_exact_match(route, path):
                return True
            if self._is_dynamic_match(route, path):
                return True
        return False

    def _is_wildcard_match(self, route: str, path: str) -> bool:
        """
        Check if the path matches a wildcard route (e.g., `/api/*`).
        """
        return route.endswith("*") and path.startswith(route.rstrip("*"))

    def _is_exact_match(self, route: str, path: str) -> bool:
        """
        Check if the path matches an exact route.
        """
        return path == route

    def _is_dynamic_match(self, route: str, path: str) -> bool:
        """
        Check if the path matches a dynamic route (e.g., `/edit/{id}`).
        """
        if "{" in route and "}" in route:
            for pattern in self.regex_patterns:
                if pattern.match(path):
                    return True
        return False

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive, send)
            path = request.url.path
            logger.debug(f"Processing path: {path}")

            if path == self.login_url:
                logger.debug("Login route, bypassing middleware.")
                await self.app(scope, receive, send)
                return

            if self.is_route_included(path):
                logger.debug("Route included in middleware.")
                token = request.cookies.get("token")
                if not token:
                    logger.debug("No token found, redirecting to login.")
                    response = RedirectResponse(url=self.login_url)
                    await response(scope, receive, send)
                    return

                try:
                    jwt.decode(token, self.jwt_secret_key, algorithms=["HS256"])
                    logger.debug("Token is valid.")
                except Exception:
                    logger.debug("Invalid token, redirecting to login.")
                    response = RedirectResponse(url=self.login_url)
                    await response(scope, receive, send)
                    return

        await self.app(scope, receive, send)
