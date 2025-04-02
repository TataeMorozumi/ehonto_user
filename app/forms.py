from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # ← これが重要！
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
        return user
    

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username=email).exists():
            raise ValidationError("このメールアドレスはすでに登録されています。")
        return email


from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'image']  # ✅ 画像フィールドを含める

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise forms.ValidationError("画像を選択してください。")
        return image    

#設定画面
from django import forms
from django.contrib.auth.models import User

class UserUpdateForm(forms.ModelForm):
    new_first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '新しい名前を入力'})
    )
    new_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '新しいメールアドレスを入力'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'email']
        labels = {
            'first_name': '現在の名前',
            'email': '現在のメールアドレス',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': True}),
        }

#絵本登録
from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'image']
        labels = {
            'title': 'タイトル',
            'author': '作者',
            'image': '画像',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '絵本のタイトルを入力'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '作者を入力'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

#こども情報登録
from django import forms
from .models import Child

class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name']
        labels = {'name': '子どもの名前'}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '子どもの名前を入力'}),
        }
