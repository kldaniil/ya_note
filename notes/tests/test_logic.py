from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm, WARNING


User = get_user_model()


class BaseTestCase(TestCase):

    NOTE_TITLE = 'Заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'qwerty'
    NEW_NOTE_TITLE = 'Заголовок заметки1'
    NEW_NOTE_TEXT = 'Текст заметки1'
    NEW_NOTE_SLUG = 'qwerty1'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.anon_client = Client()
        cls.reader_client = Client()
        cls.author_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.author_client.force_login(cls.author)


class TestNoteCreation(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_url = reverse('notes:add')
        cls.redirect_url = reverse('notes:success')
        cls.form_data = {
            'text':
            cls.NOTE_TEXT,
            'title': cls.NOTE_TITLE,
            'slug': cls.NOTE_SLUG
        }

    def test_anonymous_user_cant_create_note(self):
        self.anon_client.post(self.create_url, self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        response = self.author_client.post(self.create_url, self.form_data)
        self.assertRedirects(response, self.redirect_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        notes = Note.objects.get()
        self.assertEqual(notes.title, self.NOTE_TITLE)
        self.assertEqual(notes.text, self.NOTE_TEXT)
        self.assertEqual(notes.slug, self.NOTE_SLUG)
        self.assertEqual(notes.author, self.author)

    def test_unique_slug(self):
        Note.objects.create(
            title='',
            text='',
            author=self.author,
            slug=self.NOTE_SLUG
        )
        response = self.author_client.post(self.create_url, self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.NOTE_SLUG + WARNING,
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


class TestNoteEditDelete(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.notes = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug=cls.NOTE_SLUG
        )
        cls.edit_url = reverse('notes:edit', args=(cls.notes.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.notes.slug,))
        cls.redirect_url = reverse('notes:success')
        cls.form_data = {
            'text':
            cls.NEW_NOTE_TEXT,
            'title': cls.NEW_NOTE_TITLE,
            'slug': cls.NEW_NOTE_SLUG
        }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.redirect_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.redirect_url)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.notes.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.notes.slug, self.NEW_NOTE_SLUG)
        self.assertEqual(self.notes.author, self.author)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.title, self.NOTE_TITLE)
        self.assertEqual(self.notes.text, self.NOTE_TEXT)
        self.assertEqual(self.notes.slug, self.NOTE_SLUG)
        self.assertEqual(self.notes.author, self.author)
