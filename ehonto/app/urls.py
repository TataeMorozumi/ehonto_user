from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # ✅ views モジュール全体をインポート
from .views import HomeView, book_detail, delete_book, add_book

urlpatterns = [
    path('favorite/', views.favorite, name='favorite'),
    path('review/', views.review, name='review'),
    path('more_read/', views.more_read, name='more_read'),
    path('settings/', views.settings_view, name='settings_view'),  # ✅ 設定画面
    path('family_invite/', views.family_invite, name='family_invite'),

    # ✅ パスワード変更関連
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),

    # ✅ 認証関連
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('signup/', views.signup_view, name='signup'),

    # ✅ ホーム & 絵本登録
    path('home/', HomeView.as_view(), name='home'),  # `/home/` でアクセス可能
    path('', HomeView.as_view(), name='home'),  # `/` にアクセスしたときホーム画面を表示
    path('add_book/', add_book, name='add_book'),  # ✅ `add_book` のURLを `/add_book/` に修正


    # ✅ 詳細ページ & 削除
    path('book/<int:book_id>/', views.book_detail, name='book_detail'), 
    path('book/<int:book_id>/delete/', views.delete_book, name='delete_book'),  # ✅ 統一

]

# ✅ メディアファイルの配信設定（画像を正しく表示するために必要）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
