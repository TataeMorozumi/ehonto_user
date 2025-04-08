from django.apps import AppConfig


class AppCustomConfig(AppConfig):  # ✅ クラス名をユニークに
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
