from django import forms
from .models import JournalEntry, MoodLog, EMOTION_CHOICES


class JournalEntryForm(forms.ModelForm):
    """Form for creating/editing journal entries."""
    emotions_select = forms.MultipleChoiceField(
        choices=EMOTION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'emotion-checkbox',
        }),
        label="How are you feeling?"
    )

    class Meta:
        model = JournalEntry
        fields = ['content', 'mood_score']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-input journal-textarea',
                'rows': 8,
                'placeholder': 'How was your day? Write about your feelings, study experience, anything on your mind...\n\nTip: The more you write, the better AI insights you\'ll get! 📝',
                'id': 'id_journal_content',
            }),
            'mood_score': forms.HiddenInput(attrs={
                'id': 'id_mood_score',
            }),
        }

    def clean_emotions_select(self):
        return ','.join(self.cleaned_data.get('emotions_select', []))


class MoodLogForm(forms.ModelForm):
    """Quick mood check-in form."""
    class Meta:
        model = MoodLog
        fields = ['mood_score', 'energy_level', 'anxiety_level', 'motivation_level', 'quick_note']
        widgets = {
            'mood_score': forms.HiddenInput(attrs={'id': 'id_quick_mood'}),
            'energy_level': forms.HiddenInput(attrs={'id': 'id_energy'}),
            'anxiety_level': forms.HiddenInput(attrs={'id': 'id_anxiety'}),
            'motivation_level': forms.HiddenInput(attrs={'id': 'id_motivation'}),
            'quick_note': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Quick note (optional)...',
                'maxlength': 280,
                'id': 'id_quick_note',
            }),
        }
