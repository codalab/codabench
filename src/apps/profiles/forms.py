import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .usernames import is_its_own_slug, is_taken


class SignUpForm(UserCreationForm):

    email = forms.EmailField(
        max_length=200, help_text="Required. Inform a valid email address."
    )

    def clean_username(self):
        data = self.cleaned_data["username"]

        # Check if username has allowed characters only
        # Allow only lowercase letters, numbers, hyphens, and underscores
        if not re.match(r"^[a-z0-9_-]+$", data):
            raise forms.ValidationError("Username can only contain lowercase letters, numbers, hyphens, and underscores.")

        # Check username length
        if (len(data) > 50) or (len(data) < 5):
            raise forms.ValidationError(
                "Username must have at least 5 characters and at most 50 characters"
            )

        # Check that the username is its own slug. Why: see profiles/usernames.py
        # With the characters above, slugify only changes '-' or '_' at the start or the end, and '--'.
        if not is_its_own_slug(data):
            raise forms.ValidationError(
                "Username must start and end with a letter or a number, and cannot contain two hyphens in a row."
            )

        # Check that no user has this username or this slug.
        # Why here: the model checks the username, but not the slug, so a slug already used made the save fail.
        if is_taken(data):
            raise forms.ValidationError("A user with that username already exists.")
        return data

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if "*" in email:
            raise forms.ValidationError("Email address cannot contain the '*' character.")
        # Emails are stored in lowercase, so check for an existing account case-insensitively
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    class Meta:

        model = User
        fields = ("username", "email", "password1", "password2")


class LoginForm(forms.Form):

    username = forms.CharField(max_length=50)
    password = forms.CharField(max_length=150, widget=forms.PasswordInput)


class ActivationForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True)
