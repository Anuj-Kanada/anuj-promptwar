import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta

from journal.models import JournalEntry, MoodLog, StressTrigger
from .models import WeeklyReport


def _safe_days(request, default=30):
    """Safely parse 'days' query param with bounds."""
    try:
        return max(1, min(365, int(request.GET.get('days', default))))
    except (ValueError, TypeError):
        return default


@login_required
def insights_view(request):
    """Weekly AI-generated insights."""
    user = request.user
    reports = WeeklyReport.objects.filter(user=user)[:8]

    # Latest report
    latest = reports.first() if reports else None

    context = {
        'reports': reports,
        'latest': latest,
    }
    return render(request, 'analytics/insights.html', context)


@login_required
def trends_view(request):
    """Mood and stress trend visualizations."""
    user = request.user
    days = _safe_days(request)
    start_date = timezone.now() - timedelta(days=days)

    # Mood trend data
    mood_logs = MoodLog.objects.filter(
        user=user, logged_at__gte=start_date
    ).order_by('logged_at')

    mood_data = {
        'dates': [m.logged_at.strftime('%b %d') for m in mood_logs],
        'moods': [m.mood_score for m in mood_logs],
        'energy': [m.energy_level for m in mood_logs],
        'anxiety': [m.anxiety_level for m in mood_logs],
        'motivation': [m.motivation_level for m in mood_logs],
    }

    # Emotion distribution
    entries = JournalEntry.objects.filter(
        user=user, created_at__gte=start_date, is_analyzed=True
    )
    emotion_counts = {}
    for entry in entries:
        if entry.dominant_emotion:
            emotion = entry.dominant_emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

    # Stress trigger distribution
    triggers = StressTrigger.objects.filter(
        entry__user=user, identified_at__gte=start_date
    ).values('trigger_type').annotate(count=Count('id')).order_by('-count')

    trigger_data = {
        'labels': [t['trigger_type'].replace('_', ' ').title() for t in triggers],
        'counts': [t['count'] for t in triggers],
    }

    # Burnout risk trend
    burnout_data = {
        'dates': [e.created_at.strftime('%b %d') for e in entries if e.burnout_risk is not None],
        'scores': [round(e.burnout_risk * 100) for e in entries if e.burnout_risk is not None],
    }

    # Stats
    stats = {
        'avg_mood': round(mood_logs.aggregate(avg=Avg('mood_score'))['avg'] or 0, 1),
        'avg_anxiety': round(mood_logs.aggregate(avg=Avg('anxiety_level'))['avg'] or 0, 1),
        'total_entries': entries.count(),
        'total_moods': mood_logs.count(),
    }

    context = {
        'mood_data': json.dumps(mood_data),
        'emotion_counts': json.dumps(emotion_counts),
        'trigger_data': json.dumps(trigger_data),
        'burnout_data': json.dumps(burnout_data),
        'stats': stats,
        'days': days,
    }
    return render(request, 'analytics/trends.html', context)


@login_required
def trend_data_api(request):
    """AJAX endpoint for chart data."""
    user = request.user
    days = _safe_days(request)
    start_date = timezone.now() - timedelta(days=days)

    mood_logs = MoodLog.objects.filter(
        user=user, logged_at__gte=start_date
    ).order_by('logged_at')

    data = {
        'dates': [m.logged_at.strftime('%Y-%m-%d') for m in mood_logs],
        'moods': [m.mood_score for m in mood_logs],
        'energy': [m.energy_level for m in mood_logs],
        'anxiety': [m.anxiety_level for m in mood_logs],
    }
    return JsonResponse(data)
