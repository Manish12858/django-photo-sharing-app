import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='bio',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('follower', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='following_set',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('following', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='follower_set',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('follower', 'following'), name='unique_follow'),
                    models.CheckConstraint(condition=~models.Q(follower=models.F('following')), name='no_self_follow'),
                ],
            },
        ),
    ]
