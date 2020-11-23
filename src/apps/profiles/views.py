import json

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from api.serializers.profiles import UserSerializer
from .forms import SignUpForm
from .models import User


class LoginView(auth_views.LoginView):
    def get_context_data(self, *args, **kwargs):
        context = super(LoginView, self).get_context_data(*args, **kwargs)
        # "http://localhost:8888/profiles/signup?next=http://localhost/social/login/chahub"
        context['chahub_signup_url'] = "{}/profiles/signup?next={}/social/login/chahub".format(settings.SOCIAL_AUTH_CHAHUB_BASE_URL, settings.SITE_DOMAIN)
        return context


class LogoutView(auth_views.LogoutView):
    pass


class UserEditView(LoginRequiredMixin, DetailView):
    queryset = User.objects.all()
    template_name = 'profiles/user_edit.html'
    slug_url_kwarg = 'username'
    query_pk_and_slug = True

    def get_object(self, *args, **kwargs):
        user = super().get_object(*args, **kwargs)
        authorized = self.request.user.is_superuser or self.request.user == user
        if authorized:
            return user
        raise Http404()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['serialized_user'] = json.dumps(UserSerializer(self.get_object()).data)
        return context


class UserDetailView(LoginRequiredMixin, DetailView):
    queryset = User.objects.all()
    template_name = 'profiles/user_profile.html'
    slug_url_kwarg = 'username'
    query_pk_and_slug = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['serialized_user'] = json.dumps(UserSerializer(self.get_object()).data)
        return context


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
