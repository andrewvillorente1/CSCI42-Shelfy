from django.test import TestCase
from django.contrib.auth.models import User
from ..forms import LibraryItemEditForm
from ..models import UserLibraryItem
# Again, assuming Media model is available
try:
    from shelfy.models import Media
except ImportError:
    class Media:
        objects = None
        def __init__(self, **kwargs): self.id = kwargs.get('id', None); self.title = 'Mock'
        def save(self): pass
        @staticmethod
        def create(**kwargs): return Media(**kwargs)


class LibraryItemEditFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='formuser', password='password123')
        try:
            cls.media = Media.objects.create(title="Form Test Media", media_type="game", external_id="game456")
            cls.item = UserLibraryItem.objects.create(user=cls.user, media=cls.media, status="in_progress")
        except NameError:
            cls.media = None
            cls.item = None

    def setUp(self):
        if not self.item: self.skipTest("Required models (Media/UserLibraryItem) not available")

    def test_form_valid_data_completed(self):
        """Test form with valid data for 'completed' status."""
        form_data = {
            'status': 'completed',
            'rating': 5,
            'review': 'Great game!',
            'notes': 'Finished main quest.'
        }
        form = LibraryItemEditForm(data=form_data, instance=self.item)
        self.assertTrue(form.is_valid(), msg=form.errors)
        # Check cleaned data is as expected
        self.assertEqual(form.cleaned_data['rating'], 5)
        self.assertEqual(form.cleaned_data['review'], 'Great game!')

    def test_form_valid_data_in_progress(self):
        """Test form with valid data for 'in_progress' status (rating/review should be ignored)."""
        form_data = {
            'status': 'in_progress',
            'rating': 4, # Should be cleared by clean()
            'review': 'Playing now.', # Should be cleared by clean()
            'notes': 'Halfway through.'
        }
        form = LibraryItemEditForm(data=form_data, instance=self.item)
        self.assertTrue(form.is_valid(), msg=form.errors)
        # Check that clean() method cleared rating and review
        self.assertIsNone(form.cleaned_data.get('rating'))
        self.assertIsNone(form.cleaned_data.get('review'))
        self.assertEqual(form.cleaned_data['notes'], 'Halfway through.')

    def test_form_valid_data_dropped_with_rating(self):
        """Test form with valid data for 'dropped' status."""
        form_data = {
            'status': 'dropped',
            'rating': 1,
            'review': 'Not for me.',
            'notes': 'Stopped playing.'
        }
        form = LibraryItemEditForm(data=form_data, instance=self.item)
        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data['rating'], 1)
        self.assertEqual(form.cleaned_data['review'], 'Not for me.')

    def test_form_empty_rating_is_none(self):
        """Test that submitting an empty string for rating results in None."""
        form_data = {
            'status': 'completed',
            'rating': '', # Empty rating
            'review': 'Finished.',
            'notes': ''
        }
        form = LibraryItemEditForm(data=form_data, instance=self.item)
        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertIsNone(form.cleaned_data['rating'])

    def test_form_invalid_status(self):
        """Test form with an invalid status choice."""
        form_data = {'status': 'invalid_choice'}
        form = LibraryItemEditForm(data=form_data, instance=self.item)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_form_save_updates_instance(self):
        """Test that saving the form correctly updates the model instance."""
        form_data = {
            'status': 'completed',
            'rating': 5,
            'review': 'Excellent',
            'notes': 'All achievements'
        }
        form = LibraryItemEditForm(data=form_data, instance=self.item)
        if form.is_valid():
            form.save()
            self.item.refresh_from_db()
            self.assertEqual(self.item.status, 'completed')
            self.assertEqual(self.item.rating, 5)
            self.assertEqual(self.item.review, 'Excellent')
            self.assertEqual(self.item.notes, 'All achievements')
        else:
            self.fail(f"Form was not valid: {form.errors}")

    def test_form_save_clears_rating_review(self):
        """Test saving form for 'planned' status clears rating/review in DB."""
        # First set a rating/review when completed
        self.item.status = 'completed'
        self.item.rating = 4
        self.item.review = "Was good"
        self.item.save()

        # Now use the form to change status back to 'planned'
        form_data = {
            'status': 'planned',
            'rating': 4, # Provide rating, but it should be ignored by clean()
            'review': 'Going to play soon', # Should also be ignored
            'notes': 'On the backlog'
        }
        form = LibraryItemEditForm(data=form_data, instance=self.item)
        if form.is_valid():
            form.save()
            self.item.refresh_from_db()
            self.assertEqual(self.item.status, 'planned')
            self.assertIsNone(self.item.rating) # Check DB value is None
            self.assertIsNone(self.item.review) # Check DB value is None
            self.assertEqual(self.item.notes, 'On the backlog')
        else:
            self.fail(f"Form was not valid: {form.errors}")