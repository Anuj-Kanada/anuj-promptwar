from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import StudentRegistrationForm, StudentProfileForm


def register_view(request):
    """Student registration with exam details."""
    if request.user.is_authenticated:
        return redirect('journal:dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.save()
            # Update profile with exam details (signal creates profile)
            try:
                profile = user.profile
            except Exception:
                from .models import StudentProfile
                profile = StudentProfile.objects.create(user=user)
            profile.exam_type = form.cleaned_data['exam_type']
            profile.exam_date = form.cleaned_data.get('exam_date')
            profile.save()
            # Auto-login after registration
            login(request, user)
            messages.success(request, f'Welcome to MindEase, {user.first_name}! 🎉')
            return redirect('journal:dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login."""
    if request.user.is_authenticated:
        return redirect('journal:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Prevent open redirect attacks — validate next URL
                next_url = request.GET.get('next', '')
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('journal:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    """User logout — accepts both GET and POST for convenience."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'You have been logged out. Take care! 💙')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """View and edit profile."""
    profile = request.user.profile
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated! ✨')
            return redirect('accounts:profile')
    else:
        form = StudentProfileForm(instance=profile)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
    })
