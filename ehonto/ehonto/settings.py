"""
Django settings for ehonto project.
"""

from pathlib import Path
import os
import sys


# ✅ BASE_DIR の定義
BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.append(str(BASE_DIR.parent / "app"))
# ✅ セキュリティキー（本番環境では .env ファイルなどに保存する）
SECRET_KEY = 'django-insecure-)8jk-b))n$x$f1cpgotan-4f^9h@&rk^(4x2yc$air1vgxhz*!'

# ✅ 開発モード（本番では False に変更）
DEBUG = False

ALLOWED_HOSTS = ['tatae.pythonanywhere.com']

# ✅ アプリケーションの登録
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app.apps.EhontoAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ehonto.urls'

# ✅ テンプレート設定
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "app/templates"],

        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION =  'ehonto.ehonto.wsgi.application'

# ✅ データベース設定（SQLite）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / "db.sqlite3"),
    }
}

# ✅ 認証設定
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ✅ 言語・タイムゾーン
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# ✅ 静的ファイル（CSS, JS, 画像）設定
STATIC_URL = '/static/'  # ✅ スラッシュを修正

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'app/static'),

]

# ✅ 本番環境用（collectstatic の保存先）

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ✅ メディアファイル（画像アップロード用）
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ✅ 認証関連
LOGIN_URL = '/login/'  # ログインページ
LOGIN_REDIRECT_URL = '/app/home/'  # ログイン後にリダイレクトするページ
LOGOUT_REDIRECT_URL = '/app/login/'  # ログアウト後にリダイレクトするページ

SITE_DOMAIN = 'https://tatae.pythonanywhere.com'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # すでにあるロガーを無効にしない
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,  # 標準出力に表示（PythonAnywhereのログに表示されます）
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',  # ← これでSQLクエリが出る
            'handlers': ['console'],
        },
    },
}

