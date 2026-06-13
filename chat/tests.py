"""
Comprehensive tests for the Chat app.
Tests cover: Models, Views, AI Chat fallback, AJAX endpoints.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from .models import ChatSession, ChatMessage
from .ai_chat import _get_fallback_response, get_chat_system_prompt


class ChatSessionModelTest(TestCase):
    """Tests for ChatSession model."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.session = ChatSession.objects.create(
            user=self.user, title='Test Chat', session_type='general'
        )

    def test_session_creation(self):
        """Chat session should be created successfully."""
        self.assertEqual(self.session.title, 'Test Chat')
        self.assertTrue(self.session.is_active)

    def test_session_str(self):
        """String representation should include username."""
        self.assertIn('testuser', str(self.session))

    def test_message_count_empty(self):
        """New session should have 0 messages."""
        self.assertEqual(self.session.message_count, 0)

    def test_message_count(self):
        """message_count should reflect actual message count."""
        ChatMessage.objects.create(session=self.session, role='user', content='Hi')
        ChatMessage.objects.create(session=self.session, role='assistant', content='Hello!')
        self.assertEqual(self.session.message_count, 2)

    def test_session_ordering(self):
        """Sessions should be ordered by -updated_at."""
        # Check Meta ordering is correct
        self.assertEqual(ChatSession._meta.ordering, ['-updated_at'])


class ChatMessageModelTest(TestCase):
    """Tests for ChatMessage model."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.session = ChatSession.objects.create(user=self.user)

    def test_message_creation(self):
        """Message should be created successfully."""
        msg = ChatMessage.objects.create(
            session=self.session, role='user', content='Hello!'
        )
        self.assertEqual(msg.role, 'user')
        self.assertEqual(msg.content, 'Hello!')

    def test_message_str(self):
        """String representation should include role and content preview."""
        msg = ChatMessage.objects.create(
            session=self.session, role='assistant', content='Hi there!'
        )
        self.assertIn('Hi there!', str(msg))

    def test_message_ordering(self):
        """Messages should be ordered by sent_at (oldest first)."""
        m1 = ChatMessage.objects.create(session=self.session, role='user', content='First')
        m2 = ChatMessage.objects.create(session=self.session, role='assistant', content='Second')
        messages = list(self.session.messages.all())
        self.assertEqual(messages[0], m1)
        self.assertEqual(messages[1], m2)

    def test_cascade_delete(self):
        """Messages should be deleted when session is deleted."""
        ChatMessage.objects.create(session=self.session, role='user', content='Test')
        self.session.delete()
        self.assertEqual(ChatMessage.objects.count(), 0)


class ChatViewTest(TestCase):
    """Tests for chat views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='TestPass123!', first_name='Test'
        )
        self.client.login(username='testuser', password='TestPass123!')

    def test_chat_page_loads(self):
        """Chat page should return 200."""
        response = self.client.get(reverse('chat:chat'))
        self.assertEqual(response.status_code, 200)

    def test_chat_creates_session(self):
        """Visiting chat should auto-create a session."""
        self.client.get(reverse('chat:chat'))
        self.assertTrue(ChatSession.objects.filter(user=self.user).exists())

    def test_chat_welcome_message(self):
        """New session should have a welcome message."""
        self.client.get(reverse('chat:chat'))
        session = ChatSession.objects.filter(user=self.user).first()
        self.assertTrue(session.messages.filter(role='assistant').exists())

    def test_chat_requires_auth(self):
        """Chat should redirect unauthenticated users."""
        self.client.logout()
        response = self.client.get(reverse('chat:chat'))
        self.assertEqual(response.status_code, 302)

    def test_send_empty_message(self):
        """Empty message should return 400."""
        response = self.client.post(
            reverse('chat:send_message'),
            json.dumps({'message': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_send_long_message(self):
        """Message over 2000 chars should return 400."""
        response = self.client.post(
            reverse('chat:send_message'),
            json.dumps({'message': 'x' * 2001}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_new_session(self):
        """Creating new session should deactivate old ones."""
        # Create initial session
        self.client.get(reverse('chat:chat'))
        old_session = ChatSession.objects.filter(user=self.user, is_active=True).first()

        # Create new session
        response = self.client.post(reverse('chat:new_session'), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Old session should be deactivated
        old_session.refresh_from_db()
        self.assertFalse(old_session.is_active)

    def test_chat_history(self):
        """Chat history should return JSON with sessions."""
        ChatSession.objects.create(user=self.user, title='Session 1')
        response = self.client.get(reverse('chat:chat_history'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('sessions', data)

    def test_get_send_not_allowed(self):
        """GET on send endpoint should return 405."""
        response = self.client.get(reverse('chat:send_message'))
        self.assertEqual(response.status_code, 405)


class ChatAIFallbackTest(TestCase):
    """Tests for chat AI fallback logic."""

    def test_fallback_response_not_empty(self):
        """Fallback response should contain helpful text."""
        response = _get_fallback_response('I feel stressed')
        self.assertGreater(len(response), 50)

    def test_fallback_has_actionable_advice(self):
        """Fallback should contain breathing/grounding advice."""
        response = _get_fallback_response('help')
        self.assertTrue(
            'breath' in response.lower() or 'deep' in response.lower()
        )

    def test_system_prompt_includes_student_name(self):
        """System prompt should include the student's name."""
        prompt = get_chat_system_prompt('Anuj', 'JEE', None)
        self.assertIn('Anuj', prompt)

    def test_system_prompt_includes_exam_type(self):
        """System prompt should include the exam type."""
        prompt = get_chat_system_prompt('Test', 'NEET', None)
        self.assertIn('NEET', prompt)

    def test_system_prompt_includes_safety(self):
        """System prompt should include crisis helpline numbers."""
        prompt = get_chat_system_prompt('Test', 'JEE', None)
        self.assertIn('9152987821', prompt)  # iCall number
