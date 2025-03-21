from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings 
from .forms import SignupForm, BookForm, UserUpdateForm
from .models import Book, Child, Memo
from django.views.generic import ListView
from .forms import ChildForm
from django.db import models
from django.db.models import Q


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
    template_name = "home.html"
    context_object_name = "books"
    paginate_by = 28  # ✅ 7列×4段

    def get_queryset(self):
        # ✅ すべての本棚の絵本を取得（個人の本棚の絵本も含める）
        books = Book.objects.exclude(image='').exclude(image=None).order_by('-created_at')
        return books

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["MEDIA_URL"] = settings.MEDIA_URL
        context["children"] = Child.objects.all() .distinct() # ✅ 子どもの本棚を取得
        context["selected_child_id"] = self.request.GET.get("child_id", "")
        return context


# ✅ 子どもの本棚ページ
def child_bookshelf(request, child_id):
    selected_child = get_object_or_404(Child, id=child_id)

# ✅ 共通の本棚 + 選択した子どもの本棚の絵本を取得
    books = Book.objects.filter(models.Q(child=selected_child) | models.Q(child=None)).order_by("-created_at")

# ✅ ページネーション設定 (7列 × 4行 = 28冊)
    paginator = Paginator(books, 28)  # 1ページ28冊まで
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "child_bookshelf.html", {
        "selected_child": selected_child,
        "selected_child_id": str(child_id),
        "books": page_obj,  # ✅ ページネーションを適用
        "children": Child.objects.all().distinct(),
        "page_obj": page_obj,  # ✅ ページネーション情報を渡す
    })


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
from django.http import JsonResponse

def add_book(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.save()

            # child_id があれば、ManyToManyとしてセット
            child_id = request.POST.get("child_id")
            if child_id:
                try:
                    selected_child = Child.objects.get(id=int(child_id))
                    book.child.set([selected_child])  # ✅ 修正ポイント
                except Child.DoesNotExist:
                    pass

            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "フォームが無効です"})

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

# ✅ 絵本詳細ビュー
def book_detail(request, book_id):
    try:
        book = get_object_or_404(Book, id=book_id)
        return render(request, "book_detail.html", {"book": book})
    except Exception as e:
        print(f"❌ book_detail のエラー: {e}")
        return render(request, "error.html", {"error_message": "絵本の詳細を取得できませんでした。"})

# ✅ 絵本削除ビュー
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        book.delete()
        messages.success(request, "絵本を削除しました。")
        return redirect('home')  # ✅ 削除後はホーム画面へリダイレクト

    return render(request, "book_detail.html", {"book": book})

def home_view(request):
    children = Child.objects.all().distinct()  # 子ども一覧
    selected_child_id = request.GET.get("child_id")  # 選択された子ども
    selected_child = None

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id)
        books = Book.objects.filter(child=selected_child)
    else:
        books = Book.objects.filter(child=None)  # 共通の本棚を表示

    return render(request, "home.html", {
        "books": books,
        "children": children,
        "selected_child": selected_child,
    })  

# ✅ メモを保存するAPI（非同期リクエスト対応）
@csrf_exempt
def save_memo(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            child = Child.objects.get(id=data["child_id"])
            book = Book.objects.get(id=data["book_id"])
            memo = Memo.objects.create(book=book, child=child, content=data["memo"])
            return JsonResponse({"status": "success", "memo": memo.content})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)  

# ✅ 子ども情報編集画面
def child_edit(request):
    children = Child.objects.all()  # 登録済みの子どもを取得
    form = ChildForm()  # 新規追加用のフォーム

    if request.method == "POST":
        if children.count() >= 3:
            messages.error(request, "子どもの登録は最大3人までです。")
        else:
            form = ChildForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "子どもが登録されました。")
                return redirect('child_edit')  # ✅ 追加後にページを更新

    return render(request, 'child_edit.html', {'children': children, 'form': form})

# ✅ 子ども追加処理
def child_add(request):
    if request.method == "POST":
        form = ChildForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('child_edit')  # ✅ 追加後に「子ども情報編集画面」へ戻る
    else:
        form = ChildForm()

    return render(request, 'child_edit.html', {'form': form})
