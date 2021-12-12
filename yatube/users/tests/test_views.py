from django import forms
from django.test import Client, TestCase
from django.urls import reverse


class UsersSignUpTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_user_signup_view_class(self):
        """
        На страницу регистрации пользователя передается форма регистрации.
        """
        response = self.guest_client.get(
            reverse('users:signup')
        )
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
