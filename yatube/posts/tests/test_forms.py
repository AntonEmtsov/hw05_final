import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
UPLOAD = Post._meta.get_field('image').upload_to

USER_NAME = 'user'
USER_NAME_2 = 'user_2'
GROUP_SLUG = 'group_slug_1'
GROUP_SLUG_2 = 'group_slug_2'
TEXT = 'Измененный пост - test_edit_post'

POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USER_NAME])
USER_LOGIN = reverse('users:login')

GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
UPLOADED = SimpleUploadedFile(
    name='GIF.gif',
    content=GIF,
    content_type='image/gif',
)
UPLOADED_2 = SimpleUploadedFile(
    name='GIF_2.gif',
    content=GIF,
    content_type='image/gif',
)
UPLOADED_3 = SimpleUploadedFile(
    name='GIF_3.gif',
    content=GIF,
    content_type='image/gif',
)
UPLOADED_4 = SimpleUploadedFile(
    name='GIF_4.gif',
    content=GIF,
    content_type='image/gif',
)
UPLOADED_5 = SimpleUploadedFile(
    name='GIF_5.gif',
    content=GIF,
    content_type='image/gif',
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USER_NAME)
        cls.user2 = User.objects.create(username=USER_NAME_2)
        cls.group = Group.objects.create(
            slug=GROUP_SLUG,
            title='group_1',
            description='Тестовая группа 1',
        )
        cls.group2 = Group.objects.create(
            slug=GROUP_SLUG_2,
            title='group_2',
            description='Тестовая группа 2',
        )
        cls.post = Post.objects.create(
            text='Test post',
            author=cls.user,
            group=cls.group,
            image=UPLOADED_3,
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.COMMENT_POST = reverse('posts:add_comment', args=[cls.post.id])
        cls.REDIRECT_EDIT = f'{USER_LOGIN}?next={cls.POST_EDIT_URL}'
        cls.NEW_COMMENT = {
            'text': 'коммент',
            'post': cls.post.id,
        }
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.another_client = Client()
        cls.another_client.force_login(cls.user2)
        cls.guest_client = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        Post.objects.all().delete()
        new_post = {
            'text': 'Тест создания поста - test_create_post',
            'group': self.group.id,
            'image': UPLOADED,
        }
        response = self.author_client.post(
            POST_CREATE_URL,
            data=new_post,
            follow=True,
        )
        image = f'{UPLOAD}{new_post["image"].name}'
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, new_post['group'])
        self.assertEqual(post.text, new_post['text'])
        self.assertEquals(post.image, image)

    def test_add_post_anonymous(self):
        Post.objects.all().delete()
        new_post = {
            'text': '1Тест создания поста - test_create_post',
            'group': self.group.id,
            'image': UPLOADED_4,
        }
        self.guest_client.post(
            POST_CREATE_URL,
            data=new_post,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_edit_post(self):
        edit_post = {
            'text': TEXT,
            'group': self.group2.id,
            'image': UPLOADED_2,
        }
        response = self.author_client.post(
            self.POST_EDIT_URL,
            data=edit_post,
            follow=True,
        )
        image = f'{UPLOAD}{edit_post["image"].name}'
        post = response.context['post']
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(post.text, edit_post['text'])
        self.assertEqual(post.group.id, edit_post['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEquals(post.image, image)

    def test_edit_post_another_user_and_guest(self):
        edit_post = {
            'text': TEXT,
            'group': self.group2.id,
            'image': UPLOADED_5,
        }
        cases = [
            [self.guest_client, self.REDIRECT_EDIT],
            [self.another_client, self.POST_DETAIL_URL],
        ]
        for client, redirect_url in cases:
            with self.subTest(client=get_user(client).username):
                response = client.post(
                    self.POST_EDIT_URL,
                    data=edit_post,
                    follow=True,
                )
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, redirect_url)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.image, self.post.image)
                self.assertEqual(post.group.id, self.post.group.id)
                self.assertEqual(post.author, self.post.author)

    def test_comments(self):
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.all().count(), 0)
        response = self.author_client.post(
            self.COMMENT_POST,
            data=self.NEW_COMMENT,
            follow=True,
        )
        self.assertEqual(Comment.objects.all().count(), 1)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, self.NEW_COMMENT['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)

    def test_add_comment_anonymous(self):
        Comment.objects.all().delete()
        self.guest_client.post(
            self.COMMENT_POST,
            data=self.NEW_COMMENT,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)
