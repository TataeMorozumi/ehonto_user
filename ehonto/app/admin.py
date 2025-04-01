from django.contrib import admin
from .models import Book  # ✅ Bookモデルをインポート


@admin.register(Book)  # ✅ adminサイトにBookを登録
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'image', 'created_at')  # ✅ 一覧表示するフィールド
from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile

# ✅ インライン表示設定（fk_name を指定）
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fk_name = 'user'  # ←ここがポイント！

# ✅ User 管理画面を拡張
class CustomUserAdmin(admin.ModelAdmin):
    inlines = (UserProfileInline,)

# ✅ 既存の User を再登録
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
