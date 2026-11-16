from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class UserFlowTests(TestCase):
    def test_register_login_logout(self):
        r = self.client.post(reverse('register'), {
            'username': 'bob', 'email': 'bob@example.com', 'first_name': 'Bob',
            'password': 'Tr1cky-pass', 'password2': 'Tr1cky-pass'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(User.objects.filter(username='bob', profile__isnull=False).exists())

        r = self.client.post(reverse('login'), {'username': 'bob', 'password': 'Tr1cky-pass'})
        self.assertRedirects(r, reverse('feed'))
        for name in ('index', 'edit', 'create', 'password_change'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get(reverse('index')).status_code, 302)

    def test_password_mismatch(self):
        r = self.client.post(reverse('register'), {
            'username': 'bob', 'email': 'b@x.com', 'first_name': 'B',
            'password': 'Tr1cky-pass', 'password2': 'other-pass1'})
        self.assertContains(r, 'Passwords do not match')
        self.assertFalse(User.objects.exists())

    def test_superuser_without_profile_can_edit(self):
        User.objects.create_superuser('root', 'r@x.com', 'pw-12345-x')
        self.client.login(username='root', password='pw-12345-x')
        self.assertEqual(self.client.get(reverse('edit')).status_code, 200)
        self.assertEqual(self.client.get(reverse('feed')).status_code, 200)
