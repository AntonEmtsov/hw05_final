import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

USER_NAME = 'user'
USER_NAME_2 = 'user_2'
GROUP_SLUG = 'group_slug_1'
GROUP_SLUG_2 = 'group_slug_2'
TEXT = 'Измененный пост - test_edit_post'

POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USER_NAME])

GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name='GIF.gif',
            content=GIF,
            content_type='image/small',
        )
        cls.uploaded_2 = SimpleUploadedFile(
            name='GIF_2.gif',
            content=GIF,
            content_type='image/small',
        )
        cls.uploaded_3 = SimpleUploadedFile(
            name='GIF_3.gif',
            content=GIF,
            content_type='image/small',
        )
        cls.uploaded_4 = SimpleUploadedFile(
            name='GIF_4.gif',
            content=GIF,
            content_type='image/small',
        )
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
            image=cls.uploaded_3,
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.COMMENT_POST = reverse('posts:add_comment', args=[cls.post.id])
        cls.NEW_COMMENT = {
            'text': 'коммент',
            'post': cls.post,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.another_client = Client()
        self.another_client.force_login(self.user2)
        self.guest_client = Client()

    def test_create_post(self):
        Post.objects.all().delete()
        new_post = {
            'text': 'Тест создания поста - test_create_post',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.author_client.post(
            POST_CREATE_URL,
            data=new_post,
            follow=True,
        )
        image = f"posts/{new_post['image'].name}"
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
            'image': self.uploaded_4,
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
            'image': self.uploaded_2,
        }
        response = self.author_client.post(
            self.POST_EDIT_URL,
            data=edit_post,
            follow=True,
        )
        image = f"posts/{edit_post['image'].name}"
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
        }
        response = self.guest_client.post(
            self.POST_EDIT_URL,
            data=edit_post,
            follow=True,
        )
        cases = [self.guest_client, self.another_client]
        for client in cases:
            with self.subTest(client=client):
                response = client.post(
                    self.POST_EDIT_URL,
                    data=edit_post,
                    follow=True,
                )
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertNotEqual(edit_post['text'], post.text)
                self.assertNotEqual(edit_post['group'], post.group.id)

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
