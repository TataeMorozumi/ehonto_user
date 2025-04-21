from django.db import models
from django.utils.timezone import now 
from django.contrib.auth.models import User
import secrets
import string 

class Child(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # null=True を削除
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=now)  # ✅ デフォルトを追加

    def __str__(self):
        return self.name


class Book(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        default=User.objects.get(id=1).id  # ここでデフォルトのユーザーを設定
    )
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='book_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    child = models.ManyToManyField(Child, related_name="books")  # ✅ ここだけでOK

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return ""

    def __str__(self):
        return self.title

class Memo(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="memos")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="memos")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.child.name} のメモ: {self.book.title}"    
    

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'book', 'child')

class ReadCount(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('child', 'book')

        def __str__(self):
            return f"{self.child.name} - {self.book.title}: {self.count}回"
        
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invited_users')
    invite_code = models.CharField(max_length=50, unique=True, blank=True, null=True)  # ✅ 追加

    def __str__(self):
        return self.user.username

    def generate_invite_code(self, length=24):
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)

class ReadHistory(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
  