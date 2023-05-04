from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignUpForm(UserCreationForm):

    email = forms.EmailField(
        max_length=254, help_text="Required. Inform a valid email address."
    )

    def clean_username(self):
        data = self.cleaned_data["username"]
        if not data.islower():
            raise forms.ValidationError("Usernames should be in lowercase")
        if not data.isalnum():
            raise forms.ValidationError(
                "Usernames should not contain special characters."
            )
        if (len(data) > 15) or (len(data) < 5):
            raise forms.ValidationError(
                "Username must have at least 5 characters and at most 15 characters"
            )
        return data

    class Meta:

        model = User
        fields = ("username", "email", "password1", "password2")


class LoginForm(forms.Form):

    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=150, widget=forms.PasswordInput)
