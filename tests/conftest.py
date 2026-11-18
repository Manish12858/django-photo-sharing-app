import io
import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from PIL import Image

# Playwright's sync API runs an event loop in the test thread; allow Django ORM calls there.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

PASSWORD = "Str0ng-pass-123"


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Save uploaded files in a temporary folder instead of the project's media/ folder."""
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.MEDIA_ROOT


def image_file(name="photo.png", size=(60, 40), image_format="PNG", noise=False):
    """An uploaded image file created in memory."""
    if noise:
        image = Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3))
    else:
        image = Image.new("RGB", size, (244, 63, 94))
    buffer = io.BytesIO()
    image.save(buffer, format=image_format)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{image_format.lower()}")


@pytest.fixture
def make_user(db, django_user_model):
    def _make(username, **extra):
        from users.models import Profile

        user = django_user_model.objects.create_user(
            username=username, email=f"{username}@example.com", password=PASSWORD, **extra
        )
        Profile.objects.create(user=user)
        return user

    return _make


@pytest.fixture
def user(make_user):
    return make_user("asha")


@pytest.fixture
def other_user(make_user):
    return make_user("ravi")


@pytest.fixture
def logged_in_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def make_post(db):
    def _make(author, title="Sunset", caption=""):
        from posts.models import Post

        return Post.objects.create(user=author, title=title, caption=caption, image=image_file())

    return _make


@pytest.fixture
def demo_data(db):
    call_command("seed_demo", verbosity=0)
