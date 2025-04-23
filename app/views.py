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
        code = request.GET.get("code")  # ✅ 招待コードを取得
        form = SignupForm()
        return render(request, "signup.html", {"form": form, "code": code})  # ✅ 渡す

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

            # ✅ POSTからcodeを取得
            invite_code = request.POST.get("code")
            if invite_code:
                try:
                    inviter_profile = UserProfile.objects.get(invite_code=invite_code)
                    UserProfile.objects.create(user=user, invited_by=inviter_profile.user)
                except UserProfile.DoesNotExist:
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
from django.db.models import Count
import logging

logger = logging.getLogger(__name__)  # ログ出力用

@login_required
def favorite(request):
    user = get_related_user(request)
    selected_child_id = request.GET.get("child_id")
    selected_child = None

    if selected_child_id and selected_child_id.isdigit():
        selected_child = get_object_or_404(Child, id=selected_child_id, user=user)
        favorites = Favorite.objects.filter(user=user, child=selected_child)
        book_ids = favorites.values_list("book_id", flat=True)
    else:
        children = Child.objects.filter(user=user)
        total_children = children.count()

        # ✅ userを絞らず、childに基づいて「全員のお気に入り絵本」を抽出
        book_ids = (
            Favorite.objects.filter(child__in=children)
            .values("book")
            .annotate(child_count=Count("child", distinct=True))
            .filter(child_count=total_children)
            .values_list("book", flat=True)
        )

    # ✅ Bookのuserも絞らず
    books = Book.objects.filter(id__in=book_ids).order_by("-created_at")

    paginator = Paginator(books, 28)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    books_list = list(page_obj)
    book_rows = [books_list[i:i + 7] for i in range(0, len(books_list), 7)]

    return render(request, "favorite.html", {
        "books": page_obj,
        "book_rows": book_rows,
        "children": Child.objects.filter(user=user),
        "selected_child_id": selected_child_id,
        "page_obj": page_obj,
    })

@login_required
def more_read(request):
    user = get_related_user(request)
    child_id = request.GET.get("child_id")
    children = Child.objects.filter(user=user)
    selected_child_id = child_id if child_id else ""

    tooltip_counts = {}
    read_counts_dict = {}

    if child_id and child_id.isdigit():
        selected_child = get_object_or_404(Child, id=child_id, user=user)

        read_data = ReadCount.objects.filter(child__id=child_id, book__user=user)
        read_counts = (
            read_data.values("book")
            .annotate(total_reads=Sum("count"))
            .order_by("total_reads")
        )
        book_ids = [item["book"] for item in read_counts][:6]
        books = Book.objects.filter(id__in=book_ids, child=selected_child, user=user)
        read_counts_dict = {item["book"]: item["total_reads"] for item in read_counts}
        
    else:
        books = Book.objects.filter(user=user)[:6]
        tooltip_counts = {
            book.id: {child.name: 0 for child in children}
            for book in books
        }

        read_data = ReadCount.objects.filter(book__in=books, child__in=children)
        read_counts = (
            read_data.values("book", "child__name")
            .annotate(total_reads=Sum("count"))
        )

        for item in read_counts:
            book_id = item["book"]
            child_name = item["child__name"]
            count = item["total_reads"]
            if book_id in tooltip_counts and child_name in tooltip_counts[book_id]:
                tooltip_counts[book_id][child_name] = count

        read_counts_dict = {}

    return render(request, "more_read.html", {
        "books": books,
        "children": children,
        "selected_child_id": selected_child_id,
        "read_counts": read_counts_dict,
        "tooltip_counts": tooltip_counts,
    })

# ✅ 設定ページ
@login_required
def settings_view(request):
    user = request.user

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        email = request.POST.get('email', '').strip()

        if first_name:
            user.first_name = first_name
        if email:
            user.email = email
            user.username = email  # email を username として使う場合

        user.save()
        messages.success(request, "ユーザー情報を更新しました。")
        return redirect('settings')  # ✅ urls.py 側で name='settings' になっていることを確認

    # GETリクエスト：現在の情報を渡す（テンプレートでも使いやすく）
    return render(request, 'settings.html', {
        'user': user,
    })
# ✅ 絵本登録ページ（重複チェック付き）
@csrf_exempt
def add_book(request):
    related_user = get_related_user(request)

    if request.method == "POST":
        form = BookForm(request.POST, request.FILES or None)
        form.fields["children"].queryset = Child.objects.filter(user=related_user)

        if form.is_valid():
            title = form.cleaned_data["title"]
            selected_children = form.cleaned_data["children"]

            # ✅ 重複チェック（同じ子どもに同じタイトルが既にあるか）
            for child in selected_children:
                if Book.objects.filter(title=title, user=related_user, child=child).exists():
                    return JsonResponse({
                        "success": False,
                        "error": f"「{title}」はすでに {child.name} の本棚に登録されています。"
                    })

            book = form.save(commit=False)
            book.user = related_user
            book.save()
            book.child.set(selected_children)
            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "フォームが無効です", "errors": form.errors})
    
    else:

        form = BookForm()
        form.fields["children"].queryset = Child.objects.filter(user=related_user)

        selected_child_id = request.GET.get("child_id")
        children = Child.objects.filter(user=related_user)

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
    related_user = get_related_user(request)

    # ✅ ログインユーザー or 招待元のユーザーが所有する book のみ取得
    book = get_object_or_404(Book, id=book_id, user=related_user)

    # ✅ 関連する子ども（ManyToMany）で、招待元ユーザーに紐づくものだけ
    registered_children = book.child.filter(user=related_user)

    # ✅ お気に入り（child も関連ユーザーのものに限定）
    favorites = Favorite.objects.filter(user=related_user, book=book)
    favorited_child_ids = favorites.values_list('child_id', flat=True)

    # ✅ 読んだ回数（ログインユーザー or 招待元のユーザーの子ども）
    read_counts_qs = ReadCount.objects.filter(book=book, child__user=related_user)
    read_counts = {rc.child.id: rc.count for rc in read_counts_qs}

    # ✅ メモ（同上）
    memos_qs = Memo.objects.filter(book=book, child__user=related_user)
    memos = {memo.child.id: memo.content for memo in memos_qs}
    
    selected_child_id = request.GET.get("child_id")

    form = BookForm(instance=book)
    form.fields['children'].queryset = Child.objects.filter(user=related_user)
    form.initial['children'] = book.child.all()


    return render(request, 'book_detail.html', {
        'book': book,
        'registered_children': registered_children,
        'favorited_child_ids': list(favorited_child_ids),
        'read_counts': read_counts,
        'memos': memos,
        'selected_child_id': selected_child_id,
        'form': form,
    })

# ✅ 絵本削除ビュー

def delete_book(request, book_id):
    related_user = get_related_user(request)
    book = get_object_or_404(Book, id=book_id, user=related_user)

    if request.method == "POST":
        book.delete()
        
        return redirect('home')

    return render(request, "book_detail.html", {"book": book})



@login_required
def home_view(request):
    selected_child_id = request.GET.get("child_id")
    selected_child = None
    base_user = get_related_user(request)  

    children = Child.objects.filter(user=base_user).distinct()


    if selected_child_id and selected_child_id.isdigit():
        selected_child = get_object_or_404(Child, id=selected_child_id, user=base_user)
        books_qs = Book.objects.filter(child=selected_child, user=base_user)
    else:
        books_qs = Book.objects.filter(user=base_user).annotate(
            child_count=Count('child', distinct=True)
        ).filter(child_count=children.count())

    books_qs = books_qs.exclude(image='').exclude(image=None).order_by("-created_at")

    paginator = Paginator(books_qs, 28)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    books_list = list(page_obj)
    book_rows = [books_list[i:i+7] for i in range(0, len(books_list), 7)]

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
    related_user = get_related_user(request)
    book_id = request.POST.get("book_id")
    child_id = request.POST.get("child_id")
    content = request.POST.get("content")

    book = get_object_or_404(Book, id=book_id, user=related_user)
    child = get_object_or_404(Child, id=child_id, user=related_user)

    memo, created = Memo.objects.get_or_create(book=book, child=child)
    memo.content = content
    memo.save()

    return JsonResponse({"status": "ok", "content": memo.content})


# ✅ 子ども情報編集画面
@login_required
def child_edit(request): 
    storage = messages.get_messages(request)
    storage.used = True 
    
    user = get_related_user(request)
    children = Child.objects.filter(user=user)
    form = ChildForm()

    if request.method == "POST":
        if children.count() >= 3:
            messages.error(request, "子どもの登録は最大3人までです。")
        else:
            form = ChildForm(request.POST)
            if form.is_valid():
                child = form.save(commit=False)
                child.user = user
                child.save()
                messages.success(request, "子どもが登録されました。")
                return redirect('child_edit')

    return render(request, 'child_edit.html', {'children': children, 'form': form})

# ✅ 子ども追加処理
from django.contrib.auth.decorators import login_required

@login_required
def child_add(request):
    user = get_related_user(request)
    existing_children = Child.objects.filter(user=user)

    if existing_children.count() >= 3:
        messages.error(request, "※ 子どもの登録は最大3人までです。")
        return redirect("child_edit")

    if request.method == "POST":
        form = ChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.user = user
            child.save()
            return redirect("child_edit")
    else:
        form = ChildForm()

    return render(request, "child_edit.html", {
        "form": form,
        "children": existing_children,
        "max_children": 3
    })

# ✅ お気に入り
@csrf_exempt
@login_required
def toggle_favorite(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"favorited": False, "error": "ログインが必要です"})

        related_user = get_related_user(request)
        data = json.loads(request.body)
        book_id = data.get("book_id")
        child_id = data.get("child_id")

        try:
            book = Book.objects.get(id=book_id, user=related_user)
            child = Child.objects.get(id=child_id, user=related_user)
        except (Book.DoesNotExist, Child.DoesNotExist):
            return JsonResponse({"favorited": False, "error": "該当データなし"})

        favorite, created = Favorite.objects.get_or_create(user=request.user, book=book, child=child)

        if not created:
            favorite.delete()
            return JsonResponse({"favorited": False})
        else:
            return JsonResponse({"favorited": True})

    return JsonResponse({"error": "Invalid request"}, status=400)


# ✅ こども情報編集画面

def child_update(request, child_id):
    related_user = get_related_user(request)
    child = get_object_or_404(Child, id=child_id, user=related_user)

    if request.method == "POST":
        form = ChildForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            return redirect('child_edit')
    else:
        form = ChildForm(instance=child)
    return render(request, 'child_update.html', {'form': form})


def child_delete(request, child_id):
    related_user = get_related_user(request)
    child = get_object_or_404(Child, id=child_id, user=related_user)

    if request.method == "POST":
        child.delete()
        return redirect('child_edit')
    return render(request, 'child_delete_confirm.html', {'child': child})



# ✅ よんだ回数
@require_POST
@login_required
def increment_read_count(request):
    related_user = get_related_user(request)
    book_id = request.POST.get("book_id")
    child_id = request.POST.get("child_id")

    book = get_object_or_404(Book, id=book_id, user=related_user)
    child = get_object_or_404(Child, id=child_id, user=related_user)

    read_count, _ = ReadCount.objects.get_or_create(book=book, child=child)
    read_count.count += 1
    read_count.save()

    ReadHistory.objects.create(book=book, child=child)

    return JsonResponse({"count": read_count.count})

# ✅ もっとよんでページ

@login_required
def edit_book(request, book_id):
    related_user = get_related_user(request)
    book = get_object_or_404(Book, id=book_id, user=related_user)

    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, instance=book)
        form.fields['children'].queryset = Child.objects.filter(user=related_user)
        if form.is_valid():
            book = form.save()
            book.child.set(form.cleaned_data['children'])  # 子どもとの紐づけを更新
            return redirect("book_detail", book_id=book.id)
    else:
        pass 
        
        return redirect("book_detail", book_id=book.id)



# ✅ 家族招待
@login_required
def family_invite(request):
    profile = request.user.userprofile

    # invite_code の自動生成（念のため）
    if not profile.invite_code:
        profile.invite_code = profile.generate_invite_code()
        profile.save()

    invite_url = request.build_absolute_uri(f"/signup/?code={profile.invite_code}")

     # ✅ 自分を除いた招待ユーザーだけ取得
    invited_users = User.objects.filter(userprofile__invited_by=request.user)
    invited_users_excluding_self = invited_users.exclude(id=request.user.id)

    inviter = profile.invited_by if profile.invited_by else None

    return render(request, 'family_invite.html', {
        'invite_url': invite_url,
        'invited_users_excluding_self': invited_users_excluding_self, 
        'inviter': inviter,  
    })

# ✅ 検索結果ページ
def search_results(request):
    query = request.GET.get("q")
    related_user = get_related_user(request)
    results = []

    if query:
        results = Book.objects.filter(
            Q(user=related_user), 
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
    data = json.loads(request.body)
    book_id = data.get("book_id")
    child_id = data.get("child_id")
    user = get_related_user(request)

    try:
        book = Book.objects.get(id=book_id, user=user)
        child = Child.objects.get(id=child_id, user=user)
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
    user = get_related_user(request)
    selected_child_id = request.GET.get("child_id")
    selected_child = None
    children = Child.objects.filter(user=user)

    if selected_child_id:
        selected_child = get_object_or_404(Child, id=selected_child_id, user=user)

    current_date = date(year, month, 1)
    days_in_month = calendar.monthrange(year, month)[1]
    calendar_days = list(range(1, days_in_month + 1))
    prev_month = current_date - timedelta(days=1)
    next_month = (current_date + timedelta(days=days_in_month)).replace(day=1)

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
            child__user=user
        ).select_related('book')

    calendar_data = defaultdict(dict)
    for history in histories:
        day = history.date.day
        book_id = history.book.id
        if book_id not in calendar_data[day]:
            calendar_data[day][book_id] = {
                "id": history.book.id,
                "title": history.book.title,
                "image_url": history.book.image.url if history.book.image else ""
            }

    calendar_data = {day: list(books.values()) for day, books in calendar_data.items()}
    calendar_data_json = json.dumps(calendar_data, cls=DjangoJSONEncoder)

    read_history_json = json.dumps([{
        "date": str(h.date),
        "title": h.book.title
    } for h in histories], cls=DjangoJSONEncoder)

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
        "calendar_data_json": calendar_data_json,
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
    data = json.loads(request.body)
    book_id = data.get("book_id")
    child_id = data.get("child_id")
    related_user = get_related_user(request)

    try:
        book = Book.objects.get(id=book_id, user=related_user)
        child = Child.objects.get(id=child_id, user=related_user)
        read_count, _ = ReadCount.objects.get_or_create(book=book, child=child)

        if read_count.count > 0:
            read_count.count -= 1
            read_count.save()

        return JsonResponse({"success": True, "count": read_count.count})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

@login_required
def logout_confirm_view(request):
    return render(request, 'logout_confirm.html')

def get_related_user(request):
    if hasattr(request.user, 'userprofile') and request.user.userprofile.invited_by:
        return request.user.userprofile.invited_by
    return request.user


from django.views.decorators.http import require_POST
from django.http import JsonResponse

@require_POST
@login_required
def remove_child_from_book(request):
    book_id = request.POST.get('book_id')
    child_id = request.POST.get('child_id')
    user = get_related_user(request)

    try:
        book = Book.objects.get(id=book_id, user=user)
        child = Child.objects.get(id=child_id, user=user)
        book.child.remove(child)
        return JsonResponse({'success': True})
    except Book.DoesNotExist or Child.DoesNotExist:
        return JsonResponse({'success': False, 'error': '対象が見つかりません'})
