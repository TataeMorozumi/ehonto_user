from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings 
from .forms import SignupForm, BookForm, UserUpdateForm
from .models import Book
from django.views.generic import ListView


# ✅ ポートフォリオ画面（最初に表示するページ）
class PortfolioView(View):
    def get(self, request):
        return render(request, "portfolio.html")

# ✅ 新規登録画面
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
        return render(request, "signup.html", {"form": form})

# ✅ ログイン画面
class LoginView(View):
    def get(self, request):
        return render(request, "login.html")  

# ✅ ホーム画面（絵本一覧を表示）
class HomeView(ListView):
    model = Book
    template_name = "home.html"  # ✅ home.html をテンプレートとして指定
    context_object_name = "books"  # ✅ テンプレート内で使用する変数名を定義
    paginate_by = 6  # ✅ 1ページに6件ずつ表示

    def get_queryset(self):
        books = Book.objects.all().order_by('-created_at')  # ✅ 登録順に取得
        print(f"📌 デバッグ: HomeView に渡されたデータの数: {books.count()}")  
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["MEDIA_URL"] = settings.MEDIA_URL
        return context 

# ✅ お気に入りページ
def favorite(request):
    return render(request, 'favorite.html')

# ✅ ふりかえりページ
def review(request):
    return render(request, 'review.html')

# ✅ もっとよんでページ
def more_read(request):
    return render(request, 'more_read.html')

# ✅ 設定ページ
def settings_view(request):
    return render(request, 'settings.html')

# ✅ 家族招待ページ
def family_invite(request):
    return render(request, 'family_invite.html')

# ✅ 絵本登録ページ
def add_book(request):
    if request.method == "POST":
        print("📌 登録リクエストを受信しました")
        print(f"📌 リクエストデータ: {request.POST}")
        print(f"📌 リクエストファイル: {request.FILES}")

        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            print(f"✅ 登録成功: {book.title}, 画像: {book.image}")  
            return redirect('home') 
        else:
            print("❌ フォームエラー:", form.errors)  

    else:
        form = BookForm()
    return render(request, "add_book.html", {"form": form})

# ✅ パスワード変更ビュー
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'password_change.html'
    success_url = reverse_lazy('password_change_done')

password_change_view = login_required(CustomPasswordChangeView.as_view())

# ✅ Django標準の新規登録ビュー
def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # ✅ 登録後にログイン
            return redirect('home')  # ✅ ホーム画面へリダイレクト
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})
