from .forms import SignUpForm
from django.http import HttpResponse
from django.shortcuts import render


def sign_up(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("User created successfully!")
        elif not form.is_valid():
            return render(request, 'registration/signup.html', {'form': form})
        else:
            return HttpResponse("There was an issue. Please contact us on Github!")
    return render(request, 'registration/signup.html', {'form': form})
