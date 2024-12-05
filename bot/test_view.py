from datetime import datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4
import jinja2
import pytest
from fastapi import Request
from fastapi.exceptions import HTTPException

from common.shared_types import MessageAdapter
from bot.bot import ModelEngine
from jose import jwt

        
class TestBotViews:
    def test_show_list_chatbots(self, setup_bots):
        context = {
        'bots': setup_bots
        }
        env = jinja2.Environment(
        loader = jinja2.FileSystemLoader(['bot/templates', 'components/templates']),
        autoescape = True,
        )
        rendered = env.get_template('list.html').render(context)
    
        # Validate Template
        assert 'List of Chatbots' in rendered
        assert 'Message Adapter' in rendered
        assert 'Model' in rendered
        assert 'Edit Chatbot' not in rendered
        
        # Validate Content
        assert 'Updated just now' in rendered
        assert 'OpenAI' in rendered
        assert 'Slack' in rendered
        assert 'Bot A' in rendered
        assert 'Bot B' in rendered
        assert 'Non-existent Bot X' not in rendered
        
    def test_empty_show_list_chatbots(self):
        context = {
        'bots': []
        }
        env = jinja2.Environment(
        loader = jinja2.FileSystemLoader(['bot/templates', 'components/templates']),
        autoescape = True,
        )
        rendered = env.get_template('list.html').render(context)
    
        
        # Validate Template
        assert 'List of Chatbots' in rendered
        assert 'Message Adapter' in rendered
        assert 'Model' in rendered
        assert 'Edit Chatbot' not in rendered
        
        # Validate Content
        assert 'Updated Just Now' not in rendered
        assert 'OpenAI' not in rendered
        assert 'Slack' not in rendered
        assert 'Bot A' not in rendered

    

    def test_empty_model_and_adapter_fields(self):
        # Context with empty model_engines and message_adapters
        context = {
            'model_engines': [],
            'message_adapters': []
        }

        # Setup Jinja2 environment and load the template
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(['bot/templates', 'components/templates']),
            autoescape=True,
        )
        rendered = env.get_template('create-chatbot.html').render(context)

        # Validate empty select fields for model and adapter
        assert '<select id="model"' in rendered
        assert '<select id="adapter"' in rendered
        assert '<option value="' not in rendered  # No options should be present

    def test_render_create_chatbot_form(self):
        # Context simulates the data passed to the template
        context = {
            'model_engines': [e.value for e in ModelEngine],
            'message_adapters': [e.value for e in MessageAdapter],
            "data_source":["docs1","docs2","docs3"]
        }

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(['bot/templates', 'components/templates']),
            autoescape=True,
        )
        rendered = env.get_template('create-chatbot.html').render(context)

        assert '<form id="chatbot-form"' in rendered
        assert 'Create Chatbot' in rendered
        assert '<label for="name"' in rendered
        assert '<label for="system_prompt"' in rendered
        assert '<label for="model"' in rendered
        assert '<label for="adapter"' in rendered

        assert '<option value="OpenAI">OpenAI</option>' in rendered
        assert '<option value="Slack">Slack</option>' in rendered
        assert 'docs1' in rendered

    

    def test_render_edit_chatbot_form(self):
        context = {
            'bot': {
                'id': uuid4(),
                'name': 'Test Bot',
                'system_prompt': 'This is a test bot prompt.',
                'model': 'OpenAI',
                'adapter': 'Slack'
            },
            'model_engines': [e.value for e in ModelEngine],
            'message_adapters': [e.value for e in MessageAdapter],
            "data_source":["docs1","docs2","docs3"]
        }

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(['bot/templates', 'components/templates']),
            autoescape=True,
        )
        rendered = env.get_template('edit-chatbot.html').render(context)

        assert '<form id="chatbot-form"' in rendered
        assert 'Edit Chatbot' in rendered
        assert '<label for="name"' in rendered
        assert '<label for="system_prompt"' in rendered
        assert '<label for="model"' in rendered
        assert '<label for="adapter"' in rendered

        assert 'value="Test Bot"' in rendered
        assert 'This is a test bot prompt.' in rendered
        assert '<option value="OpenAI" selected' in rendered
        assert '<option value="Slack" selected' in rendered
        assert 'docs2' in rendered

    def test_show_list_chatbots(self, setup_view, setup_service, setup_jwt_secret, dummy_user_profile):
        view = setup_view

        # Create a mock request
        request = Mock(spec=Request)

        # Encode a token using the provided JWT secret from the fixture
        token = jwt.encode({
            "sub": "test_sub",
            "email": "test@broom.id",
            "exp": datetime.now() + timedelta(hours=3)
        }, setup_jwt_secret)  # Use the fixture's JWT secret

        # Set the cookies on the request mock
        request.cookies = {'token': token}  # Set the token correctly here

        # Mock the controller's fetch_chatbots method
        view.controller.fetch_chatbots = Mock(return_value=[
            {
                'id': uuid4(),
                'name': 'Bot A',
                'system_prompt': 'Prompt A',
                'model': 'OpenAI',
                'adapter': 'Slack',
                'updated_at': datetime.now(),
            },
            {
                'id': uuid4(),
                'name': 'Bot B',
                'system_prompt': 'Prompt B',
                'model': 'GPT-3',
                'adapter': 'Discord',
                'updated_at': datetime.now(),
            },
        ])

        # Mock the user_profile_google method
        view.auth_controller.user_profile_google = Mock(return_value=dummy_user_profile)

        # Call the view method
        response = view.show_list_chatbots(request)

        # Check that the correct template is used and context is passed
        assert response.template.name == "list.html"
        assert "bots" in response.context
        assert len(response.context["bots"]) == 2
        assert "user_profile" in response.context
        assert response.context["user_profile"].get('email') == dummy_user_profile.get("data")["email"]

        # Validate if bot names are present in the rendered template
        rendered = response.body.decode()  # Decode response body for assertion
        assert 'List of Chatbots' in rendered
        assert 'Bot A' in rendered
        assert 'Bot B' in rendered

    def test_show_create_chatbot(self, setup_view, setup_service, dummy_user_profile, setup_jwt_secret):
        view = setup_view

        view.auth_controller.user_profile_google = Mock(return_value=dummy_user_profile)

        request = Mock(spec=Request)
        token = jwt.encode({
            "sub": "test_sub",
            "email": "test@broom.id",
            "exp": datetime.now() + timedelta(hours=3)
        }, setup_jwt_secret) 
        request.cookies = {'token': token}

        response = view.show_create_chatbots(request=request)

        assert response.template.name == "create-chatbot.html"
        assert response.context["user_profile"].get('email') == dummy_user_profile.get("data")["email"]

    def test_show_edit_chatbot(self, setup_view, setup_service, dummy_user_profile, setup_jwt_secret):
        view = setup_view
        bot_id = str(uuid4())

        setup_service.get_chatbot_by_id = Mock(return_value={
            'id': bot_id,
            'name': 'Test Bot',
            'system_prompt': 'This is a test bot prompt.',
            'model': 'OpenAI',
            'adapter': 'Slack',
        })

        view.auth_controller.user_profile_google = Mock(return_value=dummy_user_profile)

        request = Mock(spec=Request)
        token = jwt.encode({
            "sub": "test_sub",
            "email": "test@broom.id",
            "exp": datetime.now() + timedelta(hours=3)
        }, setup_jwt_secret)
        request.cookies = {'token': token}

        response = view.show_edit_chatbot(bot_id, request=request)

        assert response.template.name == "edit-chatbot.html"
        assert "bot" in response.context
        assert response.context["bot"]["name"] == 'Test Bot'
        assert response.context["user_profile"].get('email') == dummy_user_profile.get("data")["email"]
        assert 'value="Test Bot"' in response.body.decode() 

    def test_show_login(self, setup_view):
        view = setup_view

        request = Mock(spec=Request)

        response = view.show_login(request)

        assert response.template.name == "login.html"

        rendered = response.body.decode()  
        assert 'Login' in rendered

    @pytest.mark.asyncio
    async def test_show_dashboard(self, setup_view, dummy_user_profile, setup_jwt_secret):
        view = setup_view

        view.controller.fetch_chatbots = Mock(return_value=[
            {"id": uuid4(), "name": "Bot A", "model": "OpenAI", "adapter": "Slack"},
            {"id": uuid4(), "name": "Bot B", "model": "GPT-3", "adapter": "Discord"},
        ])
        view.auth_controller.user_profile_google = Mock(return_value=dummy_user_profile)

        view = setup_view

        request = Mock(spec=Request)

        token = jwt.encode({
            "sub": "test_sub",
            "email": "test@broom.id",
            "exp": datetime.now() + timedelta(hours=3)
        }, setup_jwt_secret)  

        request.cookies = {'token': token}
        
        response = view.show_dashboard(request)

        assert response.template.name == "dashboard.html"
        assert "bots" in response.context
        assert len(response.context["bots"]) == 2
        assert "user_profile" in response.context

    @pytest.mark.asyncio
    async def test_show_dashboard_with_id_success(self, setup_view, dummy_user_profile, setup_jwt_secret):
        view = setup_view
        bot_id = str(uuid4())

        view.controller.fetch_chatbots = Mock(return_value=[
            Mock(id=bot_id, name="Bot A", model="OpenAI", adapter="Slack"),
            Mock(id=str(uuid4()), name="Bot B", model="GPT-3", adapter="Discord"),
        ])
        view.auth_controller.user_profile_google = Mock(return_value=dummy_user_profile)

        request = Mock()
        request.cookies = {
            "token": jwt.encode({
                "sub": "test_sub",
                "email": "test@broom.id",
                "exp": datetime.now() + timedelta(hours=3)
            }, setup_jwt_secret)
        }

        response = view.show_dashboard_with_id(request, bot_id)

        assert response.template.name == "dashboard.html"
        assert response.context["selected_bot_id"] == bot_id
        assert "bots" in response.context

    @pytest.mark.asyncio
    async def test_show_dashboard_with_id_not_found(self, setup_view, dummy_user_profile, setup_jwt_secret):
        view = setup_view
        bot_id = str(uuid4())

        view.controller.fetch_chatbots = Mock(return_value=[
            Mock(id=str(uuid4()), name="Bot A", model="OpenAI", adapter="Slack"),
            Mock(id=str(uuid4()), name="Bot B", model="GPT-3", adapter="Discord"),
        ])
        view.auth_controller.user_profile_google = Mock(return_value=dummy_user_profile)

        request = Mock()
        request.cookies = {
            "token": jwt.encode({
                "sub": "test_sub",
                "email": "test@broom.id",
                "exp": datetime.now() + timedelta(hours=3)
            }, setup_jwt_secret)
        }

        with pytest.raises(HTTPException) as exc:
            await view.show_dashboard_with_id(request, bot_id)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Bot not found"
        