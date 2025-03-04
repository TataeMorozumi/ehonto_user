from django.shortcuts import render, redirect
from django.views import View

class PortfolioView(View):
    def get(self, request):
        return render(request, "portfolio.html")
    
class SignupView(View):
    def get(self, request):
        return render(request, "signup.html")  

class LoginView(View):
    def get(self, request):
        return render(request, "login.html")  

class HomeView(View):
    def get(self, request):
        return render(request, "home.html")            