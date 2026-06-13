"""
Gemini AI Service for Journal Analysis
Analyzes journal entries to extract emotional patterns, stress triggers,
burnout risk, and personalized coping strategies.
Uses the new google.genai SDK.
"""

import json
import logging
from django.conf import settings

from google import genai

logger = logging.getLogger(__name__)


def get_gemini_client():
    """Initialize and return the Gemini client."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def analyze_journal_entry(entry_content, exam_type, exam_date, recent_moods=None):
    """
    Analyze a journal entry using Gemini AI.
    
    Returns a dict with:
    - emotional_summary, dominant_emotion, sentiment_score
    - hidden_triggers, burnout_risk_score
    - coping_suggestions, encouragement_message
    """
    mood_context = "No recent mood data available."
    if recent_moods:
        mood_context = ", ".join([f"{m['date']}: {m['score']}/10" for m in recent_moods[-7:]])

    prompt = f"""You are an empathetic, expert adolescent psychologist specializing in academic stress and student mental health during exam preparation.

A student preparing for {exam_type} (exam date: {exam_date or 'not set'}) has written this journal entry:

---
{entry_content}
---

Their recent mood scores (last 7 days): {mood_context}

Analyze this entry deeply and provide:
1. **Emotional Summary** — Key emotions detected (go beyond surface level, detect subtle emotional undertones)
2. **Dominant Emotion** — The single most prominent emotion (one word)
3. **Sentiment Score** — Overall emotional valence from 0.0 (very negative) to 1.0 (very positive)
4. **Hidden Stress Triggers** — Underlying stressors the student may not be consciously aware of. List as array of objects with "type" (academic/social/family/health/sleep/comparison/time/self_doubt/perfectionism/other), "detail" (brief description), "severity" (1-10)
5. **Burnout Risk Score** — From 0.0 (no risk) to 1.0 (critical burnout) based on language patterns, exhaustion indicators, and emotional fatigue
6. **Coping Suggestions** — 3 specific, actionable strategies tailored to their situation and exam type
7. **Encouragement Message** — A warm, genuine message (2-3 sentences) that acknowledges their struggle and motivates them. Be specific to what they wrote, not generic.

IMPORTANT: Respond ONLY with valid JSON in this exact format, no markdown formatting:
{{
  "emotional_summary": "...",
  "dominant_emotion": "...",
  "sentiment_score": 0.5,
  "hidden_triggers": [{{"type": "...", "detail": "...", "severity": 5}}],
  "burnout_risk_score": 0.3,
  "coping_suggestions": ["...", "...", "..."],
  "encouragement_message": "..."
}}"""

    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        
        # Parse the response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        return {
            'success': True,
            'data': result
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response: {e}")
        return {
            'success': False,
            'error': 'AI analysis returned invalid format. Please try again.',
            'data': _get_fallback_analysis()
        }
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': _get_fallback_analysis()
        }


def _get_fallback_analysis():
    """Return a fallback analysis when API fails."""
    return {
        'emotional_summary': 'Unable to analyze at this time. Your feelings are valid and important.',
        'dominant_emotion': 'unknown',
        'sentiment_score': 0.5,
        'hidden_triggers': [],
        'burnout_risk_score': 0.0,
        'coping_suggestions': [
            'Take a 5-minute break and do some deep breathing',
            'Write down 3 things you\'re grateful for today',
            'Reach out to a friend or family member for support'
        ],
        'encouragement_message': 'Remember, you\'re doing your best, and that\'s enough. Every step forward counts, even the small ones. 💪'
    }
