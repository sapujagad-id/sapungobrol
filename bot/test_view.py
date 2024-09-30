from datetime import datetime
from uuid import uuid4
import jinja2
import pytest

from bot.bot import BotCreate, BotResponse, MessageAdapter, ModelEngine
from bot.helper import relative_time

@pytest.fixture
def setup_bots():
  return [
    BotResponse(
        id = uuid4(),
        name = "Bot A",
        system_prompt = "prompt A here",
        model = ModelEngine.OPENAI,
        adapter = MessageAdapter.SLACK,
        created_at = datetime.fromisocalendar(2024, 1, 1),
        updated_at = datetime.fromisocalendar(2024, 1, 1),
        updated_at_relative = relative_time(datetime.fromisocalendar(2024, 1, 1)),
    ),
    BotResponse(
        id = uuid4(),
        name = "Bot B",
        system_prompt = "a much longer prompt B here",
        model = ModelEngine.OPENAI,
        adapter = MessageAdapter.SLACK,
        created_at = datetime.now(),
        updated_at = datetime.now(),
        updated_at_relative = relative_time(datetime.now()),
    )
  ]

class TestBotViews:
  def test_show_list_chatbots(self, setup_bots):
    context = {
      'bots': setup_bots
    }

    env = jinja2.Environment(
      loader = jinja2.FileSystemLoader('bot/templates')
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
      loader = jinja2.FileSystemLoader('bot/templates')
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