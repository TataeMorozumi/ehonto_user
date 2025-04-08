from django.apps import AppConfig


class EhontoAppConfig(AppConfig): # ✅ クラス名をユニークに
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
