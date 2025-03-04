from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    user_name = forms.CharField(max_length=30, required=True, label="名前")
    email = forms.EmailField(required=True, label="メールアドレス")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
