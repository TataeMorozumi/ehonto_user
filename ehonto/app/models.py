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
    child = models.ManyToManyField(Child, blank=True, related_name="books")  # ✅ 多対多に変更
   
    def __str__(self):
        return self.title

class Memo(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="memos")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="memos")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.child.name} のメモ: {self.book.title}"    