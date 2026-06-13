"""
Gemini AI Chat Service for MindEase Buddy
Provides empathetic, conversational wellness support for exam students.
Uses the new google.genai SDK.
"""

import logging
from django.conf import settings

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def get_chat_system_prompt(student_name, exam_type, exam_date, recent_mood=None, triggers=None):
    """Build the system prompt for the AI chat companion."""
    return f"""You are "MindEase Buddy" — an empathetic, always-available digital companion for students preparing for competitive exams in India.

PERSONALITY:
- Warm, understanding, non-judgmental, and supportive
- Like a caring older sibling who's been through exam pressure
- Uses age-appropriate language, occasional humor, and emojis
- Speaks in a mix of English (with occasional Hindi words like "yaar", "boss", "champ" for warmth)
- Never dismissive of feelings, always validates first

STUDENT CONTEXT:
- Name: {student_name}
- Preparing for: {exam_type}
- Exam Date: {exam_date or 'Not set yet'}
- Recent Mood: {recent_mood or 'No data yet'}
- Known Stress Triggers: {triggers or 'None identified yet'}

YOUR CAPABILITIES:
1. Provide real-time coping strategies for stress, anxiety, and overwhelm
2. Guide through quick mindfulness exercises (breathing, grounding, body scan)
3. Offer motivational encouragement and perspective
4. Help reframe negative thoughts using CBT-lite techniques
5. Suggest effective study breaks and relaxation activities
6. Share study tips and time management strategies relevant to {exam_type}
7. Help with exam anxiety and performance pressure

SAFETY GUIDELINES (STRICTLY FOLLOW):
- NEVER provide medical advice or diagnose mental health conditions
- NEVER act as a replacement for professional therapy
- If the student expresses severe distress, self-harm ideation, suicidal thoughts, or any crisis:
  * Acknowledge their pain with deep empathy
  * ALWAYS provide these helpline numbers:
    - iCall: 9152987821
    - Vandrevala Foundation: 1860-2662-345 / 1800-2333-330
    - NIMHANS: 080-46110007
    - AASRA: 9820466726
  * Encourage them to talk to a trusted adult (parent, teacher, counselor)
  * Do NOT attempt to counsel them on severe issues yourself

RESPONSE STYLE:
- Keep responses concise (2-4 paragraphs max)
- Use bullet points for actionable advice
- Include relevant emojis for warmth
- End with a supportive question or check-in when appropriate
- If they ask for an exercise, provide step-by-step instructions
"""


def send_chat_message(session, user_message, student_name, exam_type, exam_date,
                      recent_mood=None, triggers=None):
    """
    Send a message to the AI chat companion and get a response.
    """
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        system_prompt = get_chat_system_prompt(
            student_name, exam_type, exam_date, recent_mood, triggers
        )

        # Build conversation history (limit to last 20 messages to prevent token overflow)
        contents = []
        messages = session.messages.order_by('sent_at')
        recent_messages = list(messages)[-20:]
        
        for msg in recent_messages:
            role = 'user' if msg.role == 'user' else 'model'
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)]
                )
            )

        # Add the current user message
        contents.append(
            types.Content(
                role='user',
                parts=[types.Part.from_text(text=user_message)]
            )
        )

        # Generate response with system instruction
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.8,
                max_output_tokens=1024,
            )
        )

        return {
            'success': True,
            'response': response.text
        }

    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return {
            'success': False,
            'response': _get_fallback_response(user_message),
            'error': str(e)
        }


def get_quick_action_prompt(action_type, student_name, exam_type):
    """Generate prompts for quick action buttons."""
    prompts = {
        'breathing': f"Guide {student_name} through a quick 4-7-8 breathing exercise to calm exam anxiety. Make it engaging and easy to follow step by step.",
        'motivation': f"Give {student_name} a powerful, personalized motivational boost for their {exam_type} preparation. Reference specific challenges of {exam_type} prep. Make it genuine, not generic.",
        'study_tip': f"Share one practical, science-backed study technique that would help {student_name} with {exam_type} preparation. Be specific and actionable.",
        'grounding': f"Guide {student_name} through a quick 5-4-3-2-1 grounding exercise to help with exam anxiety. Make it calming and present-focused.",
        'break_ideas': f"Suggest 3 creative, refreshing study break activities for {student_name} who is preparing for {exam_type}. Make them fun and rejuvenating.",
    }
    return prompts.get(action_type, prompts['motivation'])


def _get_fallback_response(user_message):
    """Provide a fallback response when the API is unavailable."""
    return (
        "I'm having a little trouble connecting right now, but I'm still here for you! 💙\n\n"
        "While I reconnect, here are some quick things you can try:\n"
        "• Take 3 deep breaths — in for 4 counts, hold for 4, out for 4\n"
        "• Look around and name 5 things you can see\n"
        "• Stretch your arms above your head and hold for 10 seconds\n\n"
        "Try sending your message again in a moment — I want to hear what's on your mind! 🤗"
    )
