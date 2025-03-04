from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label="メールアドレス", required=True)
    first_name = forms.CharField(label="名前", max_length=30, required=True)

    class Meta:
        model = User
        fields = ["first_name", "email", "username", "password1", "password2"]
