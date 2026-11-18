from django.contrib.auth.models import User
from django.core.management import call_command

from posts.models import Post, Comment
from users.models import Follow


def test_seed_demo_creates_users_posts_and_activity(demo_data):
    assert User.objects.count() == 4
    assert Post.objects.count() == 8
    assert Follow.objects.count() == 7
    assert Comment.objects.count() == 6
    asha = User.objects.get(username="asha")
    assert asha.check_password("photonest-demo")
    assert asha.profile.bio


def test_seed_demo_does_not_create_duplicates(demo_data):
    call_command("seed_demo", verbosity=0)
    assert User.objects.count() == 4


def test_seed_demo_reset_recreates_the_data(demo_data):
    Post.objects.all().delete()
    call_command("seed_demo", "--reset", verbosity=0)
    assert Post.objects.count() == 8
