"""End-to-end test of the main user journey in a real browser (Playwright + Django live server).

Run:  pytest -m e2e            (headless)
      pytest -m e2e --headed   (watch the browser)
Set SCREENSHOTS_DIR=docs/screenshots to also save the README screenshots.
"""
import os
import re
from pathlib import Path

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import Page, expect  # noqa: E402

from posts.models import Post  # noqa: E402
from users.models import Follow  # noqa: E402

pytestmark = pytest.mark.e2e

SCREENSHOTS_DIR = os.environ.get("SCREENSHOTS_DIR")
PASSWORD = "Str0ng-pass-123"
PHOTO = Path(__file__).resolve().parents[2] / "posts" / "demo_photos" / "lake-evening.jpg"


@pytest.fixture
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1280, "height": 900}}


def screenshot(page: Page, name: str):
    if not SCREENSHOTS_DIR:
        return
    Path(SCREENSHOTS_DIR).mkdir(parents=True, exist_ok=True)
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(Path(SCREENSHOTS_DIR) / f"{name}.png"))


def test_new_user_can_follow_like_comment_and_post(page: Page, live_server, demo_data):
    base = live_server.url

    # Sign up: the user is logged in and sees everyone's photos
    page.goto(f"{base}/users/register/")
    page.fill("#id_username", "neha")
    page.fill("#id_email", "neha@example.com")
    page.fill("#id_first_name", "Neha")
    page.fill("#id_password", PASSWORD)
    page.fill("#id_password2", PASSWORD)
    page.get_by_role("button", name="Sign up").click()
    expect(page.get_by_text("Welcome to PhotoNest, neha!")).to_be_visible()
    expect(page.get_by_test_id("post-card")).to_have_count(6)  # first page of the Explore tab
    screenshot(page, "3-explore")

    # Open Asha's profile and follow her
    page.get_by_test_id("suggestion").filter(has_text="asha").get_by_role("link", name="asha").click()
    expect(page.get_by_role("heading", name="asha")).to_be_visible()
    expect(page.get_by_test_id("follower-count")).to_have_text("3")
    page.get_by_role("button", name="Follow").click()
    expect(page.get_by_role("button", name="Following ✓")).to_be_visible()
    expect(page.get_by_test_id("follower-count")).to_have_text("4")
    screenshot(page, "2-profile")

    # The Following feed now shows Asha's posts
    page.get_by_role("link", name="Feed", exact=True).click()
    expect(page.get_by_test_id("post-card")).to_have_count(2)
    first_post = page.get_by_test_id("post-card").first
    expect(first_post).to_contain_text("Golden hour")

    # Like it (without a page reload) and comment on it
    expect(first_post.locator(".like-text")).to_have_text("3 likes")
    first_post.get_by_role("button", name="Like").click()
    expect(first_post.locator(".like-text")).to_have_text("4 likes")
    first_post.get_by_placeholder("Add a comment...").fill("Stunning colours!")
    first_post.get_by_role("button", name="Post", exact=True).click()
    first_post = page.get_by_test_id("post-card").first
    expect(first_post.get_by_test_id("comment").last).to_contain_text("neha Stunning colours!")
    page.evaluate("window.scrollTo(0, 0)")
    screenshot(page, "1-feed")

    # Share a new photo
    page.get_by_role("link", name="+ New post").click()
    page.set_input_files("#id_image", str(PHOTO))
    page.fill("#id_title", "My first post")
    page.fill("#id_caption", "Testing PhotoNest")
    expect(page.locator("#preview")).to_be_visible()
    screenshot(page, "4-new-post")
    page.get_by_role("button", name="Publish").click()
    expect(page.get_by_text("Your photo was published.")).to_be_visible()
    expect(page).to_have_url(re.compile(r"/posts/\d+/$"))

    # It appears on the user's own profile
    page.get_by_role("link", name="My profile").click()
    expect(page.get_by_test_id("profile-post")).to_have_count(1)

    assert Follow.objects.filter(follower__username="neha", following__username="asha").exists()
    assert Post.objects.get(title="Golden hour").liked_by.filter(username="neha").exists()
    assert Post.objects.filter(user__username="neha", title="My first post").exists()
