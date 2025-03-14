from django.contrib import admin
from .models import Book  # ✅ Bookモデルをインポート

@admin.register(Book)  # ✅ adminサイトにBookを登録
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'image', 'created_at')  # ✅ 一覧表示するフィールド
