from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from slack_sdk.oauth.installation_store.models.bot import Bot
from slack_sdk.oauth.installation_store.models.installation import Installation
from sqlalchemy.orm import sessionmaker

from .slack_dto import WorkspaceData
from .slack_repository import (CustomInstallationStore,
                               PostgresWorkspaceDataRepository,
                               WorkspaceDataModel)


class TestSlackRepository:
    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=sessionmaker)

    @pytest.fixture
    def mock_workspace_data(self):
        return WorkspaceData(
            team_id="T12345678",
            access_token="xoxb-mock-token",
        )

    @pytest.fixture
    def workspace_data_repository(self, mock_session):
        return PostgresWorkspaceDataRepository(session=mock_session)

    @pytest.fixture
    def installation_store(self, workspace_data_repository):
        store = CustomInstallationStore(workspace_data_repository=workspace_data_repository)
        store.log = MagicMock() 
        return store

    def test_create_workspace_data_new(self, workspace_data_repository, mock_session, mock_workspace_data):
        mock_session_instance = mock_session.return_value.__enter__.return_value
        workspace_data_repository.create_workspace_data(mock_workspace_data)

        assert mock_session_instance.add.called
        assert mock_session_instance.commit.called

    def test_create_workspace_data_existing(self, workspace_data_repository, mock_session, mock_workspace_data):
        mock_session_instance = mock_session.return_value.__enter__.return_value

        existing_data = WorkspaceDataModel(
            id=uuid4(),
            team_id=mock_workspace_data.team_id,
            access_token="xoxb-old-token",
        )
        mock_session_instance.query.return_value.filter.return_value.first.return_value = existing_data

        workspace_data_repository.create_workspace_data(mock_workspace_data)

        assert mock_session_instance.delete.called
        assert mock_session_instance.add.called
        assert mock_session_instance.commit.called

    def test_get_workspace_data_by_team_id(self, workspace_data_repository, mock_session):
        mock_session_instance = mock_session.return_value.__enter__.return_value

        mock_data = WorkspaceDataModel(
            id=uuid4(),
            team_id="T12345678",
            access_token="xoxb-mock-token",
        )
        mock_session_instance.query.return_value.filter.return_value.first.return_value = mock_data

        result = workspace_data_repository.get_workspace_data_by_team_id("T12345678")

        assert result.team_id == "T12345678"
        assert result.access_token == "xoxb-mock-token"

    def test_get_all_workspace_data(self, workspace_data_repository, mock_session):
        mock_data = [
            WorkspaceDataModel(
                id=uuid4(),
                team_id="T12345678",
                access_token="xoxb-mock-token-1",
            ),
            WorkspaceDataModel(
                id=uuid4(),
                team_id="T87654321",
                access_token="xoxb-mock-token-2",
            ),
        ]

        mock_session_instance = mock_session.return_value.__enter__.return_value
        mock_session_instance.query.return_value.all.return_value = mock_data

        result = workspace_data_repository.get_all_workspace_data()

        assert len(result) == 2
        assert result[0].team_id == "T12345678"
        assert result[0].access_token == "xoxb-mock-token-1"
        assert result[1].team_id == "T87654321"
        assert result[1].access_token == "xoxb-mock-token-2"

    def test_custom_installation_store_save(self, installation_store, workspace_data_repository):
        installation = Installation(
            team_id="T12345678",
            bot_token="xoxb-mock-token",
            user_id="U12345678",
        )

        workspace_data_repository.create_workspace_data = MagicMock()

        installation_store.save(installation)

        workspace_data_repository.create_workspace_data.assert_called_once()

    def test_custom_installation_store_find_installation(self, installation_store, workspace_data_repository):
        mock_data = WorkspaceDataModel(
            id=uuid4(),
            team_id="T12345678",
            access_token="xoxb-mock-token",
        )
        workspace_data_repository.get_workspace_data_by_team_id = MagicMock(return_value=mock_data)

        result = installation_store.find_installation(
            enterprise_id=None,
            team_id="T12345678",
        )

        assert result.team_id == "T12345678"
        assert result.bot_token == "xoxb-mock-token"

    def test_custom_installation_store_find_bot(self, installation_store, workspace_data_repository, monkeypatch):
        mock_data = WorkspaceDataModel(
            id=uuid4(),
            team_id="T12345678",
            access_token="xoxb-mock-token",
            installed_at=datetime.now()
        )
        workspace_data_repository.get_workspace_data_by_team_id = MagicMock(return_value=mock_data)

        mock_client = MagicMock()
        mock_client.bots_info.return_value = {
            "bot": {
                "id": "B12345678",
                "user_id": "U12345678",
            }
        }
        monkeypatch.setattr("slack_sdk.WebClient.bots_info", mock_client.bots_info)

        result = installation_store.find_bot(
            enterprise_id=None,
            team_id="T12345678",
        )

        assert result is not None
        assert isinstance(result, Bot)
        assert result.team_id == "T12345678"
        assert result.bot_token == "xoxb-mock-token"
        assert result.bot_id == "B12345678"
        assert result.bot_user_id == "U12345678"

        workspace_data_repository.get_workspace_data_by_team_id.assert_called_once_with("T12345678")