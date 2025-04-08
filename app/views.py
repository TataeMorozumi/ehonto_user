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

from .forms import BookForm, UserUpdateForm, ChildForm, SignupForm
from .models import Book, Child, Memo, Favorite, ReadCount, UserProfile, ReadHistory
from django.contrib.auth.models import AnonymousUser, User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# ✅ ポートフォリオ画面（最初に表示するページ）
class PortfolioView(View):
    def get(self, request):
        return render(request, "portfolio.html")


class CustomPasswordChangeView(PasswordChangeView):
    # login_requiredをdispatchメソッドにデコレータとして適用
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
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
            user.username = email
            user.save()

            # ✅ 招待者を保存する処理
            invited_by_id = request.GET.get("code")
            if invited_by_id:
                try:
                    inviter = User.objects.get(id=invited_by_id)
                    UserProfile.objects.create(user=user, invited_by=inviter)
                except User.DoesNotExist:
                    UserProfile.objects.create(user=user)
            else:
                UserProfile.objects.create(user=user)

            login(request, user)
            return redirect("home")

        return render(request, "signup.html", {"form": form})


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
@login_required
def child_bookshelf(request, child_id):
    selected_child = get_object_or_404(Child, id=child_id, user=request.user)

    # ✅ 自分の絵本だけ取得（選択した子 + 共通）
    books = Book.objects.filter(
        user=request.user
    ).filter(
        models.Q(child=selected_child) | models.Q(child=None)
    ).order_by("-created_at")

    # ✅ ページネーション設定
    paginator = Paginator(books, 28)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "child_bookshelf.html", {
        "selected_child": selected_child,
        "selected_child_id": str(child_id),
        "books": page_obj,
        "children": Child.objects.filter(user=request.user).distinct(),
        "page_obj": page_obj,
    })


# ✅ お気に入りページ
from django.core.paginator import Paginator

@login_required 
def favorite(request):
    selected_child_id = request.GET.get("child_id")
    selected_child = None

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=request.user)
        favorites = Favorite.objects.filter(user=request.user, child=selected_child)
    else:
        favorites = Favorite.objects.filter(user=request.user)

    books = Book.objects.filter(
        id__in=favorites.values_list("book_id", flat=True),
        user=request.user  # 🔐 ← これを追加！
    ).order_by("-created_at")


    # ✅ ページネーション（7x4 = 28冊）
    paginator = Paginator(books, 28)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    books_list = list(page_obj)
    book_rows = [books_list[i:i+7] for i in range(0, len(books_list), 7)]

    return render(request, "favorite.html", {
        "books": page_obj,
        "book_rows": book_rows,
        "children": Child.objects.filter(user=request.user),  # ✅ 自分の子どものみ表示
        "selected_child_id": selected_child_id,
        "page_obj": page_obj,
    })

@login_required
def more_read(request):
    user = request.user
    child_id = request.GET.get("child_id")
    children = Child.objects.filter(user=user)
    selected_child_id = child_id if child_id else ""

    if child_id:
        # 🔸個別本棚
        read_data = ReadCount.objects.filter(child__id=child_id, book__user=user)
        read_counts = (
            read_data.values("book")
            .annotate(total_reads=Sum("count"))
            .order_by("total_reads")
        )
        book_ids = [item["book"] for item in read_counts][:6]
        books = Book.objects.filter(id__in=book_ids)
        read_counts_dict = {item["book"]: item["total_reads"] for item in read_counts}
        tooltip_counts = {}
    else:
        # 🔸共通本棚
        books = Book.objects.filter(user=user)[:6]
        read_data = ReadCount.objects.filter(book__in=books, child__user=user)

        read_counts = (
            read_data.values("book", "child__name")
            .annotate(total_reads=Sum("count"))
        )

        # ✅ すべての子ども×絵本を0で初期化
        tooltip_counts = {
            book.id: {child.name: 0 for child in children}
            for book in books
        }

        # ✅ 実データで上書き
        for item in read_counts:
            book_id = item["book"]
            name = item["child__name"]
            count = item["total_reads"]
            tooltip_counts[book_id][name] = count

        read_counts_dict = {}

    return render(request, "more_read.html", {
        "books": books,
        "children": children,
        "selected_child_id": selected_child_id,
        "read_counts": read_counts_dict,
        "tooltip_counts": tooltip_counts,
    })

# ✅ 設定ページ
def settings_view(request):
    return render(request, 'settings.html')

# ✅ 家族招待ページ
def family_invite(request):
    return render(request, 'family_invite.html')


# ✅ 絵本登録ページ（重複チェック付き）
@csrf_exempt 
def add_book(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data["title"]
            child_id = request.POST.get("child_id")

            selected_child = None
            is_common = not child_id or child_id == "None"

            if is_common:
                # ✅ 共通本棚はすべての絵本から重複チェック
                if Book.objects.filter(title=title, user=request.user).exists():
                    return JsonResponse({
                        "success": False,
                        "error": f"「{title}」はすでに登録されています。"
                    })
            else:
                try:
                    selected_child = Child.objects.get(id=int(child_id), user=request.user)
                    # ✅ 子どもごとの絵本から重複チェック
                    existing_books = Book.objects.filter(title=title, user=request.user, child=selected_child)
                    if existing_books.exists():
                        return JsonResponse({
                            "success": False,
                            "error": f"「{title}」はすでに {selected_child.name} の本棚に登録されています。"
                        })
                except Child.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "error": "子ども情報が見つかりません。"
                    })

            # 重複がなければ登録処理
            book = form.save(commit=False)
            book.user = request.user
            book.save()
            form.save_m2m()

            if is_common:
                all_children = Child.objects.filter(user=request.user)
                book.child.set(all_children)
            else:
                book.child.set([selected_child])

            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "フォームが無効です"})

    # GETリクエスト時
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

# ✅ 絵本詳細ビュー

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import Book, Favorite, Memo, ReadCount, Child

@login_required
def book_detail(request, book_id):
    # ✅ Book: ログインユーザーのbookのみ取得
    book = get_object_or_404(Book, id=book_id, user=request.user)

    # ✅ Child: ログインユーザーの子どもだけに限定（ManyToManyで紐づく中から）
    registered_children = book.child.filter(user=request.user)

    # ✅ お気に入り（ユーザー & Book 限定）※child もログインユーザーのみに絞られる
    favorites = Favorite.objects.filter(user=request.user, book=book)
    favorited_child_ids = favorites.values_list('child_id', flat=True)

    # ✅ 読んだ回数（ログインユーザーの子どもに対してのみ）
    read_counts_qs = ReadCount.objects.filter(book=book, child__user=request.user)
    read_counts = {rc.child.id: rc.count for rc in read_counts_qs}

    # ✅ メモ（ログインユーザーの子どもに対してのみ）
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
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)  # ← これに修正

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
        books_qs = Book.objects.filter(child=selected_child, user=request.user)  # ✅ ここを修正
    else:
        books_qs = Book.objects.filter(user=request.user)

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
def save_memo(request):
    book_id = request.POST.get("book_id")
    child_id = request.POST.get("child_id")
    content = request.POST.get("content")

    book = get_object_or_404(Book, id=book_id, user=request.user)
    child = get_object_or_404(Child, id=child_id, user=request.user)


    memo, created = Memo.objects.get_or_create(book=book, child=child)
    memo.content = content
    memo.save()

    return JsonResponse({"status": "ok", "content": memo.content})

# ✅ 子ども情報編集画面
def child_edit(request): 
    children = Child.objects.filter(user=request.user)  # ✅ 自分の子どもだけ取得
    form = ChildForm()  # 新規追加用のフォーム

    if request.method == "POST":
        if children.count() >= 3:
            messages.error(request, "子どもの登録は最大3人までです。")
        else:
            form = ChildForm(request.POST)
            if form.is_valid():
                child = form.save(commit=False)
                child.user = request.user  # ✅ 所有者を指定
                child.save()
                messages.success(request, "子どもが登録されました。")
                return redirect('child_edit')

    return render(request, 'child_edit.html', {'children': children, 'form': form})


# ✅ 子ども追加処理
from django.contrib.auth.decorators import login_required

@login_required
def child_add(request):
    # 自分の子どもだけを取得・カウント
    existing_children = Child.objects.filter(user=request.user)
    if existing_children.count() >= 3:
        messages.error(request, "子どもは最大3人まで登録できます。")
        return redirect("child_edit")

    if request.method == "POST":
        form = ChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.user = request.user  # 🔑←ここが重要
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
    child = get_object_or_404(Child, id=child_id, user=request.user)

    if request.method == "POST":
        form = ChildForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            return redirect('child_edit')
    else:
        form = ChildForm(instance=child)
    return render(request, 'child_update.html', {'form': form})

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


    read_count, created = ReadCount.objects.get_or_create(book=book, child=child)
    read_count.count += 1
    read_count.save()

    return JsonResponse({"count": read_count.count})

# ✅ もっとよんでページ
from django.db.models import Sum

@login_required
def more_read(request):
    user = request.user
    child_id = request.GET.get("child_id")
    children = Child.objects.filter(user=user)
    selected_child_id = child_id if child_id else ""

    if child_id:
        # 子ども個別の本棚：その子の読んだ回数が少ない順に表示
        read_data = ReadCount.objects.filter(child__id=child_id, book__user=user)
        read_counts = (
            read_data.values("book")
            .annotate(total_reads=Sum("count"))
            .order_by("total_reads")
        )
        book_ids = [item["book"] for item in read_counts][:6]
        books = Book.objects.filter(id__in=book_ids)
        read_counts_dict = {item["book"]: item["total_reads"] for item in read_counts}
        tooltip_counts = {}  # 共通本棚でのみ使う
    else:
        # 共通本棚：誰が何回読んだかを book_id ごとに記録
        read_data = ReadCount.objects.filter(book__user=user)
        read_counts = (
            read_data.values("book", "child__name")
            .annotate(total_reads=Sum("count"))
        )
        tooltip_counts = {}
        for item in read_counts:
            book_id = item["book"]
            child_name = item["child__name"]
            count = item["total_reads"]
            if book_id not in tooltip_counts:
                tooltip_counts[book_id] = []
            tooltip_counts[book_id].append(f"{child_name}：{count}回")
        
        books = Book.objects.filter(user=user)[:6]
        read_counts_dict = {}  # 共通本棚では使わない

    context = {
        "books": books,
        "children": children,
        "selected_child_id": selected_child_id,
        "read_counts": read_counts_dict,
        "tooltip_counts": tooltip_counts,
    }
    return render(request, "more_read.html", context)
@login_required
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)

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
            Q(user=request.user), 
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

    book = get_object_or_404(Book, id=book_id)
    child = get_object_or_404(Child, id=child_id)

    # Count 更新
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
@login_required
def review(request, year, month):
    selected_child_id = request.GET.get("child_id")
    selected_child = None
    children = Child.objects.filter(user=request.user)  # 自分の子どもだけ取得

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=request.user)

    current_date = date(year, month, 1)
    days_in_month = calendar.monthrange(year, month)[1]
    calendar_days = list(range(1, days_in_month + 1))
    prev_month = current_date - timedelta(days=1)
    next_month = (current_date + timedelta(days=days_in_month)).replace(day=1)

    # 他ユーザーのデータが表示されないようにuser=request.user を追加
    if selected_child:
        histories = ReadHistory.objects.filter(
            child=selected_child,
            date__year=year,
            date__month=month
        ).select_related('book')
    else:
        histories = ReadHistory.objects.filter(
            date__year=year,
            date__month=month,
            child__user=request.user  # 他ユーザーの履歴を除外
        ).select_related('book')

    # 履歴のJSON形式を作成
    read_history_json = json.dumps([{
        "date": str(h.date),
        "title": h.book.title
    } for h in histories], cls=DjangoJSONEncoder)

    # calendar_data の形式を正しく作成
    calendar_data = defaultdict(dict)  # 内部も辞書に変更（book.idがキー）

    for history in histories:
        day = history.date.day
        book_id = history.book.id

        # すでにその日付に同じ本が登録されていたらスキップ
        if book_id not in calendar_data[day]:
            calendar_data[day][book_id] = {
                "id": history.book.id,
                "title": history.book.title,
                "image_url": history.book.image.url if history.book.image else ""
            }

    # 最後に JSON化用にリスト形式へ変換
    calendar_data = {day: list(books.values()) for day, books in calendar_data.items()}
    calendar_data_json = json.dumps(calendar_data, cls=DjangoJSONEncoder)

    # 最も読まれた絵本を取得
    book_counter = Counter([h.book.title for h in histories])
    most_read_title = book_counter.most_common(1)[0][0] if book_counter else None

    # 月間合計と子どもごとの読んだ回数
    monthly_total = histories.count()
    child_totals = defaultdict(int)
    for h in histories:
        child_totals[h.child.name] += 1

    # テンプレートに渡すデータ
    return render(request, "review.html", {
        "children": children,
        "selected_child_id": selected_child_id,
        "calendar_days": calendar_days,
        "calendar_data_json": calendar_data_json,  # ここで JSON 形式を渡す
        "current_date": current_date,
        "prev_month": {"year": prev_month.year, "month": prev_month.month},
        "next_month": {"year": next_month.year, "month": next_month.month},
        "read_history_json": read_history_json,
        "most_read_title": most_read_title,
        "monthly_total": monthly_total,
        "child_totals": dict(child_totals),
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
   
