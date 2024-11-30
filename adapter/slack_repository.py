from abc import abstractmethod, ABC
from loguru import logger
from datetime import datetime
from sqlalchemy import Column, Uuid, String, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from uuid import uuid4
from typing import Optional

from .slack_dto import WorkspaceData
from slack_bolt.authorization import AuthorizeResult
from slack_sdk import WebClient

from slack_sdk.oauth.installation_store import InstallationStore
from slack_sdk.oauth.installation_store.models.installation import Installation
from slack_sdk.oauth.installation_store.models.bot import Bot


Base = declarative_base()


class WorkspaceDataModel(Base):
    __tablename__ = "workspace_data"

    id = Column(Uuid, primary_key=True)
    team_id = Column(String(255), nullable=False)
    access_token = Column(String(255), nullable=False)
    installed_at = Column(DateTime, default=datetime.now)

class WorkspaceDataRepository(ABC):
    @abstractmethod
    def create_workspace_data(self, workspace_data: WorkspaceData): # pragma: no cover
        pass
    
    @abstractmethod
    def get_workspace_data_by_team_id(self, team_id:str) -> WorkspaceDataModel | None: # pragma: no cover
        pass

    @abstractmethod
    def get_all_workspace_data(self) -> list[WorkspaceData]: # pragma: no cover
        pass

class PostgresWorkspaceDataRepository(WorkspaceDataRepository):
    def __init__(self, session: sessionmaker[Session]) -> None:
        self.create_session = session
        self.logger = logger.bind(service="PostgresWorkspaceDataRepository")

    def create_workspace_data(self, workspace_data: WorkspaceData):
        self.logger.bind(
            team_id=workspace_data.team_id,
            access_token=workspace_data.access_token
        ).info("saving workspace data")

        with self.create_session() as session:
            with self.logger.catch(message="saving workspace data error", reraise=True):
                existing_workspace_data = self.get_workspace_data_by_team_id(workspace_data.team_id)

                if existing_workspace_data:
                    session.delete(existing_workspace_data)
                    self.logger.info(f"Deleted existing workspace data for team_id: {workspace_data.team_id}")

                workspace_data_id = uuid4()
                new_workspace_data = WorkspaceDataModel(
                    **workspace_data.model_dump(), id=workspace_data_id
                )
                session.add(new_workspace_data)
                self.logger.info(f"Created new workspace data for team_id: {workspace_data.team_id}")

                session.commit()

    def get_workspace_data_by_team_id(self, team_id:str) -> WorkspaceDataModel | None:
        with self.create_session() as session:
            with self.logger.catch(
                message=f"Workspace with team_id: {team_id} not found", 
                reraise=True,
            ):
                return session.query(WorkspaceDataModel).filter(WorkspaceDataModel.team_id == team_id).first()

    def get_all_workspace_data(self) -> list[WorkspaceData]:
        with self.create_session() as session:
            return session.query(WorkspaceDataModel).all()
        
class CustomInstallationStore(InstallationStore):
    def __init__(self, workspace_data_repository:WorkspaceDataRepository):
        self.workspace_data_repository = workspace_data_repository
        self.log = logger.bind(service="CustomInstallationStore")

    def save(self, installation: Installation):
        workspace_data = WorkspaceDataModel(
            team_id=installation.team_id,
            access_token=installation.bot_token,
        )
        self.log.info(f"save installation={installation.team_id, installation.bot_token}")
        self.workspace_data_repository.create_workspace_data(workspace_data)

    def find_installation(self, *, 
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False,
        ):
        with self.log.catch(message="Error getting installation", reraise=True):
            workspace_data = self.workspace_data_repository.get_workspace_data_by_team_id(team_id)
            if workspace_data:
                return Installation(
                    team_id=team_id,
                    bot_token=workspace_data.access_token,
                    user_id=user_id
                )
        
    def find_bot(self, *, 
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False) -> Optional[Bot]:
        with self.log.catch(message="Error getting bot", reraise=True):
            workspace_data = self.workspace_data_repository.get_workspace_data_by_team_id(team_id)
            client = WebClient(token=workspace_data.access_token)
            bot_info = client.bots_info(team_id=team_id)
            if workspace_data:
                return Bot(
                    team_id=team_id,
                    bot_token=workspace_data.access_token,
                    bot_id=bot_info["bot"]["id"],
                    bot_user_id=bot_info["bot"]["user_id"],
                    installed_at=workspace_data.installed_at
                )
