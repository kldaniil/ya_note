from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestListPage(TestCase):

    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.author = User.objects.create(username='Автор')
        all_notes = [
            Note(
                title=f'Заметка {index}',
                text=f'Текст заметки {index}',
                author=cls.author,
                slug=f'qwerty_{index}'
            )
            for index in range(10)
        ]
        Note.objects.bulk_create(all_notes)

    def test_user_empty_list(self):
        self.client.force_login(self.user)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        notes_count = object_list.count()
        self.assertEqual(notes_count, 0)

    def test_sorting(self):
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        all_ids = [notes.id for notes in object_list]
        sorted_ids = sorted(all_ids)
        self.assertEqual(all_ids, sorted_ids)


class TestForms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.author = User.objects.create(username='Автор')
        cls.notes = Note.objects.create(
            title='hello', text='world', slug='slug1', author=cls.author
        )

    def test_create_form(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:add'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)
