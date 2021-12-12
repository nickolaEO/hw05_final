import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create_form(self):
        """
        Новая запись в БД при отправке формы со страницы создания поста.
        """
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст из формы',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = PostFormTests.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostFormTests.author.username}
            )
        )
        last_post = Post.objects.order_by('pub_date').last()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.id, form_data['group'])
        self.assertEqual(last_post.author, PostFormTests.author)

    def test_post_edit_form(self):
        """
        Изменение поста при отправке формы со страницы редактирования поста.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст из формы',
            'group': PostFormTests.group.id
        }
        response = PostFormTests.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post.pk}
            )
        )
        last_post = Post.objects.last()
        self.assertEqual(
            form_data['text'],
            last_post.text
        )
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.id, form_data['group'])
        self.assertEqual(last_post.author, PostFormTests.author)

    def test_non_authorized_user_publish_post(self):
        """
        Неавторизованный пользователь не может опубликовать пост.
        """
        posts_count = Post.objects.count()
        post_create_url = reverse('posts:post_create')
        form_data = {
            'text': 'Текст из формы',
        }
        response = PostFormTests.guest_client.post(
            post_create_url,
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        self.assertRedirects(
            response,
            reverse('users:login') + f'?next={post_create_url}'
        )
        self.assertEqual(Post.objects.count(), posts_count)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_authorized_client_create_comment(self):
        """
        Авторизованный пользователь может комментировать пост.
        """
        comments_count = CommentFormTest.post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = CommentFormTest.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentFormTest.post.id}
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        last_comment = CommentFormTest.post.comments.last()
        self.assertEqual(last_comment.text, form_data['text'])
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': CommentFormTest.post.id}
            )
        )

    def test_non_authorized_client_create_comments(self):
        """
        Неавторизованный пользователь не может комментировать пост.
        """
        comments_count = CommentFormTest.post.comments.count()
        comment_post_url = reverse(
            'posts:add_comment',
            kwargs={'post_id': CommentFormTest.post.id}
        )
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = CommentFormTest.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response,
            reverse('users:login') + f'?next={comment_post_url}'
        )
