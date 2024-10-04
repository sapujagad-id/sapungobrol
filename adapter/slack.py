from fastapi import Request, Response, HTTPException
from loguru import logger
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from chat.chat import Chat

class SlackAdapter:
    def __init__(self, app: App, chatbot: Chat) -> None:
        self.app = app
        self.handler = SlackRequestHandler(self.app)
        self.logger = logger.bind(service="SlackAdapter")
        self.chatbot = chatbot

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
        
        question = f"<@{user_id}> asked: \n\n\"{question}\" "

        try:
            response = self.app.client.chat_postMessage(channel=channel_id, text=question)
            thread_ts = response["ts"]
            
            loading_message = self.app.client.chat_postMessage(
                channel=channel_id,
                text=":hourglass_flowing_sand: Processing your request, please wait...",
                thread_ts=thread_ts
            )
            
            chatbot_response = self.chatbot.generate_response(query=question)
            
            self.app.client.chat_update(
                channel=channel_id,
                ts=loading_message["ts"],
                text=chatbot_response
            )
            
            return Response(status_code=200)

        except SlackApiError as e:
            if 'thread_ts' in locals():
                try:
                    self.app.client.chat_delete(channel=channel_id, ts=thread_ts)
                except SlackApiError as delete_error:
                    raise HTTPException(status_code=400, detail=f"Slack API Error : {delete_error}")

            raise HTTPException(status_code=400, detail=f"Slack API Error : {e}")
        
