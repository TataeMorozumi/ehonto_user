from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    image = models.ImageField(upload_to='book_images/', blank=True, null=True)  # ✅ 画像フィールドを追加
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
