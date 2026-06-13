import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import WellnessAlert, MindfulnessExercise


@login_required
def alerts_view(request):
    """View wellness alerts."""
    alerts = WellnessAlert.objects.filter(user=request.user)
    unread_count = alerts.filter(is_read=False).count()

    context = {
        'alerts': alerts[:20],
        'unread_count': unread_count,
    }
    return render(request, 'wellness/alerts.html', context)


@login_required
def mark_alert_read(request, pk):
    """Mark an alert as read (AJAX)."""
    if request.method == 'POST':
        try:
            alert = WellnessAlert.objects.get(pk=pk, user=request.user)
            alert.is_read = True
            alert.save()
            return JsonResponse({'success': True})
        except WellnessAlert.DoesNotExist:
            return JsonResponse({'error': 'Alert not found'}, status=404)
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def exercises_view(request):
    """View mindfulness exercises library."""
    exercises = MindfulnessExercise.objects.all()
    category = request.GET.get('category')
    if category:
        exercises = exercises.filter(category=category)

    # Group by category
    categories = {}
    for ex in exercises:
        cat = ex.get_category_display()
        if cat not in categories:
            categories[cat] = []
        try:
            steps = json.loads(ex.steps) if ex.steps else []
        except (json.JSONDecodeError, TypeError):
            steps = []
        categories[cat].append({
            'id': ex.id,
            'title': ex.title,
            'emoji': ex.emoji,
            'description': ex.description,
            'duration': ex.duration_minutes,
            'difficulty': ex.difficulty,
            'steps': steps,
        })

    context = {
        'categories': categories,
        'selected_category': category,
    }
    return render(request, 'wellness/exercises.html', context)


@login_required
def resources_view(request):
    """Curated wellness resources."""
    resources = {
        'crisis_helplines': [
            {'name': 'iCall', 'number': '9152987821', 'desc': 'Psychosocial helpline by TISS'},
            {'name': 'Vandrevala Foundation', 'number': '1860-2662-345', 'desc': '24/7 mental health support'},
            {'name': 'NIMHANS', 'number': '080-46110007', 'desc': 'National mental health helpline'},
            {'name': 'AASRA', 'number': '9820466726', 'desc': 'Crisis intervention & suicide prevention'},
        ],
        'study_techniques': [
            {'name': 'Pomodoro Technique', 'emoji': '🍅', 'desc': '25 min focus + 5 min break'},
            {'name': 'Active Recall', 'emoji': '🧠', 'desc': 'Test yourself instead of re-reading'},
            {'name': 'Spaced Repetition', 'emoji': '📅', 'desc': 'Review at increasing intervals'},
            {'name': 'Feynman Technique', 'emoji': '🎓', 'desc': 'Explain concepts in simple words'},
        ],
    }
    return render(request, 'wellness/resources.html', {'resources': resources})
