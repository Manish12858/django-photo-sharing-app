import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def fill_comment_authors(apps, schema_editor):
    """Link existing comments to users using the old `posted_by` username."""
    Comment = apps.get_model('posts', 'Comment')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    for comment in Comment.objects.all():
        user = User.objects.filter(username=comment.posted_by).first()
        if user is None:
            comment.delete()  # the author no longer exists
        else:
            comment.author = user
            comment.save(update_fields=['author'])


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Comments: store a link to the user instead of a copy of the username
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(fill_comment_authors, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveField(
            model_name='comment',
            name='posted_by',
        ),
        migrations.AlterField(
            model_name='comment',
            name='body',
            field=models.CharField(max_length=300),
        ),
        migrations.AlterField(
            model_name='comment',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        # Posts: keep the time (not just the date), drop the unused slug
        migrations.RemoveField(
            model_name='post',
            name='slug',
        ),
        migrations.AlterField(
            model_name='post',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posts',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-created', '-id']},
        ),
    ]
