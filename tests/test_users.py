from django.contrib.auth.models import User
from django.urls import reverse
from PIL import Image

from users.models import Follow, Profile
from tests.conftest import PASSWORD, image_file

REGISTRATION = {
    "username": "neha", "email": "neha@example.com", "first_name": "Neha",
    "password": PASSWORD, "password2": PASSWORD,
}


# ---------- registration and login ----------

def test_register_creates_profile_and_logs_in(client, db):
    response = client.post(reverse("register"), REGISTRATION)
    assert response.url == reverse("feed") + "?tab=all"
    user = User.objects.get(username="neha")
    assert Profile.objects.filter(user=user).exists()
    assert client.session["_auth_user_id"] == str(user.id)


def test_register_validates_passwords_and_email(client, user):
    mismatch = client.post(reverse("register"), {**REGISTRATION, "password2": "Different-pass-1"})
    assert "Passwords do not match" in mismatch.text
    duplicate = client.post(reverse("register"), {**REGISTRATION, "email": "ASHA@example.com"})
    assert "already exists" in duplicate.text
    missing = client.post(reverse("register"), {**REGISTRATION, "email": ""})
    assert missing.status_code == 200
    assert not User.objects.filter(username="neha").exists()


def test_login_redirects_to_next_page(client, user):
    response = client.post(reverse("login") + "?next=/posts/create/", {"username": "asha", "password": PASSWORD, "next": "/posts/create/"})
    assert response.url == "/posts/create/"


def test_login_ignores_external_next_url(client, user):
    response = client.post(reverse("login"), {"username": "asha", "password": PASSWORD, "next": "https://evil.example.com/"})
    assert response.url == reverse("feed")


def test_login_with_wrong_password(client, user):
    response = client.post(reverse("login"), {"username": "asha", "password": "wrong"})
    assert "Invalid username or password" in response.text
    assert "_auth_user_id" not in client.session


def test_logout_only_accepts_post(logged_in_client):
    assert logged_in_client.get(reverse("logout")).status_code == 405
    response = logged_in_client.post(reverse("logout"))
    assert response.url == reverse("login")
    assert "_auth_user_id" not in logged_in_client.session


# ---------- profiles ----------

def test_profile_page_is_public_and_shows_counts(client, user, other_user, make_post):
    make_post(user, "One")
    make_post(user, "Two")
    Follow.objects.create(follower=other_user, following=user)
    response = client.get(reverse("profile", args=["asha"]))
    assert response.status_code == 200
    assert response.context["person"].follower_count == 1
    assert response.context["person"].following_count == 0
    assert len(response.context["posts"]) == 2


def test_unknown_profile_returns_404(client, db):
    assert client.get(reverse("profile", args=["nobody"])).status_code == 404


def test_my_profile_link_redirects_to_own_profile(logged_in_client):
    assert logged_in_client.get(reverse("index")).url == reverse("profile", args=["asha"])


def test_edit_profile_updates_bio_and_resizes_photo(logged_in_client, user):
    response = logged_in_client.post(reverse("edit"), {
        "first_name": "Asha", "last_name": "Verma", "email": "asha@example.com",
        "bio": "Sunset chaser", "photo": image_file(size=(1200, 900)),
    })
    assert response.url == reverse("profile", args=["asha"])
    profile = Profile.objects.get(user=user)
    assert profile.bio == "Sunset chaser"
    with Image.open(profile.photo.path) as photo:
        assert max(photo.size) == 400


def test_edit_profile_rejects_email_used_by_someone_else(logged_in_client, other_user):
    response = logged_in_client.post(reverse("edit"), {"first_name": "", "last_name": "", "email": "ravi@example.com", "bio": ""})
    assert "already exists" in response.text


# ---------- following ----------

def test_follow_and_unfollow(logged_in_client, user, other_user):
    url = reverse("follow", args=["ravi"])
    assert logged_in_client.post(url).url == reverse("profile", args=["ravi"])
    assert Follow.objects.filter(follower=user, following=other_user).exists()
    logged_in_client.post(url)
    assert not Follow.objects.exists()


def test_cannot_follow_yourself(logged_in_client):
    logged_in_client.post(reverse("follow", args=["asha"]))
    assert not Follow.objects.exists()


def test_follow_requires_login_and_post(client, logged_in_client, other_user):
    assert logged_in_client.get(reverse("follow", args=["ravi"])).status_code == 405
    client.logout()
    response = client.post(reverse("follow", args=["ravi"]))
    assert response.url.startswith(reverse("login"))


# ---------- search and password reset ----------

def test_search_people_by_username_or_name(logged_in_client, make_user):
    make_user("meera", first_name="Meera")
    make_user("kabir", first_name="Kabir")
    by_name = logged_in_client.get(reverse("search"), {"q": "meer"})
    assert [person.username for person in by_name.context["people"]] == ["meera"]
    nothing = logged_in_client.get(reverse("search"), {"q": "zzz"})
    assert "No people found" in nothing.text


def test_password_reset_sends_email(client, user, mailoutbox):
    response = client.post(reverse("password_reset"), {"email": "asha@example.com"})
    assert response.url == reverse("password_reset_done")
    assert len(mailoutbox) == 1


def test_account_pages_render(client, db):
    for name in ["login", "register", "password_reset", "password_reset_done", "password_reset_complete"]:
        assert client.get(reverse(name)).status_code == 200, name
