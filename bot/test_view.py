from datetime import datetime
from uuid import uuid4
import jinja2

from bot.bot import BotCreate, BotResponse, MessageAdapter, ModelEngine
from bot.helper import relative_time

class TestBotViews:
  def test_show_list_chatbots(self, setup_bots):

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
    assert 'Updated Just Now'
    assert 'OpenAI' in rendered
    assert 'Slack' in rendered
    assert 'Bot A' in rendered
    assert 'Bot B' in rendered
    assert 'Non-existent Bot X' not in rendered