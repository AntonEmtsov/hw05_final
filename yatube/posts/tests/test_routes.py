from django.test import TestCase
from django.urls import reverse


GROUP_SLUG = 'group_slug_1'
POST_ID = 1
USER_NAME = 'user_1'

CASES = [
    ['/', 'index', []],
    ['/create/', 'post_create', []],
    [f'/group/{GROUP_SLUG}/', 'group_list', [GROUP_SLUG]],
    [f'/profile/{USER_NAME}/', 'profile', [USER_NAME]],
    [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
    [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]],
    [f'/profile/{USER_NAME}/unfollow/', 'profile_unfollow', [USER_NAME]],
    [f'/profile/{USER_NAME}/follow/', 'profile_follow', [USER_NAME]],
    [f'/follow/', 'follow_index', []],
    [f'posts/{POST_ID}/comment/', 'add_comment', [POST_ID]],
]


class ModelTest(TestCase):
    def test_routes(self):
        for url, route, args in CASES:
            with self.subTest(route=route):
                self.assertEqual(url, reverse(f'posts:{route}', args=args))
