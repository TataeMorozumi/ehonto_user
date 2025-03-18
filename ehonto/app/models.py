from django.db import models
from django.utils.timezone import now  # 追加

class Child(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=now)  # ✅ デフォルトを追加

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    image = models.ImageField(upload_to="book_images/", null=True, blank=True)  # ✅ NULL を許可
    created_at = models.DateTimeField(auto_now_add=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE, null=True, blank=True, related_name="books")
   
    def __str__(self):
        return self.title