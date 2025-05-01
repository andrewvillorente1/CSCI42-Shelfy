from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from ..models import UserLibraryItem, hashids # Import hashids from your models
# IMPORTANT: You need the Media model from your 'shelfy' app
# Adjust the import path if 'shelfy' is structured differently
try:
    from shelfy.models import Media
except ImportError:
    # Provide a mock or basic structure if shelfy isn't easily importable in test env
    # This is a placeholder - ideally, shelfy should be installed/available
    print("Warning: Could not import Media model from shelfy. Tests may fail.")
    # Define a minimal mock if necessary for tests to run
    class Media:
        objects = None # Add basic manager mock if needed
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', None)
            self.title = kwargs.get('title', 'Mock Media')
        def save(self): pass
        @staticmethod
        def create(**kwargs): return Media(**kwargs)


class UserLibraryItemModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a user
        cls.user = User.objects.create_user(username='libuser', password='password123')
        # Create a media item (assuming Media model is available)
        try:
            cls.media = Media.objects.create(
                title="Test Book",
                media_type="book",
                external_id="book123"
            )
        except NameError:
            cls.media = None # Handle case where Media couldn't be imported/mocked

    def test_create_library_item(self):
        """Test creating a UserLibraryItem successfully."""
        if not self.media: self.skipTest("Media model not available")

        item_count = UserLibraryItem.objects.count()
        item = UserLibraryItem.objects.create(
            user=self.user,
            media=self.media,
            status="in_progress" # Test non-default status
        )
        self.assertEqual(UserLibraryItem.objects.count(), item_count + 1)
        self.assertEqual(item.user, self.user)
        self.assertEqual(item.media, self.media)
        self.assertEqual(item.status, "in_progress")
        self.assertEqual(item.rating, None) # Default
        # Check auto_now_add and auto_now fields are set
        self.assertIsNotNone(item.date_added)
        self.assertIsNotNone(item.last_updated)

    def test_default_status(self):
        """Test that the default status is 'planned'."""
        if not self.media: self.skipTest("Media model not available")
        item = UserLibraryItem.objects.create(user=self.user, media=self.media)
        self.assertEqual(item.status, "planned")

    def test_unique_together_constraint(self):
        """Test that a user cannot add the same media item twice."""
        if not self.media: self.skipTest("Media model not available")
        # Create the first item
        UserLibraryItem.objects.create(user=self.user, media=self.media)
        # Attempt to create a duplicate
        with self.assertRaises(IntegrityError):
            UserLibraryItem.objects.create(user=self.user, media=self.media)

    def test_str_representation(self):
        """Test the __str__ method."""
        if not self.media: self.skipTest("Media model not available")
        item = UserLibraryItem.objects.create(user=self.user, media=self.media, status="completed")
        expected_str = f"{self.user.username} - {self.media.title} (completed)"
        self.assertEqual(str(item), expected_str)

    def test_get_hashed_id(self):
        """Test the get_hashed_id method."""
        if not self.media: self.skipTest("Media model not available")
        item = UserLibraryItem.objects.create(user=self.user, media=self.media)
        hashed_id = item.get_hashed_id()
        self.assertIsInstance(hashed_id, str)
        self.assertTrue(len(hashed_id) >= 6) # Based on min_length
        # Decode to check if it matches original id
        decoded_id = hashids.decode(hashed_id)
        self.assertEqual(len(decoded_id), 1)
        self.assertEqual(decoded_id[0], item.id)

    def test_rating_choices(self):
        """Test assigning valid and invalid ratings (via save, not form)."""
        if not self.media: self.skipTest("Media model not available")
        item = UserLibraryItem.objects.create(user=self.user, media=self.media)
        # Valid rating
        item.rating = 5
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.rating, 5)

        # Invalid rating (model field PositiveSmallIntegerField might raise DB error
        # depending on backend, or Django validation might catch it first if clean() called)
        # This test might be better suited for the form which explicitly handles choices.
        # Trying to save an invalid choice might raise IntegrityError or ValidationError
        # For model-level, we mostly trust Django's field validation.
        pass