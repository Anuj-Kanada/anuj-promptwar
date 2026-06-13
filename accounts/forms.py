from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import StudentProfile, EXAM_CHOICES


class StudentRegistrationForm(UserCreationForm):
    """Registration form with exam details."""
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your first name',
            'class': 'form-input',
            'id': 'id_first_name',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'your@email.com',
            'class': 'form-input',
            'id': 'id_email',
        })
    )
    exam_type = forms.ChoiceField(
        choices=EXAM_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_exam_type',
        })
    )
    exam_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input',
            'id': 'id_exam_date',
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Choose a username',
                'class': 'form-input',
                'id': 'id_username',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Create a password',
            'class': 'form-input',
            'id': 'id_password1',
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm password',
            'class': 'form-input',
            'id': 'id_password2',
        })


class StudentProfileForm(forms.ModelForm):
    """Profile edit form."""
    class Meta:
        model = StudentProfile
        fields = ['exam_type', 'exam_date', 'daily_study_hours', 'goals', 'avatar_emoji']
        widgets = {
            'exam_type': forms.Select(attrs={'class': 'form-input', 'id': 'id_exam_type'}),
            'exam_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'id': 'id_exam_date'}),
            'daily_study_hours': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 18, 'id': 'id_study_hours'}),
            'goals': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'What are your goals?', 'id': 'id_goals'}),
            'avatar_emoji': forms.TextInput(attrs={'class': 'form-input', 'id': 'id_avatar_emoji'}),
        }
