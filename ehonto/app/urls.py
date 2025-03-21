from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # ✅ views モジュール全体をインポート
from .views import (
    HomeView, book_detail, delete_book, add_book,
    child_edit, child_add, child_bookshelf,
    favorite, review, more_read,
    settings_view, family_invite,
    signup_view, save_memo
)


urlpatterns = [
    # ✅ お気に入り・履歴ページ
    path('favorite/', views.favorite, name='favorite'),
    path('review/', views.review, name='review'),
    path('more_read/', views.more_read, name='more_read'),

    # ✅ 設定・家族招待
    path('settings/', views.settings_view, name='settings_view'),
    path('family_invite/', views.family_invite, name='family_invite'),

    # ✅ パスワード変更関連
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),

    # ✅ 認証関連
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('signup/', views.signup_view, name='signup'),

    # ✅ ホーム & 絵本登録
    path('home/', views.HomeView.as_view(), name='home'),
    path('', views.HomeView.as_view(), name='home'),  # `/` でホーム画面にアクセス
    path('add_book/', views.add_book, name='add_book'),

    # ✅ 子どもの本棚ページ（修正）
    path('bookshelf/<int:child_id>/', views.child_bookshelf, name='child_bookshelf'),

    # ✅ 絵本の詳細 & 削除
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('book/<int:book_id>/delete/', views.delete_book, name='delete_book'),

    # ✅ 子ども情報編集・追加
    path('child/edit/', views.child_edit, name='child_edit'),
    path('child/add/', views.child_add, name='child_add'),

    # ✅ メモ
    path('save_memo/', views.save_memo, name='save_memo'),
]

# ✅ メディアファイルの配信設定（画像を正しく表示するために必要）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
