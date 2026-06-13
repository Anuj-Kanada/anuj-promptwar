import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import JournalEntry, MoodLog, StressTrigger
from .forms import JournalEntryForm, MoodLogForm
from .ai_service import analyze_journal_entry


@login_required
def dashboard(request):
    """Main dashboard with mood chart, recent entries, and quick actions."""
    user = request.user
    profile = user.profile

    # Recent journal entries
    recent_entries = JournalEntry.objects.filter(user=user)[:5]

    # Recent mood logs (last 14 days)
    two_weeks_ago = timezone.now() - timedelta(days=14)
    mood_logs = MoodLog.objects.filter(user=user, logged_at__gte=two_weeks_ago).order_by('logged_at')

    # Mood chart data
    mood_data = list(mood_logs.values_list('mood_score', flat=True))
    mood_dates = [log.logged_at.strftime('%b %d') for log in mood_logs]

    # Also include mood from journal entries
    journal_moods = JournalEntry.objects.filter(
        user=user, created_at__gte=two_weeks_ago
    ).order_by('created_at')
    for entry in journal_moods:
        if entry.created_at.strftime('%b %d') not in mood_dates:
            mood_dates.append(entry.created_at.strftime('%b %d'))
            mood_data.append(entry.mood_score)

    # Stats
    total_entries = JournalEntry.objects.filter(user=user).count()
    avg_mood = None
    if mood_data:
        avg_mood = round(sum(mood_data) / len(mood_data), 1)

    # Latest AI insights
    latest_analyzed = JournalEntry.objects.filter(user=user, is_analyzed=True).first()

    # Streak calculation (max 365 to prevent infinite loops)
    today = timezone.now().date()
    streak = 0
    check_date = today
    for _ in range(365):
        has_entry = JournalEntry.objects.filter(
            user=user,
            created_at__date=check_date
        ).exists()
        if has_entry:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    context = {
        'profile': profile,
        'recent_entries': recent_entries,
        'mood_data': json.dumps(mood_data),
        'mood_dates': json.dumps(mood_dates),
        'total_entries': total_entries,
        'avg_mood': avg_mood,
        'streak': streak,
        'latest_analyzed': latest_analyzed,
        'mood_form': MoodLogForm(),
    }
    return render(request, 'journal/dashboard.html', context)


@login_required
def new_entry(request):
    """Create a new journal entry with AI analysis."""
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.emotions = form.clean_emotions_select()

            # Set mood label
            mood_labels = {1: 'Terrible', 2: 'Bad', 3: 'Not Great', 4: 'Okay', 5: 'Decent',
                          6: 'Good', 7: 'Great', 8: 'Amazing', 9: 'Fantastic', 10: 'On Fire'}
            entry.mood_label = mood_labels.get(entry.mood_score, 'Okay')
            entry.save()

            # Run AI analysis
            profile = request.user.profile
            recent_moods = list(
                MoodLog.objects.filter(user=request.user)
                .order_by('-logged_at')[:7]
                .values('mood_score', 'logged_at')
            )
            recent_mood_data = [
                {'date': m['logged_at'].strftime('%b %d'), 'score': m['mood_score']}
                for m in recent_moods
            ]

            result = analyze_journal_entry(
                entry_content=entry.content,
                exam_type=profile.get_exam_type_display(),
                exam_date=str(profile.exam_date) if profile.exam_date else None,
                recent_moods=recent_mood_data
            )

            if result.get('success') or result.get('data'):
                data = result['data']
                entry.ai_summary = data.get('emotional_summary', '')
                entry.dominant_emotion = data.get('dominant_emotion', '')
                entry.sentiment_score = data.get('sentiment_score')
                entry.burnout_risk = data.get('burnout_risk_score')
                entry.encouragement = data.get('encouragement_message', '')
                entry.coping_suggestions = json.dumps(data.get('coping_suggestions', []))
                entry.ai_insights = json.dumps(data.get('hidden_triggers', []))
                entry.is_analyzed = True
                entry.save()

                # Create StressTrigger objects
                for trigger in data.get('hidden_triggers', []):
                    if isinstance(trigger, dict):
                        StressTrigger.objects.create(
                            entry=entry,
                            trigger_type=trigger.get('type', 'other'),
                            trigger_detail=trigger.get('detail', ''),
                            severity=trigger.get('severity', 5)
                        )

            # Also create a MoodLog from this entry
            MoodLog.objects.create(
                user=request.user,
                mood_score=entry.mood_score,
                energy_level=5,
                anxiety_level=5,
                motivation_level=5,
            )

            messages.success(request, 'Journal entry saved! AI insights are ready. ✨')
            return redirect('journal:entry_detail', pk=entry.pk)
    else:
        form = JournalEntryForm()

    return render(request, 'journal/new_entry.html', {'form': form})


@login_required
def entry_detail(request, pk):
    """View a journal entry with AI analysis."""
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)

    # Parse JSON fields for template
    coping = []
    if entry.coping_suggestions:
        try:
            coping = json.loads(entry.coping_suggestions)
        except json.JSONDecodeError:
            coping = [entry.coping_suggestions]

    triggers = entry.stress_triggers.all()

    context = {
        'entry': entry,
        'coping_suggestions': coping,
        'triggers': triggers,
    }
    return render(request, 'journal/entry_detail.html', context)


@login_required
def history(request):
    """View all past journal entries with filters."""
    entries = JournalEntry.objects.filter(user=request.user)

    # Filter by date range
    date_filter = request.GET.get('days', '30')
    if date_filter.isdigit():
        days = int(date_filter)
        start_date = timezone.now() - timedelta(days=days)
        entries = entries.filter(created_at__gte=start_date)

    context = {
        'entries': entries,
        'date_filter': date_filter,
    }
    return render(request, 'journal/history.html', context)


@login_required
def quick_mood_log(request):
    """AJAX endpoint for quick mood logging."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mood_score = max(1, min(10, int(data.get('mood_score', 5))))
            energy_level = max(1, min(10, int(data.get('energy_level', 5))))
            anxiety_level = max(1, min(10, int(data.get('anxiety_level', 5))))
            motivation_level = max(1, min(10, int(data.get('motivation_level', 5))))
            mood_log = MoodLog.objects.create(
                user=request.user,
                mood_score=mood_score,
                energy_level=energy_level,
                anxiety_level=anxiety_level,
                motivation_level=motivation_level,
                quick_note=str(data.get('quick_note', ''))[:280]
            )
            return JsonResponse({
                'success': True,
                'message': 'Mood logged! 🎯',
                'mood_score': mood_log.mood_score,
            })
        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({'success': False, 'error': 'Invalid data format'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Failed to save mood log'}, status=500)
    return JsonResponse({'error': 'POST required'}, status=405)
