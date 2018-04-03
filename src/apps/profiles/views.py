from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

from .forms import SignUpForm


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('pages:home')

    form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def user_profile(request):
    return render(request, 'pages/user_profile.html')
