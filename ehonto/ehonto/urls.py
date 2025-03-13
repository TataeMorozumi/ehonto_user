"""
URL configuration for ehonto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from app.views import PortfolioView, SignupView, LoginView, HomeView, settings_view
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('portfolio/', PortfolioView.as_view(), name="portfolio"),  # ✅ ポートフォリオをデフォルトページに設定
    path('signup/', SignupView.as_view(), name="signup"),  # ✅ 新規登録ページ
    path('login/', LoginView.as_view(), name="login"),  # ✅ ログインページ
    path('', HomeView.as_view(), name="home"),  # ✅ `/home/` にアクセスできるようにする
    path('settings/', settings_view, name="settings_view"),
    path('', include('app.urls')),  # ✅ `app/urls.py` でURLを管理

    # ✅ Django標準のログイン・ログアウト
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

# ✅ メディアファイルの配信設定
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
