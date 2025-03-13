from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # ✅ views モジュール全体をインポート

urlpatterns = [
    path('favorite/', views.favorite, name='favorite'),
    path('review/', views.review, name='review'),
    path('more_read/', views.more_read, name='more_read'),
    path('settings/', views.settings_view, name='settings_view'),  # ✅ `settings_view` を修正
    path('family_invite/', views.family_invite, name='family_invite'),
    path('add/', views.add_book, name='add_book'),

    # ✅ パスワード変更関連
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),

    # ✅ 認証関連
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('signup/', views.signup_view, name='signup'),

    # ✅ ホーム & 絵本登録
    path('home/', views.home_view, name='home'),  # ✅ `/home/` でもアクセス可能
    path('add_book/', views.add_book, name='add_book'),

    # ✅ デフォルトのルート（`/` にアクセスするとホーム画面）
    path('', views.home_view, name='home'),
]

# ✅ メディアファイルの配信設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
