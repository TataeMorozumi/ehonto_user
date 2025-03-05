from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from .forms import SignupForm

class PortfolioView(View):
    def get(self, request):
        return render(request, "portfolio.html")
    
class SignupView(View):
    def get(self, request):
        form = SignupForm()
        return render(request, "signup.html", {"form": form})  
    
    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.save()
            login(request, user)  # 自動ログイン
            return redirect("home")  # ホーム画面へリダイレクト
        return render(request, "accounts/signup.html", {"form": form})
    
class LoginView(View):
    def get(self, request):
        return render(request, "login.html")  

class HomeView(View):
    def get(self, request):
        return render(request, "home.html")    

def favorite(request):
    return render(request, 'favorite.html')

def review(request):
    return render(request, 'review.html')

def more_read(request):
    return render(request, 'more_read.html')

def settings(request):
    return render(request, 'settings.html')

def family_invite(request):
    return render(request, 'family_invite.html')
        