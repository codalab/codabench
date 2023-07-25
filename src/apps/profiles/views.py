import json
import django

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.views.generic import DetailView, TemplateView

from api.serializers.profiles import UserSerializer, OrganizationDetailSerializer, OrganizationEditSerializer, \
    UserNotificationSerializer
from .forms import SignUpForm, LoginForm
from .models import User, Organization, Membership
from .tokens import account_activation_token


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


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        user = None
        messages.error(request, f"User not found. Please sign up again.")
        return redirect('accounts:signup')
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, f'Your account is fully setup! Please login.')
        return redirect('accounts:login')
    else:
        messages.error(request, f"Activation link is invalid. Please double check your link.")
        return redirect('accounts:signup')
    return redirect('pages:home')


def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account.'
    message = render_to_string('profiles/emails/template_activate_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f'Dear {user.username}, please go to you email {to_email} inbox and click on \
            received activation link to confirm and complete the registration. *Note: Check your spam folder.')
    else:
        messages.error(request, f'Problem sending confirmation email to {to_email}, check if you typed it correctly.')


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
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect('pages:home')
        else:
            context['form'] = form

    if not context.get('form'):
        context['form'] = SignUpForm()
    return render(request, 'registration/signup.html', context)


def log_in(request):

    # Fectch next redirect page after login
    # default : None
    next = request.GET.get('next', None)

    context = {}
    context['chahub_signup_url'] = "{}/profiles/signup?next={}/social/login/chahub".format(
        settings.SOCIAL_AUTH_CHAHUB_BASE_URL,
        settings.SITE_DOMAIN
    )
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)

                # if next is none redirect to home
                # otherwise redirect to requested page
                if next is None:
                    return redirect('pages:home')
                else:
                    return redirect(next)
            else:
                messages.error(request, "Wrong Credentials!")
        else:
            context['form'] = form

    if not context.get('form'):
        context['form'] = LoginForm()
    return render(request, 'registration/login.html', context)


# Password Reset views/forms below
# auth_forms
class CustomPasswordResetForm(auth_forms.PasswordResetForm):
    """
        Subclassed auth_forms.PasswordResetForm in order to add a print statement
        to see the email in the logs.
        Source: https://github.com/django/django/blob/8b1ff0da4b162e87edebd94e61f2cd153e9e159d/django/contrib/auth/forms.py#L287
    """
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        print(email_message.message())
        if html_email_template_name is not None:
            html_email = render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        email_message.send()


# auth_views
# https://devdocs.io/django~2.2/topics/auth/default#django.contrib.auth.views.PasswordChangeView # Search for PasswordResetView
class CustomPasswordResetView(auth_views.PasswordResetView):
    """
    1. form_class: subclassing auth_views.PasswordResetView to use a custom form "CustomPasswordResetForm" above
    2. success_url: Our src/apps/profiles/urls_accounts.py has become an "app" with the use of "app_name".
       We have to use app:view_name syntax in templates like " {% url 'accounts:password_reset_confirm'%} "
       Therefore we need to tell this view to find the right success_url with that syntax or django won't be
       able to find the view.
    3. from_email: We want to set the from_email to info@codalab.org - may eventually put in .env file.
    #  The other commented sections are the defaults for other attributes in auth_views.PasswordResetView.
       They are in here in case someone wants to customize in the future. All attributes show up in the order
       shown in the docs.
    """
    # template_name = 'registration/password_reset_form.html'
    form_class = CustomPasswordResetForm  # auth_forms.PasswordResetForm
    # email_template_name = ''  # Defaults to registration/password_reset_email.html if not supplied.
    # subject_template_name = ''  # Defaults to registration/password_reset_subject.txt if not supplied.
    # token_generator = ''  # This will default to default_token_generator, it’s an instance of django.contrib.auth.tokens.PasswordResetTokenGenerator.
    success_url = django.urls.reverse_lazy("accounts:password_reset_done")
    from_email = "info@codalab.org"


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    1. success_url: Our src/apps/profiles/urls_accounts.py has become an "app" with the use of "app_name".
       We have to use app:view_name syntax in templates like " {% url 'accounts:password_reset_confirm'%} "
       Therefore we need to tell this view to find the right success_url with that syntax or django won't be
       able to find the view.
    """
    # template_name = '' # Default value is registration/password_reset_confirm.html.
    # form_class = '' # Defaults to django.contrib.auth.forms.SetPasswordForm.
    # token_generator = '' # This will default to default_token_generator, it’s an instance of django.contrib.auth.tokens.PasswordResetTokenGenerator.
    # post_reset_login = '' # Defaults to False.
    success_url = django.urls.reverse_lazy("accounts:password_reset_complete")


class UserNotificationEdit(LoginRequiredMixin, DetailView):
    queryset = User.objects.all()
    template_name = 'profiles/user_notifications.html'
    slug_url_kwarg = 'username'
    query_pk_and_slug = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notifications'] = json.dumps(UserNotificationSerializer(self.get_object()).data)
        return context


class OrganizationCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'profiles/organization_create.html'


class OrganizationDetailView(LoginRequiredMixin, DetailView):
    queryset = Organization.objects.all()

    def get_context_data(self, **kwargs):
        context = {}
        if self.object:
            context['organization'] = OrganizationDetailSerializer(self.object).data
        membership = self.object.membership_set.filter(user=self.request.user)
        if len(membership) == 1:
            context['is_editor'] = membership.first().group in Membership.EDITORS_GROUP
        else:
            context['is_editor'] = False
        return context


class OrganizationEditView(LoginRequiredMixin, DetailView):
    queryset = Organization.objects.all()
    template_name = 'profiles/organization_edit.html'

    def get_object(self, *args, **kwargs):
        organization = super().get_object(*args, **kwargs)
        member = organization.membership_set.filter(user=self.request.user)
        if len(member) == 0 or member.first().group not in Membership.EDITORS_GROUP:
            raise Http404()
        return organization

    def get_context_data(self, **kwargs):
        context = {}
        if self.object:
            context['organization'] = json.dumps(OrganizationEditSerializer(self.object).data)
        return context


class OrganizationInviteView(LoginRequiredMixin, TemplateView):
    template_name = 'profiles/organization_invite.html'
