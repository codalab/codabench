import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignUpForm(UserCreationForm):

    email = forms.EmailField(
        max_length=254, help_text="Required. Inform a valid email address."
    )

    def clean_username(self):
        data = self.cleaned_data["username"]

        # Check if username has allowed characters only
        # Allow only lowercase letters, numbers, hyphens, and underscores
        if not re.match(r"^[a-z0-9_-]+$", data):
            raise forms.ValidationError("Username can only contain lowercase letters, numbers, hyphens, and underscores.")

        # Check username length
        if (len(data) > 15) or (len(data) < 5):
            raise forms.ValidationError(
                "Username must have at least 5 characters and at most 15 characters"
            )
        return data

    def clean_email(self):
        email = self.cleaned_data["email"]
        if "*" in email:
            raise forms.ValidationError("Email address cannot contain the '*' character.")
        return email

    class Meta:

        model = User
        fields = ("username", "email", "password1", "password2")


class LoginForm(forms.Form):

    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=150, widget=forms.PasswordInput)


class ActivationForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True)
