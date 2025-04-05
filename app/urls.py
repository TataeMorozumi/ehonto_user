from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # ✅ views モジュール全体をインポート
from .views import (
    SignupView, LoginView, HomeView, book_detail, delete_book, add_book,
    child_edit, child_add, child_bookshelf,
    favorite, review, more_read,
    settings_view, family_invite,
    signup_view, save_memo, home_view,  # signup_viewを追加、SignupViewは削除
)



urlpatterns = [
    # ✅ お気に入り・履歴ページ
    path('favorite/', views.favorite, name='favorite'),
    path('more_read/', views.more_read, name='more_read'),

    # ✅ 設定・家族招待
    path('settings/', views.settings_view, name='settings_view'),
    path('family_invite/', views.family_invite, name='family_invite'),

    # ✅ パスワード変更関連
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),

    # ✅ 認証関連
    path("signup/", SignupView.as_view(), name="signup"),

    # ✅ ホーム & 絵本登録
    path('', home_view, name='home'),  
    path('home/', home_view, name='home_alt'),  
    path('add_book/', views.add_book, name='add_book'),

    # ✅ 子どもの本棚ページ（修正）
    path('bookshelf/<int:child_id>/', views.child_bookshelf, name='child_bookshelf'),

    # ✅ 絵本の詳細 & 削除
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('book/<int:book_id>/delete/', views.delete_book, name='delete_book'),
    path("book/<int:book_id>/edit/", views.edit_book, name="edit_book"),

    # ✅ 子ども情報編集・追加
    path('child/edit/', views.child_edit, name='child_edit'),
    path('child/add/', views.child_add, name='child_add'),
    path('child/<int:child_id>/edit/', views.child_update, name='child_update'),
    path('child/<int:child_id>/delete/', views.child_delete, name='child_delete'),


    # ✅ メモ
    path('save_memo/', views.save_memo, name='save_memo'),

    # ✅ お気に入り
    path('toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),

    # ✅ よんだ回数
    path('increment_read_count/', views.increment_read_count, name='increment_read_count'),

    # ✅ 検索結果ページ
    path("search/", views.search_results, name="search_results"),
    
    # ✅ －ボタン
    path('decrement_read_count/', views.decrement_read_count, name='decrement_read_count'),

    # ✅ ふりかえり画面
    path("review/<int:year>/<int:month>/", views.review, name="review"),
    path("review/", views.review_default, name="review_default"),

    # ✅ ログインビューの追加
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
]

# ✅ メディアファイルの配信設定（画像を正しく表示するために必要）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



