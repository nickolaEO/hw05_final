from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CreationForm

User = get_user_model()


class CreationFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form = CreationForm

    def test_signup_form(self):
        """
        Создается новый пользователь при отправке формы регистрации.
        """
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Name',
            'last_name': 'Surname',
            'username': 'NewUser',
            'email': 'new@user.com',
            'password1': 'Qwerty.1234',
            'password2': 'Qwerty.1234',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertTrue(
            User.objects.filter(username=self.user.username).exists()
        )
