"""Fill the app with demo users, photos, likes, comments and follows.

    python manage.py seed_demo          # create the demo data once
    python manage.py seed_demo --reset  # delete the demo users and create everything again
"""
from datetime import timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from posts.models import Post, Comment
from users.models import Profile, Follow

PHOTOS_DIR = Path(__file__).resolve().parents[2] / 'demo_photos'
DEMO_PASSWORD = 'photonest-demo'

# username, first name, last name, bio
PEOPLE = [
    ('asha', 'Asha', 'Verma', 'Weekend hiker and sunset chaser.'),
    ('ravi', 'Ravi', 'Kumar', 'City walks, night lights and good coffee.'),
    ('meera', 'Meera', 'Iyer', 'Beaches over mountains, always.'),
    ('kabir', 'Kabir', 'Singh', 'Camping, stars and long drives.'),
]

# author, photo, title, caption, hours ago
POSTS = [
    ('asha', 'mountain-sunset.jpg', 'Golden hour', 'Worth every step of the climb.', 2),
    ('ravi', 'city-lights.jpg', 'City lights', 'The city never really sleeps.', 5),
    ('meera', 'beach-day.jpg', 'Beach day', 'Sun, sand and zero notifications.', 9),
    ('kabir', 'camping-stars.jpg', 'Night under the stars', 'No signal, no problem.', 20),
    ('ravi', 'morning-coffee.jpg', 'Morning ritual', 'First coffee of the day hits different.', 28),
    ('asha', 'misty-forest.jpg', 'Into the forest', 'Morning mist on the trail.', 40),
    ('meera', 'balloon-festival.jpg', 'Balloon festival', 'Woke up at 5 am for this. No regrets.', 55),
    ('kabir', 'lake-evening.jpg', 'Lake evening', 'Calm water, calm mind.', 70),
]

FOLLOWS = [
    ('asha', 'ravi'), ('asha', 'meera'), ('ravi', 'asha'), ('ravi', 'kabir'),
    ('meera', 'asha'), ('kabir', 'asha'), ('kabir', 'meera'),
]

# post index -> users who liked it
LIKES = {0: ['ravi', 'meera', 'kabir'], 1: ['asha', 'kabir'], 2: ['asha'], 3: ['asha', 'meera'],
         4: ['meera'], 5: ['ravi', 'kabir'], 6: ['asha', 'ravi', 'kabir'], 7: ['meera']}

# post index, author, comment
COMMENTS = [
    (0, 'ravi', 'Those colours!'),
    (0, 'meera', 'Adding this trail to my list.'),
    (1, 'asha', 'Which rooftop is this?'),
    (2, 'kabir', 'Take me there.'),
    (3, 'asha', 'So peaceful.'),
    (6, 'ravi', 'Early mornings pay off.'),
]


class Command(BaseCommand):
    help = 'Create demo users, photos, likes, comments and follows.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete the demo users first and create everything again.')

    @transaction.atomic
    def handle(self, *args, **options):
        usernames = [person[0] for person in PEOPLE]
        if options['reset']:
            User.objects.filter(username__in=usernames).delete()
        elif User.objects.filter(username__in=usernames).exists():
            self.stdout.write(self.style.WARNING('Demo data already exists. Run with --reset to create it again.'))
            return

        users = {}
        for username, first_name, last_name, bio in PEOPLE:
            user = User.objects.create_user(
                username=username, email=f'{username}@example.com', password=DEMO_PASSWORD,
                first_name=first_name, last_name=last_name,
            )
            Profile.objects.create(user=user, bio=bio)
            users[username] = user

        now = timezone.now()
        posts = []
        for username, photo, title, caption, hours_ago in POSTS:
            post = Post(user=users[username], title=title, caption=caption)
            with open(PHOTOS_DIR / photo, 'rb') as image_file:
                post.image.save(photo, File(image_file), save=False)
            post.save()
            # spread the posts over the last few days so the feed shows "2 hours ago", "3 days ago", ...
            Post.objects.filter(pk=post.pk).update(created=now - timedelta(hours=hours_ago))
            posts.append(post)

        for follower, following in FOLLOWS:
            Follow.objects.create(follower=users[follower], following=users[following])
        for index, likers in LIKES.items():
            posts[index].liked_by.add(*[users[name] for name in likers])
        for index, author, body in COMMENTS:
            Comment.objects.create(post=posts[index], author=users[author], body=body)

        self.stdout.write(self.style.SUCCESS(
            f'Created {len(users)} demo users and {len(posts)} posts. '
            f'Log in as "asha" (or ravi, meera, kabir) with the password "{DEMO_PASSWORD}".'
        ))
