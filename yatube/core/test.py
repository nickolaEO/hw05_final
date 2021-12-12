from http import HTTPStatus

from django.test import Client, TestCase


class CustomErrorTestClass(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404_error_page(self):
        """
        Страница 404 отдает кастомный шаблон.
        """
        response = self.guest_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
