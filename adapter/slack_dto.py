from pydantic import BaseModel

class SlackConfig(BaseModel):
    slack_bot_token: str
    slack_signing_secret: str
    slack_client_id: str
    slack_client_secret: str
    slack_scopes: list[str]

class WorkspaceData(BaseModel):
    team_id: str
    access_token: str