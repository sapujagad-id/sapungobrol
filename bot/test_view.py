from datetime import datetime
from uuid import uuid4
import jinja2
import pytest

from bot.bot import BotCreate, BotResponse, MessageAdapter, ModelEngine
from bot.helper import relative_time

class TestBotViews:
  def test_show_list_chatbots(self, setup_bots):
    context = {
      'bots': setup_bots
    }
    env = jinja2.Environment(
      loader = jinja2.FileSystemLoader('bot/templates'),
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
      loader = jinja2.FileSystemLoader('bot/templates'),
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
          loader=jinja2.FileSystemLoader('bot/templates'),
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
          'message_adapters': [e.value for e in MessageAdapter]
      }

      env = jinja2.Environment(
          loader=jinja2.FileSystemLoader('bot/templates'),
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
          'message_adapters': [e.value for e in MessageAdapter]
      }

      env = jinja2.Environment(
          loader=jinja2.FileSystemLoader('bot/templates'),
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