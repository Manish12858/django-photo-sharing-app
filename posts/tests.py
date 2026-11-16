import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Post

# 1x1 transparent GIF
GIF = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,'
       b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class PostFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user('alice', password='s3cret-pass!')
        self.client.login(username='alice', password='s3cret-pass!')

    def test_feed_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('feed')).status_code, 302)

    def test_create_like_comment_delete(self):
        img = SimpleUploadedFile('a.gif', GIF, content_type='image/gif')
        r = self.client.post(reverse('create'), {'title': 'Hello', 'caption': 'hi', 'image': img})
        self.assertRedirects(r, reverse('feed'))
        post = Post.objects.get()
        self.assertEqual(post.slug, 'hello')

        r = self.client.post(reverse('like'), {'post_id': post.id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.json(), {'liked': True, 'count': 1})

        self.client.post(reverse('feed'), {'post_id': post.id, 'body': 'nice'})
        self.assertEqual(post.comments.get().posted_by, 'alice')

        r = self.client.get(reverse('feed'))
        self.assertContains(r, 'Hello')
        self.assertContains(r, 'nice')

        self.client.post(reverse('post_delete', args=[post.id]))
        self.assertFalse(Post.objects.exists())
