from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Неавторизованный клиент
        cls.guest_client = Client()
        # Авторизованный клиент
        cls.user = User.objects.create_user(username='TestUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Авторизованный клиент (автор)
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Добрый вечер, я диспетчер!',
        )
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.author)

    # Проверка общедоступных страниц
    def test_public_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        urls = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': PostURLTests.group.slug}
            ): HTTPStatus.OK,
            reverse(
                'posts:profile',
                kwargs={'username': PostURLTests.author}
            ): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostURLTests.post.pk}
            ): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostURLTests.post.pk}
            ): HTTPStatus.FOUND,
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostURLTests.post.pk}
            ): HTTPStatus.FOUND,
            reverse('posts:post_create'): HTTPStatus.FOUND,
            reverse('posts:follow_index'): HTTPStatus.FOUND,
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostURLTests.author}
            ): HTTPStatus.FOUND,
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostURLTests.author}
            ): HTTPStatus.FOUND,
        }
        for url, status_code in urls.items():
            with self.subTest(url=url):
                response = PostURLTests.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    # Проверка доступности страниц для авторизованного пользователя
    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница /posts/<post_id>/edit/ доступна автору поста."""
        response = PostURLTests.authorized_client_author.get(
            f'/posts/{PostURLTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_create_url_exists_at_desired_location_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = PostURLTests.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    # Проверка запроса к несуществующей странице
    def test_unexisting_page_url_not_exists_at_desired_location(self):
        """Страница /unexisting_page/ не существует."""
        response = PostURLTests.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostURLTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostURLTests.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostURLTests.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostURLTests.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for url, template in urls.items():
            with self.subTest(url=url):
                response = PostURLTests.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)
