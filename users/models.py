from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='profile_photos/', blank=True)
    bio = models.CharField(max_length=160, blank=True)

    def __str__(self):
        return self.user.username


class Follow(models.Model):
    """`follower` follows `following`."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='follower_set')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow'),
            models.CheckConstraint(condition=~models.Q(follower=models.F('following')), name='no_self_follow'),
        ]

    def __str__(self):
        return f'{self.follower} follows {self.following}'
