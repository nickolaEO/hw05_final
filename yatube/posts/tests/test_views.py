import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.post_objs = Post.objects.bulk_create(
            [Post(
                pk=i,
                author=cls.author,
                text=f'Добрый вечер, я диспетчер #{i}!',
                group=cls.group
            ) for i in range(13)]
        )
        cls.post_per_page = {
            'first': settings.POST_PER_PAGE,
            'second': Post.objects.count() - settings.POST_PER_PAGE
        }

    def test_paginator_for_index_group_list_profile_page(self):
        """
        Паджинатор корректно работает на страницах index, group_list, profile.
        """
        pages = {
            reverse('posts:index'): self.post_per_page['first'],
            reverse('posts:index') + '?page=2': self.post_per_page['second'],
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorTests.group.slug}
            ): self.post_per_page['first'],
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorTests.group.slug}
            ) + '?page=2': self.post_per_page['second'],
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorTests.author}
            ): self.post_per_page['first'],
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorTests.author}
            ) + '?page=2': self.post_per_page['second'],
        }

        for page, post_count in pages.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    len(response.context['page_obj'].object_list),
                    post_count
                )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.author)
        # Другая группа
        cls.another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='another-test-slug',
            description='Другое тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = PostPagesTests.authorized_client_author.get(
                    reverse_name
                )
                self.assertTemplateUsed(response, template)

    def check_context(self, post_object):
        self.assertEqual(post_object.text, PostPagesTests.post.text)
        self.assertEqual(post_object.author, PostPagesTests.author)
        self.assertEqual(post_object.image, PostPagesTests.post.image)
        self.assertEqual(post_object.group, PostPagesTests.group)
        self.assertNotEqual(post_object.group, PostPagesTests.another_group)

    def test_index_page_uses_correct_context(self):
        """
        Страница index сформирована с правильным контекстом.
        """
        response = PostPagesTests.guest_client.get(
            reverse('posts:index')
        )
        post = response.context['page_obj'][0]
        self.check_context(post)

    def test_group_list_page_uses_correct_context(self):
        """
        Страница group_list сформирована с правильным контекстом.
        """
        response = PostPagesTests.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            )
        )
        post = response.context['page_obj'][0]
        self.assertEqual(
            response.context['group'],
            PostPagesTests.group
        )
        self.check_context(post)

    def test_profile_page_uses_correct_context(self):
        """
        Страница profile сформирована с правильным контекстом.
        """
        response = PostPagesTests.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.author.username}
            )
        )
        post = response.context['page_obj'][0]
        self.assertEqual(
            response.context['user_profile'].username,
            PostPagesTests.author.username
        )
        self.check_context(post)

    def test_post_detail_page_contains_one_record(self):
        """На страницу с деталями поста передается один объект."""
        response = PostPagesTests.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.pk}
            )
        )
        post = response.context['user_single_post']
        self.check_context(post)
        self.assertEqual(
            response.context['user_single_post'].id,
            PostPagesTests.post.pk
        )
        self.assertIsInstance(
            response.context['form'].fields['text'],
            forms.fields.CharField
        )

    def test_post_create_page_contains_create_form(self):
        """
        На страницу с созданием поста передается форма создания.
        """
        response = PostPagesTests.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_contains_edit_form(self):
        """
        На страницу с редактированием поста передается форма редактирования.
        """
        response = PostPagesTests.authorized_client_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.pk}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

        self.assertEqual(
            response.context['post'].id,
            PostPagesTests.post.pk
        )
        self.assertTrue(response.context['is_edit'])

    def test_new_post_creates_on_pages(self):
        """
        Новый пост создается на страницах index, group_list, profile.
        """
        posts_count = Post.objects.count()
        Post.objects.create(
            author=PostPagesTests.author,
            text='Новый пост',
            group=PostPagesTests.group,
            image=PostPagesTests.uploaded,
        )
        urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.author}
            ),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    posts_count + 1
                )

    def test_data_cache_index_page_works_correct(self):
        """
        Кэширование данных на главной странице работает корректно.
        """
        response = PostPagesTests.authorized_client.get(
            reverse('posts:index')
        )
        cached_content = response.content
        Post.objects.all().delete()
        response = PostPagesTests.authorized_client.get(
            reverse('posts:index')
        )
        content_deleted = response.content
        self.assertEqual(
            cached_content,
            content_deleted
        )
        cache.clear()
        response = PostPagesTests.authorized_client.get(
            reverse('posts:index')
        )
        cache_cleared = response.content
        self.assertNotEqual(
            cached_content,
            cache_cleared
        )

    def test_authorized_user_is_follow_the_author(self):
        """
        Авторизованный пользователь может подписываться на других авторов.
        """
        followers_count = Follow.objects.count()
        response = PostPagesTests.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.author}
            )
        )
        self.assertEqual(Follow.objects.count(), followers_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.author}
            )
        )

    def test_authorized_user_is_unfollow_the_author(self):
        """
        Авторизованный пользователь может отписываться от авторов.
        """
        followers_count = Follow.objects.count()
        response = PostPagesTests.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostPagesTests.author}
            )
        )
        self.assertEqual(Follow.objects.count(), followers_count)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.author}
            )
        )

    def test_new_post_appears_on_follower_feed(self):
        """
        Новая запись появляется в ленте подписчиков.
        """
        posts_count = Post.objects.count()
        Post.objects.create(
            author=PostPagesTests.author,
            text='Новый пост',
            group=PostPagesTests.group,
            image=PostPagesTests.uploaded,
        )
        Follow.objects.create(
            user=PostPagesTests.user,
            author=PostPagesTests.author,
        )
        response = PostPagesTests.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), posts_count + 1)

    def test_new_post_dont_appear_on_follower_feed(self):
        """
        Новая запись не появляется в ленте тех, кто не подписан.
        """
        posts_count = Post.objects.count()
        Post.objects.create(
            author=PostPagesTests.author,
            text='Новый пост',
            group=PostPagesTests.group,
            image=PostPagesTests.uploaded,
        )
        response = PostPagesTests.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), posts_count - 1)
