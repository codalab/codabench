# from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
# from django.shortcuts import render


def sign_up(request):
    return HttpResponse("Not implemented yet!")

    # if request.method == 'POST':
    #     form = UserCreationForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         return HttpResponse("User created successfully!")
    # else:
    #     form = UserCreationForm()
    #     return render(request, 'registration/signup.html', {'form': form})
