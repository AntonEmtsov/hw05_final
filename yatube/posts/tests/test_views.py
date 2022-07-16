import shutil
import tempfile

from django import conf
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts import settings
from ..models import Group, Post, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=conf.settings.BASE_DIR)

GROUP_SLUG = 'group_slug_1'
GROUP_SLUG_2 = 'group_slug_2'
USER_NAME = 'user_1'

INDEX_URL = reverse('posts:index')
GROUP_URL = reverse('posts:group_list', args=[GROUP_SLUG])
GROUP_URL_2 = reverse('posts:group_list', args=[GROUP_SLUG_2])
PROFILE_URL = reverse('posts:profile', args=[USER_NAME])
FOLLOW_INDEX = (reverse('posts:follow_index'))

GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        uploaded = SimpleUploadedFile(
            name='test_gif_name.gif',
            content=GIF,
            content_type='image/gif'
        )
        cls.user = User.objects.create(username=USER_NAME)
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
            image=uploaded,
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_index_pages_show_correct_context(self):
        urls = [
            [INDEX_URL, 'page_obj'],
            [GROUP_URL, 'page_obj'],
            [PROFILE_URL, 'page_obj'],
            [self.POST_DETAIL_URL, 'post'],
        ]
        for url, contex in urls:
            with self.subTest(url=url):
                response = self.user_client.get(url)
                post = response.context[contex]
                if contex == 'page_obj':
                    self.assertEqual(len(response.context[contex]), 1)
                    post = response.context[contex][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.image, self.post.image)

    def test_group_list_pages_show_correct_context(self):
        group = self.user_client.get(
            GROUP_URL).context.get('group')
        self.assertEqual(group.id, self.post.group.id)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_profile_correct_context(self):
        self.assertEqual(self.user_client.get(
            PROFILE_URL).context['author'], self.user)

    def test_post_another_group(self):
        self.assertNotIn(
            self.post,
            self.user_client.get(GROUP_URL_2).context.get('page_obj')
        )

    def test_pagination(self):
        count_obj = Post.objects.all().count() + 1
        page_2 = "?page=2"
        Post.objects.bulk_create(
            Post(
                text=f'post {i}',
                author=self.user,
                group=self.group,
            ) for i in range(settings.NUMBER_POST_PAGINATION + 1)
        )
        urls = [
            [INDEX_URL, settings.NUMBER_POST_PAGINATION],
            [GROUP_URL, settings.NUMBER_POST_PAGINATION],
            [PROFILE_URL, settings.NUMBER_POST_PAGINATION],
            [INDEX_URL + page_2, count_obj],
            [GROUP_URL + page_2, count_obj],
            [PROFILE_URL + page_2, count_obj],
        ]
        for url, count in urls:
            with self.subTest(url=url):
                self.assertEqual(len(
                    self.client.get(url).context['page_obj']),
                    count
                )

    def test_cache_index(self):
        first_client = self.user_client.get(INDEX_URL)
        self.assertNotEqual(Post.objects.all().count(), 0)
        Post.objects.all().delete()
        two_client = self.user_client.get(INDEX_URL)
        self.assertEqual(Post.objects.all().count(), 0)
        self.assertEqual(first_client.content, two_client.content)
        cache.clear()
        third_client = self.user_client.get(INDEX_URL)
        self.assertNotEqual(first_client.content, third_client.content)

class FollowTests(TestCase):
    def setUp(self):

        self.user_follower = User.objects.create(username='follower')
        self.user_following = User.objects.create(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Test follower/following',
        )
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)
        self.PROFILE_FOLLOW = (reverse(
            'posts:profile_follow',
            args=[self.user_following.username],
        ))
        self.PROFILE_UNFOLLOW = (reverse(
            'posts:profile_unfollow',
            args=[self.user_following.username],
        ))

    def test_follow_unfollow(self):
        Follow.objects.all().delete()
        self.assertEqual(Follow.objects.all().count(), 0)
        self.client_auth_follower.get(self.PROFILE_FOLLOW)
        self.assertEqual(Follow.objects.all().count(), 1)
        self.client_auth_follower.get(self.PROFILE_UNFOLLOW)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client_auth_follower.get(FOLLOW_INDEX)
        post = response.context['page_obj'][0].text
        self.assertEqual(post, self.post.text)
        response = self.client_auth_following.get(FOLLOW_INDEX)
        self.assertNotContains(response, self.post.text)