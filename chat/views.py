import json
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

logger = logging.getLogger(__name__)

from .models import ChatSession, ChatMessage
from .ai_chat import send_chat_message, get_quick_action_prompt
from journal.models import MoodLog, StressTrigger


@login_required
def chat_view(request):
    """Main chat interface."""
    user = request.user
    profile = user.profile

    # Get or create active session
    session = ChatSession.objects.filter(user=user, is_active=True).first()
    if not session:
        session = ChatSession.objects.create(
            user=user,
            title=f"Chat with MindEase Buddy",
            session_type='general'
        )

    messages_list = session.messages.all()

    # If new session, add welcome message
    if not messages_list.exists():
        welcome_msg = (
            f"Hey {user.first_name or 'there'}! 👋 I'm your MindEase Buddy — "
            f"think of me as a supportive friend who gets the exam pressure.\n\n"
            f"I see you're preparing for **{profile.get_exam_type_display()}** — "
            f"that's a big deal, and I'm here to help you through it! 💪\n\n"
            f"You can:\n"
            f"• Tell me how you're feeling\n"
            f"• Ask for study tips or motivation\n"
            f"• Request a quick breathing exercise\n"
            f"• Just vent — I'm all ears! 👂\n\n"
            f"What's on your mind today?"
        )
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=welcome_msg
        )
        messages_list = session.messages.all()

    context = {
        'session': session,
        'messages': messages_list,
        'profile': profile,
    }
    return render(request, 'chat/chat.html', context)


@login_required
def send_message(request):
    """AJAX endpoint to send a message and get AI response."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        quick_action = data.get('quick_action')

        if not user_message and not quick_action:
            return JsonResponse({'error': 'Message is required'}, status=400)

        # Validate message length
        if len(user_message) > 2000:
            return JsonResponse({'error': 'Message too long (max 2000 characters)'}, status=400)

        user = request.user
        profile = user.profile

        # Get active session
        session = ChatSession.objects.filter(user=user, is_active=True).first()
        if not session:
            session = ChatSession.objects.create(user=user, title="Chat Session")

        # Handle quick actions
        if quick_action:
            user_message = {
                'breathing': "I need a breathing exercise to calm down",
                'motivation': "I need some motivation right now",
                'study_tip': "Can you share a study tip?",
                'grounding': "I'm feeling anxious, help me ground myself",
                'break_ideas': "What should I do for a study break?",
            }.get(quick_action, user_message)

        # Save user message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=user_message
        )

        # Get context for AI
        recent_mood = MoodLog.objects.filter(user=user).first()
        mood_context = f"{recent_mood.mood_score}/10" if recent_mood else None

        triggers = StressTrigger.objects.filter(
            entry__user=user
        ).values_list('trigger_detail', flat=True)[:5]
        trigger_context = ', '.join(triggers) if triggers else None

        # Get AI response
        result = send_chat_message(
            session=session,
            user_message=user_message,
            student_name=user.first_name or user.username,
            exam_type=profile.get_exam_type_display(),
            exam_date=str(profile.exam_date) if profile.exam_date else None,
            recent_mood=mood_context,
            triggers=trigger_context
        )

        ai_response = result.get('response', 'Sorry, I had trouble responding. Please try again!')

        # Save AI response
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response
        )

        return JsonResponse({
            'success': True,
            'response': ai_response,
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request format'}, status=400)
    except Exception as e:
        logger.error(f'Chat error for user {request.user.username}: {e}')
        return JsonResponse({
            'success': False,
            'response': 'Sorry, something went wrong. Please try again! 💙',
        }, status=500)


@login_required
def new_session(request):
    """Start a new chat session."""
    # Deactivate current sessions
    ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)

    # Create new session
    session = ChatSession.objects.create(
        user=request.user,
        title="New Chat Session"
    )

    return JsonResponse({'success': True, 'session_id': session.id})


@login_required
def chat_history(request):
    """Get chat history for sidebar."""
    sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')[:20]
    data = [{
        'id': s.id,
        'title': s.title,
        'date': s.started_at.strftime('%b %d, %Y'),
        'messages': s.message_count,
        'is_active': s.is_active,
    } for s in sessions]
    return JsonResponse({'sessions': data})
