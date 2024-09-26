from fastapi import Request, Response, HTTPException
from loguru import logger
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler


class SlackAdapter:
    def __init__(self, app: App) -> None:
        self.app = app
        self.handler = SlackRequestHandler(self.app)
        self.logger = logger.bind(service="SlackAdapter")

    # Function to listen for events on Slack. No need to test this since this is purely dependent on
    # Bolt
    # pragma: no cover
    async def handle_events(self, req: Request):
        return await self.handler.handle(req)

    async def ask(self, request: Request):
        pass