import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='child',
            name='user',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.CASCADE,
                null=True  # ✅ default は削除し、null を許容する形に変更
            ),
        ),
        migrations.AlterField(
            model_name='book',
            name='child',
            field=models.ManyToManyField(related_name='books', to='app.child'),
        ),
    ]
