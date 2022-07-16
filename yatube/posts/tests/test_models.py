from django.test import TestCase

from ..models import Comment, Group, Post, User


class ModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user_1')
        cls.group = Group.objects.create(
            slug='group_slug_1',
            title='group_1',
            description='Тестовая группа 1',
        )
        cls.post = Post.objects.create(
            text='Заходит однажды тестировщик в бар...',
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text=f'Забегает в бар. '
            f'Пролезает в бар. '
            f'Врывается в бар.... ',
            author=cls.user,
            post=cls.post,
        )

    def test_models_have_correct_object_names(self):
        str_models = {
            self.group: self.group.title,
            self.post: self.post.text[:15],
            self.comment: self.comment.text[:20],
        }
        for obj, value in str_models.items():
            with self.subTest(obj=obj):
                self.assertEqual(str(obj), value)
