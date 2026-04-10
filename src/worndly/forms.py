from django import forms
from django.contrib.auth.models import User


class PlayerProfileCreationForm(forms.Form):
    # Name is optional, but the auth fields are required.
    name = forms.CharField(max_length=120, required=False)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username
