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

def add_book(request):
    return render(request, 'add_book.html')


from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from app.models import Book

class HomeView(View):
    def get(self, request):
        book_list = Book.objects.all()  # 全データを取得
        paginator = Paginator(book_list, 6)  # 1ページに6件ずつ表示
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, "home.html", {"page_obj": page_obj})

from django.http import JsonResponse
from django.shortcuts import render
from .models import Book

def add_book(request):
    if request.method == "POST":
        title = request.POST.get('title')
        author = request.POST.get('author')
        published_date = request.POST.get('published_date')
        
        if title and author and published_date:  # 必須データがあるか確認
            Book.objects.create(title=title, author=author, published_date=published_date)
            return JsonResponse({"success": True})  # ✅ JSON を返す

        return JsonResponse({"success": False, "error": "データが不足しています"})

    return JsonResponse({"success": False, "error": "無効なリクエスト"})