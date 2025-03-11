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
from .forms import BookForm


def add_book(request):
    if request.method == "POST":
        title = request.POST.get('title')
        author = request.POST.get('author')
        form = BookForm(request.POST, request.FILES)  # ✅ `request.FILES` で画像を受け取る
        if form.is_valid():
            form.save()
        if title and author:  # 必須データがあるか確認
            Book.objects.create(title=title, author=author)
            return JsonResponse({"success": True})  # ✅ JSON を返す

        return JsonResponse({"success": False, "error": "データが不足しています"})

    return JsonResponse({"success": False, "error": "無効なリクエスト"})
#設定画面
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm

@login_required
def settings_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            new_first_name = form.cleaned_data.get('new_first_name')
            new_email = form.cleaned_data.get('new_email')

            if new_first_name:
                request.user.first_name = new_first_name  # ✅ 新しい名前を更新
            if new_email:
                request.user.email = new_email  # ✅ 新しいメールアドレスを更新

            request.user.save()
            messages.success(request, "アカウント情報を更新しました！")
            return redirect('settings')  # 設定画面にリダイレクト
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'settings.html', {'form': form})