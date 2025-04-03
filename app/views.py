from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.db import models
from django.db.models import Count, Sum, Q
from django.utils.timezone import now
from django.core.serializers.json import DjangoJSONEncoder

import json
import calendar
from datetime import datetime, timedelta, date
from collections import defaultdict, Counter

from .forms import SignupForm, BookForm, UserUpdateForm, ChildForm
from .models import Book, Child, Memo, Favorite, ReadCount, UserProfile, ReadHistory
from django.contrib.auth.models import AnonymousUser, User

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

    children = Child.objects.filter(user=request.user)  

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=request.user)
        favorites = Favorite.objects.filter(user=request.user, child=selected_child, child__user=request.user )
    else:
        favorites = Favorite.objects.filter(user=request.user, child__user=request.user )

    # ✅ お気に入りの book も自分のものだけ
    books = Book.objects.filter(
        id__in=favorites.values_list("book_id", flat=True),
        user=request.user
    ).order_by("-created_at")

    paginator = Paginator(books, 28)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    books_list = list(page_obj)
    book_rows = [books_list[i:i+7] for i in range(0, len(books_list), 7)]

    return render(request, "favorite.html", {
        "books": page_obj,
        "book_rows": book_rows,
        "children": children,
        "selected_child_id": selected_child_id,
        "page_obj": page_obj,
    })

# ✅ 設定ページ
def settings_view(request):
    return render(request, 'settings.html')

# ✅ 家族招待ページ
def family_invite(request):
    return render(request, 'family_invite.html')


# ✅ 絵本登録ページ（重複チェック付き）
from django.views.decorators.csrf import csrf_exempt

def add_book(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data["title"]
            child_id = request.POST.get("child_id")

            # ✅ 共通の本棚（child_id が空や None の場合）を考慮
            selected_child = None
            if child_id and child_id != "None":
                try:
                    selected_child = Child.objects.get(id=int(child_id))
                    existing_books = Book.objects.filter(
                        title=title,
                        child=selected_child
                    )
                    if existing_books.exists():
                        return JsonResponse({
                            "success": False,
                            "error": "同じ絵本がすでにこの本棚に登録されています。"
                        })
                except Child.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "error": "子ども情報が見つかりません。"
                    })

            book = form.save(commit=False)
            book.user = request.user  # ← ここを先に！
            book.save()
            form.save_m2m()

            if selected_child:
                book.child.set([selected_child])  # ✅ 紐づけ（共通の場合はスキップ）

            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "フォームが無効です"})



    # ✅ GETの場合のみテンプレートを返す！
    form = BookForm()
    selected_child_id = request.GET.get("child_id")
    children = Child.objects.filter(user=request.user)

    return render(request, "add_book.html", {
        "form": form,
        "selected_child_id": selected_child_id,
        "children": children,
    })

# ✅ パスワード変更ビュー
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'password_change.html'
    success_url = reverse_lazy('password_change_done')

password_change_view = login_required(CustomPasswordChangeView.as_view())



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

            # ✅ URLパラメータ code を使って招待者を取得
            invited_by_id = request.POST.get("code")  # ← POSTで受け取るように修正

            inviter = None
            if invited_by_id:
                try:
                    inviter = User.objects.get(id=invited_by_id)
                except User.DoesNotExist:
                    pass  # 存在しない場合はスルー

            # ✅ UserProfileを作成して招待者を保存
            UserProfile.objects.create(user=user, invited_by=inviter)

            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "パスワードが一致しません")

    return render(request, "signup.html")

# ✅ 絵本詳細ビュー
@login_required
def book_detail(request, book_id):
    # ✅ 自分の絵本しか取得できないように制限
    book = get_object_or_404(Book, id=book_id, user=request.user)

    # ✅ 該当絵本に紐づく子ども
    if book.child.exists():
        registered_children = book.child.filter(user=request.user)
    else:
        registered_children = Child.objects.filter(user=request.user)

    favorites = Favorite.objects.filter(user=request.user, book=book)
    favorited_child_ids = favorites.values_list('child_id', flat=True)

    # ✅ 各子どもの読んだ回数取得
    read_counts_qs = ReadCount.objects.filter(book=book, child__user=request.user)
    read_counts = {rc.child.id: rc.count for rc in read_counts_qs}

    # ✅ 各子どものメモ取得
    memos_qs = Memo.objects.filter(book=book, child__user=request.user)
    memos = {memo.child.id: memo.content for memo in memos_qs}

    return render(request, 'book_detail.html', {
        'book': book,
        'registered_children': registered_children,
        'favorited_child_ids': list(favorited_child_ids),  
        'read_counts': read_counts,
        'memos': memos,
    })


# ✅ 絵本削除ビュー
@login_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)  # ← 🔧 修正

    if request.method == "POST":
        book.delete()
        messages.success(request, "絵本を削除しました。")
        return redirect('home')

    return render(request, "book_detail.html", {"book": book})



from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.conf import settings

from .models import Book, Child

@login_required
def home_view(request):
    selected_child_id = request.GET.get("child_id")
    selected_child = None

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=request.user)
        books_qs = Book.objects.filter(child=selected_child, user=request.user)
    else:
        books_qs = Book.objects.filter(child=selected_child, user=request.user)

    books_qs = books_qs.exclude(image='').exclude(image=None).order_by("-created_at")

    paginator = Paginator(books_qs, 28)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    books_list = list(page_obj)
    book_rows = [books_list[i:i+7] for i in range(0, len(books_list), 7)]

    children = Child.objects.filter(user=request.user).distinct()

    context = {
        "books": page_obj,
        "page_obj": page_obj,
        "MEDIA_URL": settings.MEDIA_URL,
        "children": children,
        "selected_child_id": selected_child_id,
        "book_rows": book_rows,
    }
    return render(request, "home.html", context)

  

# ✅ メモを保存するAPI（非同期リクエスト対応）
@require_POST
@login_required
def increment_read_count(request):
    book_id = request.POST.get("book_id")
    child_id = request.POST.get("child_id")

    book = get_object_or_404(Book, id=book_id, user=request.user)
    child = get_object_or_404(Child, id=child_id, user=request.user)

    # Count 更新
    read_count, _ = ReadCount.objects.get_or_create(book=book, child=child)
    read_count.count += 1
    read_count.save()

    # 履歴を追加
    ReadHistory.objects.create(book=book, child=child)

    return JsonResponse({"count": read_count.count})

# ✅ 子ども情報編集画面
@login_required
def child_edit(request):
    children = Child.objects.filter(user=request.user)  
    form = ChildForm()

    if request.method == "POST":
        if children.count() >= 3:
            messages.error(request, "子どもの登録は最大3人までです。")
        else:
            form = ChildForm(request.POST)
            if form.is_valid():
                child = form.save(commit=False)
                child.user = request.user  
                child.save()
                messages.success(request, "子どもが登録されました。")
                return redirect('child_edit')

    return render(request, 'child_edit.html', {'children': children, 'form': form})

# ✅ 子ども追加処理
@login_required
def child_add(request):
    # ✅ ログインユーザーの子どもを対象にカウント
    existing_children = Child.objects.filter(user=request.user)

    if existing_children.count() >= 3:
        messages.error(request, "子どもは最大3人まで登録できます。")
        return redirect("child_edit")

    if request.method == "POST":
        form = ChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.user = request.user  # ✅ ユーザーに紐づけ
            child.save()
            return redirect('child_edit')
    else:
        form = ChildForm()

    return render(request, 'child_edit.html', {
        'form': form,
        'children': existing_children,
        'max_children': 3
    })



# ✅ お気に入り
@csrf_exempt
@login_required
def toggle_favorite(request):
    if request.method == "POST":
        data = json.loads(request.body)
        book_id = data.get("book_id")
        child_id = data.get("child_id")

        try:
            book = Book.objects.get(id=book_id, user=request.user)
            child = Child.objects.get(id=child_id, user=request.user)
        except (Book.DoesNotExist, Child.DoesNotExist):
            return JsonResponse({"favorited": False, "error": "該当データなし"})

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            book=book,
            child=child
        )

        if not created:
            favorite.delete()
            return JsonResponse({"favorited": False})
        else:
            return JsonResponse({"favorited": True})

    return JsonResponse({"error": "Invalid request"}, status=400)

# ✅ こども情報編集画面
@login_required
def child_update(request, child_id):
    child = get_object_or_404(Child, id=child_id, user=request.user)  

    if request.method == "POST":
        form = ChildForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            return redirect('child_edit')
    else:
        form = ChildForm(instance=child)

    return render(request, 'child_update.html', {'form': form})


@login_required
def child_delete(request, child_id):
    child = get_object_or_404(Child, id=child_id, user=request.user)  

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

    book = get_object_or_404(Book, id=book_id, user=request.user)
    child = get_object_or_404(Child, id=child_id, user=request.user)

    read_count, _ = ReadCount.objects.get_or_create(book=book, child=child)
    read_count.count += 1
    read_count.save()

    ReadHistory.objects.create(book=book, child=child)

    return JsonResponse({"count": read_count.count})


@login_required
def more_read(request):
    selected_child_id = request.GET.get("child_id")
    children = Child.objects.filter(user=request.user)
    selected_child = None

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=request.user)
        books = Book.objects.filter(child=selected_child, user=request.user).distinct()
    else:
        books = Book.objects.filter(child=None, user=request.user).distinct()

    # 絵本ごとの読んだ回数を取得
    book_with_counts = []
    for book in books:
        if selected_child:
            count = ReadCount.objects.filter(book=book, child=selected_child).aggregate(total=Sum("count"))["total"] or 0
        else:
            count = ReadCount.objects.filter(book=book, child__user=request.user).aggregate(total=Sum("count"))["total"] or 0
        book_with_counts.append((book, count))
        

    sorted_books = sorted(book_with_counts, key=lambda x: x[1])[:6]
    sorted_books_only = [b[0] for b in sorted_books]

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

from django.contrib.auth.decorators import login_required

@login_required
def edit_book(request, book_id):
    # ✅ 自分の絵本だけ編集できるように制限
    book = get_object_or_404(Book, id=book_id, user=request.user)

    if request.method == "POST":
        book.title = request.POST.get("title")
        book.author = request.POST.get("author")

        if 'image' in request.FILES:
            book.image = request.FILES['image']

        book.save()
        return redirect("book_detail", book_id=book.id)

    
@login_required
def family_invite(request):
    invite_url = f"http://127.0.0.1:8000/app/signup/?code={request.user.id}"


    # ✅ 自分が招待したユーザーを取得（← これが必要！）
    invited_users = User.objects.filter(userprofile__invited_by=request.user)

    return render(request, 'family_invite.html', {
        'invite_url': invite_url,
        'invited_users': invited_users,
    })



# ✅ 検索結果ページ
def search_results(request):
    query = request.GET.get("q")
    results = []

    if query:
        results = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).order_by("-created_at")

    return render(request, "search_results.html", {
        "query": query,
        "results": results
    })

# ✅ よんだ履歴
@require_POST
@login_required
def increment_read_count(request):
    book_id = request.POST.get("book_id")
    child_id = request.POST.get("child_id")

    book = get_object_or_404(Book, id=book_id, user=request.user)
    child = get_object_or_404(Child, id=child_id, user=request.user)


    read_count, _ = ReadCount.objects.get_or_create(book=book, child=child)
    read_count.count += 1
    read_count.save()

    # 履歴を追加
    ReadHistory.objects.create(book=book, child=child)

    return JsonResponse({"count": read_count.count})

@require_POST
@login_required
def decrement_read_count(request):
    print("📉 decrement_read_count 呼ばれた")  
    data = json.loads(request.body)
    book_id = data.get("book_id")
    child_id = data.get("child_id")

    try:
        book = Book.objects.get(id=book_id)
        child = Child.objects.get(id=child_id, user=request.user)
        read_count, _ = ReadCount.objects.get_or_create(book=book, child=child)

        if read_count.count > 0:
            read_count.count -= 1
            read_count.save()

        return JsonResponse({"success": True, "count": read_count.count})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@login_required
def review_default(request):
    today = date.today()
    return redirect("review", year=today.year, month=today.month)            
from collections import defaultdict, Counter
from django.utils.timezone import now
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def review(request, year, month):
    selected_child_id = request.GET.get("child_id")
    selected_child = None
    children = Child.objects.filter(user=request.user)

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=request.user)

    current_date = date(year, month, 1)
    days_in_month = calendar.monthrange(year, month)[1]
    calendar_days = list(range(1, days_in_month + 1))
    prev_month = current_date - timedelta(days=1)
    next_month = (current_date + timedelta(days=days_in_month)).replace(day=1)

    # ✅ ログインユーザーの履歴のみ取得
    if selected_child:
        histories = ReadHistory.objects.filter(
            child=selected_child,
            child__user=request.user,
            date__year=year,
            date__month=month
        )
    else:
        histories = ReadHistory.objects.filter(
            date__year=year,
            date__month=month,
            book__user=request.user,
            child__user=request.user 
        )

    read_history_json = json.dumps([
        {"date": str(h.date), "title": h.book.title}
        for h in histories
    ], cls=DjangoJSONEncoder)

    calendar_data = defaultdict(list)
    for history in histories:
        day = history.date.day
        calendar_data[day].append(history.book)

    calendar_data = {
        str(day): [
            {
                "id": book.id,
                "title": book.title,
                "image_url": book.image.url if book.image else ""
            }
            for book in set(books)
        ]
        for day, books in calendar_data.items()
    }

    calendar_data_json = json.dumps(calendar_data, cls=DjangoJSONEncoder)

    book_counter = Counter([h.book.title for h in histories])
    most_read_title = book_counter.most_common(1)[0][0] if book_counter else None

    monthly_total = histories.count()
    child_totals = defaultdict(int)
    for h in histories:
        child_totals[h.child.name] += 1

    return render(request, "review.html", {
        "children": children,
        "selected_child_id": selected_child_id,
        "calendar_days": calendar_days,
        "calendar_data": calendar_data,
        "current_date": current_date,
        "prev_month": {"year": prev_month.year, "month": prev_month.month},
        "next_month": {"year": next_month.year, "month": next_month.month},
        "read_history_json": read_history_json,
        "most_read_title": most_read_title,
        "monthly_total": monthly_total,
        "child_totals": dict(child_totals),
        "calendar_data_json": calendar_data_json,
        "year": year,
        "month": month,
    })


@require_POST
@login_required
def decrement_read_count(request):
    print("📉 decrement_read_count 呼ばれた")  
    data = json.loads(request.body)
    book_id = data.get("book_id")
    child_id = data.get("child_id")

    try:
        book = Book.objects.get(id=book_id)
        child = Child.objects.get(id=child_id, user=request.user)
        read_count, _ = ReadCount.objects.get_or_create(book=book, child=child)

        if read_count.count > 0:
            read_count.count -= 1
            read_count.save()

        return JsonResponse({"success": True, "count": read_count.count})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
@require_POST
@login_required
def save_memo(request):
    book_id = request.POST.get("book_id")
    child_id = request.POST.get("child_id")
    content = request.POST.get("content")

    # ✅ ログインユーザーの book・child のみ許可
    book = get_object_or_404(Book, id=book_id, user=request.user)
    child = get_object_or_404(Child, id=child_id, user=request.user)

    memo, _ = Memo.objects.get_or_create(book=book, child=child)
    memo.content = content
    memo.save()

    return JsonResponse({"status": "ok", "content": memo.content})  