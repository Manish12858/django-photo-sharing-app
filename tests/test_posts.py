from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from PIL import Image

from posts.models import Post, Comment
from users.models import Follow
from tests.conftest import image_file


# ---------- creating and deleting posts ----------

def test_create_post_requires_login(client, db):
    response = client.get(reverse("create"))
    assert response.url == f"{reverse('login')}?next={reverse('create')}"


def test_create_post(logged_in_client, user):
    response = logged_in_client.post(reverse("create"), {"title": "Hello", "caption": "First post", "image": image_file()})
    post = Post.objects.get()
    assert response.url == post.get_absolute_url()
    assert post.user == user
    assert post.image.name.startswith("post_images/")


def test_large_photos_are_resized(logged_in_client, settings):
    logged_in_client.post(reverse("create"), {"title": "Big", "image": image_file(size=(3000, 1500))})
    with Image.open(Post.objects.get().image.path) as saved:
        assert saved.size == (settings.MAX_IMAGE_DIMENSION, 540)


def test_small_photos_are_kept_as_they_are(logged_in_client):
    logged_in_client.post(reverse("create"), {"title": "Small", "image": image_file(size=(300, 200))})
    with Image.open(Post.objects.get().image.path) as saved:
        assert saved.size == (300, 200)


def test_files_over_the_size_limit_are_rejected(logged_in_client, settings):
    settings.MAX_UPLOAD_SIZE_MB = 0.01  # 10 KB, so a small noisy image is "too big"
    response = logged_in_client.post(reverse("create"), {"title": "Huge", "image": image_file(size=(200, 200), noise=True)})
    assert response.status_code == 200
    assert "smaller than" in response.text
    assert not Post.objects.exists()


def test_non_images_are_rejected(logged_in_client):
    from django.core.files.uploadedfile import SimpleUploadedFile

    fake = SimpleUploadedFile("notes.png", b"not really an image", content_type="image/png")
    response = logged_in_client.post(reverse("create"), {"title": "Fake", "image": fake})
    assert response.status_code == 200
    assert not Post.objects.exists()


def test_users_can_delete_only_their_own_posts(logged_in_client, user, other_user, make_post):
    mine, theirs = make_post(user), make_post(other_user)
    assert logged_in_client.post(reverse("post_delete", args=[theirs.id])).status_code == 404
    response = logged_in_client.post(reverse("post_delete", args=[mine.id]))
    assert response.url == reverse("profile", args=["asha"])
    assert list(Post.objects.all()) == [theirs]


# ---------- feed ----------

def test_feed_requires_login(client, db):
    assert client.get(reverse("feed")).status_code == 302


def test_following_feed_shows_own_posts_and_people_you_follow(logged_in_client, user, other_user, make_user, make_post):
    stranger = make_user("kabir")
    make_post(user, "Mine")
    make_post(other_user, "Followed")
    make_post(stranger, "Stranger")
    Follow.objects.create(follower=user, following=other_user)

    following = logged_in_client.get(reverse("feed"))
    explore = logged_in_client.get(reverse("feed") + "?tab=all")

    assert {p.title for p in following.context["page"]} == {"Mine", "Followed"}
    assert {p.title for p in explore.context["page"]} == {"Mine", "Followed", "Stranger"}


def test_feed_is_paginated_newest_first(logged_in_client, user, make_post):
    for number in range(8):
        make_post(user, f"Post {number}")
    first_page = logged_in_client.get(reverse("feed"))
    second_page = logged_in_client.get(reverse("feed") + "?page=2")
    assert [p.title for p in first_page.context["page"]] == [f"Post {n}" for n in range(7, 1, -1)]
    assert [p.title for p in second_page.context["page"]] == ["Post 1", "Post 0"]


def test_feed_suggests_people_to_follow(logged_in_client, user, other_user, make_user):
    make_user("kabir")
    Follow.objects.create(follower=user, following=other_user)
    response = logged_in_client.get(reverse("feed"))
    assert [person.username for person in response.context["suggestions"]] == ["kabir"]


def test_feed_query_count_does_not_grow_with_more_posts(logged_in_client, user, other_user, make_post):
    """Guards against the N+1 query problem: 6 posts must not need more queries than 2."""
    def feed_queries():
        with CaptureQueriesContext(connection) as queries:
            logged_in_client.get(reverse("feed"))
        return len(queries)

    for number in range(2):
        post = make_post(user, f"Post {number}")
        post.liked_by.add(other_user)
        Comment.objects.create(post=post, author=other_user, body="Nice")
    with_two_posts = feed_queries()

    for number in range(2, 6):
        post = make_post(user, f"Post {number}")
        post.liked_by.add(other_user)
        Comment.objects.create(post=post, author=other_user, body="Nice")
    assert feed_queries() == with_two_posts


# ---------- post page ----------

def test_post_page_is_public(client, user, make_post):
    post = make_post(user, "Public sunset", caption="Look at this")
    response = client.get(post.get_absolute_url())
    assert response.status_code == 200
    assert "Public sunset" in response.text
    assert "Log in</a> to like and comment" in response.text


def test_unknown_post_returns_404(client, db):
    assert client.get("/posts/999/").status_code == 404


# ---------- likes ----------

def test_like_and_unlike(logged_in_client, user, other_user, make_post):
    post = make_post(other_user)
    url = reverse("like", args=[post.id])
    ajax = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

    assert logged_in_client.post(url, **ajax).json() == {"liked": True, "count": 1}
    assert logged_in_client.post(url, **ajax).json() == {"liked": False, "count": 0}


def test_like_requires_post_and_existing_post(logged_in_client, user, make_post):
    post = make_post(user)
    assert logged_in_client.get(reverse("like", args=[post.id])).status_code == 405
    assert logged_in_client.post(reverse("like", args=[999])).status_code == 404


def test_like_count_text_is_consistent(logged_in_client, user, other_user, make_post):
    post = make_post(user)
    post.liked_by.add(other_user)
    response = logged_in_client.get(post.get_absolute_url())
    assert "1 like</p>" in response.text


# ---------- comments ----------

def test_add_comment(logged_in_client, user, other_user, make_post):
    post = make_post(other_user)
    response = logged_in_client.post(reverse("add_comment", args=[post.id]), {"body": "Great shot", "next": "/posts/feed/"})
    assert response.url == f"/posts/feed/#post-{post.id}"
    comment = Comment.objects.get()
    assert (comment.author, comment.body) == (user, "Great shot")


def test_empty_comment_is_rejected(logged_in_client, user, make_post):
    post = make_post(user)
    logged_in_client.post(reverse("add_comment", args=[post.id]), {"body": ""})
    assert not Comment.objects.exists()


def test_comment_redirect_ignores_external_next_url(logged_in_client, user, make_post):
    post = make_post(user)
    response = logged_in_client.post(reverse("add_comment", args=[post.id]), {"body": "Hi", "next": "https://evil.example.com/"})
    assert response.url == f"{post.get_absolute_url()}#post-{post.id}"


def test_comment_can_be_deleted_by_its_author_and_the_post_owner_only(client, user, other_user, make_user, make_post):
    stranger = make_user("kabir")
    post = make_post(user)
    first = Comment.objects.create(post=post, author=other_user, body="by ravi")
    second = Comment.objects.create(post=post, author=other_user, body="also by ravi")

    client.force_login(stranger)
    client.post(reverse("comment_delete", args=[first.id]))
    assert Comment.objects.count() == 2

    client.force_login(other_user)  # comment author
    client.post(reverse("comment_delete", args=[first.id]))
    client.force_login(user)  # post owner
    client.post(reverse("comment_delete", args=[second.id]))
    assert Comment.objects.count() == 0
