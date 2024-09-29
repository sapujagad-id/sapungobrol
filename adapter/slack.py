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
        data = await request.form()
    
        channel_id = data.get("channel_id")
        user_id = data.get("user_id")
        parameter = data.get("text", "")
          
        parts = parameter.split(" ", 1) 
        if len(parts) == 2:
            _, question = parts
        else:
            raise HTTPException(status_code=400, detail="Missing parameter in the request.")

            
        user_info = self.app.client.users_info(user=user_id)
        display_name = user_info["user"]["profile"]["display_name"]
        
        question = f"{question} \n\n-{display_name}"

        self.app.client.chat_postMessage(channel=channel_id, text=question)