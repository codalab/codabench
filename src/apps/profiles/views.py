from django.conf import settings
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views

from .forms import SignUpForm


class LoginView(auth_views.LoginView):
    def get_context_data(self, *args, **kwargs):
        context = super(LoginView, self).get_context_data(*args, **kwargs)
        # "http://localhost:8888/profiles/signup?next=http://localhost/social/login/chahub"
        context['chahub_signup_url'] = "{}/profiles/signup?next={}/social/login/chahub".format(settings.SOCIAL_AUTH_CHAHUB_BASE_URL, settings.SITE_DOMAIN)
        return context


class LogoutView(auth_views.LogoutView):
    pass


def sign_up(request):
    context = {}
    context['chahub_signup_url'] = "{}/profiles/signup?next={}/social/login/chahub".format(
        settings.SOCIAL_AUTH_CHAHUB_BASE_URL,
        settings.SITE_DOMAIN
    )
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('pages:home')
        else:
            context['form'] = form

    if not context.get('form'):
        context['form'] = SignUpForm()
    return render(request, 'registration/signup.html', context)


def user_profile(request):
    return render(request, 'pages/user_profile.html')
