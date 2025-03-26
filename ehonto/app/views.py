from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings 
from .forms import SignupForm, BookForm, UserUpdateForm
from .models import Book, Child, Memo, Favorite, ReadCount, UserProfile 
from django.views.generic import ListView
from .forms import ChildForm
from django.db import models
from django.contrib.auth.models import AnonymousUser, User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum
from collections import defaultdict



# ✅ ポートフォリオ画面（最初に表示するページ）
class PortfolioView(View):
    def get(self, request):
        return render(request, "portfolio.html")

# ✅ 新規登録画面
from django.contrib.auth.models import User
from django.contrib import messages

class SignupView(View):
    def get(self, request):
        form = SignupForm()
        return render(request, "signup.html", {"form": form})  
    
    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            if User.objects.filter(username=email).exists():
                messages.error(request, "このメールアドレスはすでに使用されています。")
                return render(request, "signup.html", {"form": form})

            user = form.save(commit=False)
            user.first_name = form.cleaned_data["first_name"]
            user.email = email
            user.username = email  # ← これがないとusername未設定になる
            user.save()
            login(request, user)
            return redirect("home")

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
from django.core.paginator import Paginator

@login_required
def favorite(request):
    selected_child_id = request.GET.get("child_id")
    selected_child = None

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id)
        favorites = Favorite.objects.filter(user=request.user, child=selected_child)
    else:
        favorites = Favorite.objects.filter(user=request.user)

    books = Book.objects.filter(id__in=favorites.values_list("book_id", flat=True)).order_by("-created_at")

    # ✅ ページネーション（7x4）
    paginator = Paginator(books, 28)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "favorite.html", {
        "books": page_obj,
        "children": Child.objects.all(),
        "selected_child_id": selected_child_id,
        "page_obj": page_obj,
    })

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
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.save()  # 先に保存してから child をセット

            child_id = request.POST.get("child_id")
            print("✅ POSTされたchild_id:", child_id)
            if child_id:
                try:
                    selected_child = Child.objects.get(id=int(child_id))
                    print("✅ 受け取った child_id:", child_id)
                    book.child.set([selected_child])  # ✅ ManyToMany 関連付け
                except Child.DoesNotExist:
                    pass

            print("✅ 登録された子ども:", list(book.child.all()))

            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "フォームが無効です"})

    else:
        form = BookForm()
        children = Child.objects.filter(user=request.user)
        return render(request, "add_book.html", {"form": form, "children": children})


# ✅ パスワード変更ビュー
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'password_change.html'
    success_url = reverse_lazy('password_change_done')

password_change_view = login_required(CustomPasswordChangeView.as_view())

# ✅ Django標準の新規登録ビュー
def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 == password2:
            # ユーザー作成
            user = User.objects.create_user(username=email, email=email, password=password1)
            user.first_name = name
            user.save()

            # ✅ 招待URLに含まれるinviteパラメータから招待者を特定
            invited_by_id = request.GET.get("invite")
            if invited_by_id:
                try:
                    inviter = User.objects.get(id=invited_by_id)
                    UserProfile.objects.create(user=user, invited_by=inviter)
                except User.DoesNotExist:
                    pass  # 存在しないユーザーIDなら無視

            # 自動ログイン
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "パスワードが一致しません")

    return render(request, 'signup.html')

# ✅ 絵本詳細ビュー

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if book.child.exists():
        registered_children = book.child.all()
    else:
        registered_children = Child.objects.all()

     # ✅ ログインユーザーに紐づくお気に入りのみ取得
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user, book=book)
        favorited_child_ids = favorites.values_list('child_id', flat=True)
    else:
        favorited_child_ids = []
    
     # ✅ 各子どもに対する読んだ回数を取得
    from .models import ReadCount
    read_counts_qs = ReadCount.objects.filter(book=book)
    read_counts = {rc.child.id: rc.count for rc in read_counts_qs}

     # ✅ メモを渡すための追加処理
    from .models import Memo
    memos_qs = Memo.objects.filter(book=book)
    memos = {memo.child.id: memo.content for memo in memos_qs}

    return render(request, 'book_detail.html', {
        'book': book,
        'registered_children': registered_children,
        'favorited_child_ids': list(favorited_child_ids),  
        'read_counts': read_counts,
        'memos': memos,
    })

# ✅ 絵本削除ビュー
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        book.delete()
        messages.success(request, "絵本を削除しました。")
        return redirect('home')  # ✅ 削除後はホーム画面へリダイレクト

    return render(request, "book_detail.html", {"book": book})


@login_required
def home_view(request):
    selected_child_id = request.GET.get("child_id")
    selected_child = None

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=request.user)
        books_qs = Book.objects.filter(child=selected_child)
    else:
        # ✅ すべての本棚（共通＆子ども両方）を対象に表示
        books_qs = Book.objects.all()

    # ✅ 画像が空でないものだけを表示
    books_qs = books_qs.exclude(image='').exclude(image=None).order_by("-created_at")

    # ✅ ページネーション（7x4 = 28件/ページ）
    paginator = Paginator(books_qs, 28)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ✅ 子どもリストをコンテキストに追加（ドロップダウン用）
    children = Child.objects.filter(user=request.user).distinct()

    context = {
        "books": page_obj,
        "page_obj": page_obj,
        "MEDIA_URL": settings.MEDIA_URL,
        "children": children,
        "selected_child_id": selected_child_id,
    }
    return render(request, "home.html", context)

  

# ✅ メモを保存するAPI（非同期リクエスト対応）
@require_POST
@login_required
def save_memo(request):
    book_id = request.POST.get("book_id")
    child_id = request.POST.get("child_id")
    content = request.POST.get("content")

    book = get_object_or_404(Book, id=book_id)
    child = get_object_or_404(Child, id=child_id)

    memo, created = Memo.objects.get_or_create(book=book, child=child)
    memo.content = content
    memo.save()

    return JsonResponse({"status": "ok", "content": memo.content})

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
    # 登録済みの子どもをカウント
    existing_children = Child.objects.all()
    if existing_children.count() >= 3:
        messages.error(request, "子どもは最大3人まで登録できます。")
        return redirect("child_edit")

    if request.method == "POST":
        form = ChildForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('child_edit')
    else:
        form = ChildForm()

    return render(request, 'child_edit.html', {'form': form, 'children': existing_children, 'max_children': 3})



# ✅ お気に入り
@csrf_exempt
@login_required
def toggle_favorite(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            print("❌ 未ログインのユーザーがアクセス")
            return JsonResponse({"favorited": False, "error": "ログインが必要です"})

        data = json.loads(request.body)
        print("✅ 受信したデータ:", data)

        book_id = data.get("book_id")
        child_id = data.get("child_id")

        try:
            book = Book.objects.get(id=book_id)
            child = Child.objects.get(id=child_id)
        except (Book.DoesNotExist, Child.DoesNotExist):
            return JsonResponse({"favorited": False, "error": "該当データなし"})

        user = request.user
        print("✅ ログインユーザー:", user)

        favorite, created = Favorite.objects.get_or_create(user=user, book=book, child=child)

        if not created:
            favorite.delete()
            print("⭐ お気に入りを解除しました")
            return JsonResponse({"favorited": False})
        else:
            print("⭐ お気に入りに登録しました")
            return JsonResponse({"favorited": True})

    return JsonResponse({"error": "Invalid request"}, status=400)


# ✅ こども情報編集画面
def child_update(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    if request.method == "POST":
        form = ChildForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            return redirect('child_edit')
    else:
        form = ChildForm(instance=child)
    return render(request, 'child_update.html', {'form': form})

def child_delete(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    if request.method == "POST":
        child.delete()
        return redirect('child_edit')
    return render(request, 'child_delete_confirm.html', {'child': child})

# ✅ よんだ回数
@require_POST
@login_required
def increment_read_count(request):
    book_id = request.POST.get("book_id")
    child_id = request.POST.get("child_id")

    book = get_object_or_404(Book, id=book_id)
    child = get_object_or_404(Child, id=child_id)

    read_count, created = ReadCount.objects.get_or_create(book=book, child=child)
    read_count.count += 1
    read_count.save()

    return JsonResponse({"count": read_count.count})

# ✅ もっとよんでページ
def more_read(request):
    selected_child_id = request.GET.get("child_id")
    children = Child.objects.filter(user=request.user)
    selected_child = None

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=request.user)
        books = Book.objects.filter(child=selected_child).distinct()
    else:
        books = Book.objects.filter(child=None).distinct()

    # 絵本ごとの読んだ回数を取得
    book_with_counts = []
    for book in books:
        if selected_child:
            count = ReadCount.objects.filter(book=book, child=selected_child).aggregate(total=Sum("count"))["total"] or 0
        else:
            count = 0  # 共通の本棚では後で個別に集計
        book_with_counts.append((book, count))

    sorted_books = sorted(book_with_counts, key=lambda x: x[1])[:6]
    sorted_books_only = [b[0] for b in sorted_books]

    # ✅ 読んだ回数データの辞書づくり
    read_counts = {}
    tooltip_counts = defaultdict(dict)

    if selected_child:
        read_counts = {
            book.id: ReadCount.objects.filter(book=book, child=selected_child).aggregate(total=Sum("count"))["total"] or 0
            for book in sorted_books_only
        }
    else:
        for book in sorted_books_only:
            for child in children:
                count = ReadCount.objects.filter(book=book, child=child).aggregate(total=Sum("count"))["total"] or 0
                tooltip_counts[book.id][child.name] = count

    return render(request, "more_read.html", {
        "books": sorted_books_only,
        "children": children,
        "selected_child_id": selected_child_id,
        "read_counts": read_counts,
        "tooltip_counts": tooltip_counts,
    })

@login_required
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        book.title = request.POST.get("title")
        book.author = request.POST.get("author")

        # ✅ 新しい画像があれば更新
        if 'image' in request.FILES:
            book.image = request.FILES['image']

        book.save()
        return redirect("book_detail", book_id=book.id)
    
@login_required
def family_invite(request):
    # 招待URLを作成
    invite_url = request.build_absolute_uri(
        reverse("signup") + f"?invite={request.user.id}"
    )

    # 自分が招待した家族（UserProfile 経由）
    invited = User.objects.filter(userprofile__invited_by=request.user)

    return render(request, "family_invite.html", {
        "invite_url": invite_url,
        "invited_users": invited,
    })


