# from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm
from django.http import HttpResponse
from django.shortcuts import render


def sign_up(request):
    # return HttpResponse("Not implemented yet!")
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("User created successfully!")
    # form at this point contains errors that we want
    return render(request, 'registration/signup.html', {'form': form})
