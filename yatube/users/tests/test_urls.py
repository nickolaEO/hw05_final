from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Неавторизованный клиент
        cls.guest_client = Client()
        # Авторизованный клиент
        cls.user = User.objects.create_user(username='TestUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    urls_non_auth = {
        reverse('users:signup'): 'users/signup.html',
        reverse('users:login'): 'users/login.html',
        reverse(
            'users:password_reset_form'
        ): 'users/password_reset_form.html',
        reverse(
            'users:password_reset_done'
        ): 'users/password_reset_done.html',
        reverse(
            'users:password_reset_confirm',
            args=('1111', '1111')
        ): 'users/password_reset_confirm.html',
        reverse(
            'users:password_reset_complete'
        ): 'users/password_reset_complete.html',
        reverse('users:logout'): 'users/logged_out.html',
    }
    urls_auth = {
        reverse(
            'users:password_change'
        ): 'users/password_change_form.html',
        reverse(
            'users:password_change_done'
        ): 'users/password_change_done.html',
    }

    def test_user_urls_exists_at_desired_location_non_authorized(self):
        """URL-страница доступна неавторизованным клиентам."""
        for url, template in UserURLTests.urls_non_auth.items():
            with self.subTest(url=url):
                response = UserURLTests.guest_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_user_urls_exists_at_desired_location_authorized(self):
        """URL-страница доступна авторизованным клиентам."""
        for url, template in UserURLTests.urls_auth.items():
            with self.subTest(url=url):
                response = UserURLTests.authorized_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_user_urls_uses_correct_template_non_authorized(self):
        """
        URL-адрес использует соответствующий шаблон (неавториз. клиент).
        """
        for url, template in UserURLTests.urls_non_auth.items():
            with self.subTest(url=url):
                response = UserURLTests.guest_client.get(url, follow=True)
                self.assertTemplateUsed(response, template)

    def test_user_urls_uses_correct_template_authorized(self):
        """
        URL-адрес использует соответствующий шаблон (авториз. клиент).
        """
        for url, template in UserURLTests.urls_auth.items():
            with self.subTest(url=url):
                response = UserURLTests.authorized_client.get(url, follow=True)
                self.assertTemplateUsed(response, template)
