from django.contrib.auth import get_user
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

GROUP_SLUG = 'group_slug_1'
USER_NAME = 'user_1'
USER_NAME_2 = 'user_2'
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
USER_LOGIN = reverse('users:login')
GROUP_URL = reverse('posts:group_list', args=[GROUP_SLUG])
PROFILE_URL = reverse('posts:profile', args=[USER_NAME])
PROFILE_URL_2 = reverse('posts:profile', args=[USER_NAME_2])
FOLLOW_INDEX = reverse('posts:follow_index')
PAGE_404 = '/404'
REDIRECT_CREATE = f'{USER_LOGIN}?next={POST_CREATE_URL}'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create(username=USER_NAME)
        cls.user_2 = User.objects.create(username=USER_NAME_2)
        cls.group = Group.objects.create(
            slug=GROUP_SLUG,
            title='group_1',
            description='Тестовая группа 1',
        )
        cls.post = Post.objects.create(
            text='Test post',
            author=cls.user_1,
            group=cls.group
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.REDIRECT_EDIT = f'{USER_LOGIN}?next={cls.POST_EDIT_URL}'
        cls.PROFILE_FOLLOW = (reverse(
            'posts:profile_follow',
            args=[cls.user_1.username],
        ))
        cls.PROFILE_UNFOLLOW = (reverse(
            'posts:profile_unfollow',
            args=[cls.user_2.username],
        ))
        cls.REDIRECT_FOLLOW = f'{USER_LOGIN}?next={cls.PROFILE_FOLLOW}'
        cls.REDIRECT_UNFOLLOW = f'{USER_LOGIN}?next={cls.PROFILE_UNFOLLOW}'

    def setUp(self):
        self.guest = Client()
        self.another = Client()
        self.another.force_login(self.user_2)
        self.author = Client()
        self.author.force_login(self.user_1)

    def testing_status_pages(self):
        urls = [
            [INDEX_URL, self.guest, 200],
            [POST_CREATE_URL, self.another, 200],
            [POST_CREATE_URL, self.guest, 302],
            [GROUP_URL, self.guest, 200],
            [PROFILE_URL, self.guest, 200],
            [self.POST_DETAIL_URL, self.guest, 200],
            [self.POST_EDIT_URL, self.guest, 302],
            [self.POST_EDIT_URL, self.another, 302],
            [self.POST_EDIT_URL, self.author, 200],
            [PAGE_404, self.author, 404],
            [self.PROFILE_FOLLOW, self.author, 302],
            [self.PROFILE_FOLLOW, self.another, 302],
            [self.PROFILE_FOLLOW, self.guest, 302],
            [self.PROFILE_UNFOLLOW, self.author, 302],
            [self.PROFILE_UNFOLLOW, self.another, 302],
            [self.PROFILE_UNFOLLOW, self.guest, 302],
        ]
        for url, client, code, in urls:
            with self.subTest(
                url=url, code=code, client=get_user(client).username
            ):
                self.assertEqual(
                    client.get(url).status_code, code
                )

    def test_pages_uses_correct_template(self):
        urls = {
            INDEX_URL: 'posts/index.html',
            POST_CREATE_URL: 'posts/create_post.html',
            GROUP_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            PAGE_404: 'core/404.html',
            FOLLOW_INDEX: 'posts/follow.html',
        }
        for url, html in urls.items():
            with self.subTest(html=html):
                self.assertTemplateUsed(
                    self.author.get(url), html
                )

    def test_redirect(self):
        urls = [
            [self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL],
            [self.POST_EDIT_URL, self.guest, self.REDIRECT_EDIT],
            [POST_CREATE_URL, self.guest, REDIRECT_CREATE],
            [self.PROFILE_FOLLOW, self.author, PROFILE_URL],
            [self.PROFILE_FOLLOW, self.another, PROFILE_URL],
            [self.PROFILE_FOLLOW, self.guest, self.REDIRECT_FOLLOW],
            [self.PROFILE_UNFOLLOW, self.author, PROFILE_URL_2],
            [self.PROFILE_UNFOLLOW, self.another, PROFILE_URL_2],
            [self.PROFILE_UNFOLLOW, self.guest, self.REDIRECT_UNFOLLOW],
        ]
        for url, client, redirect_url in urls:
            with self.subTest(url=url, re_url=redirect_url):
                self.assertRedirects(
                    client.get(url, follow=True), redirect_url
                )
