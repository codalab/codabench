# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
# from django.shortcuts import render
from django.shortcuts import render, redirect

from .forms import SignUpForm


def sign_up(request):
    # return HttpResponse("Not implemented yet!")

    # if request.method == 'POST':
    #     form = UserCreationForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         return HttpResponse("User created successfully!")
    # else:
    #     form = UserCreationForm()
    #     return render(request, 'registration/signup.html', {'form': form})

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
