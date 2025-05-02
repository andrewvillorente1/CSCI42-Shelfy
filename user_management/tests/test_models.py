from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Profile
import time

class ProfileModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        cls.profile = Profile.objects.get(user=cls.user)

    def test_profile_creation_signal(self):
        """Test if a Profile is automatically created when a User is created."""
        user_count = User.objects.count()
        profile_count = Profile.objects.count()

        new_user = User.objects.create_user(username='newuser', password='password123')

        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(Profile.objects.count(), profile_count + 1)
        self.assertTrue(Profile.objects.filter(user=new_user).exists())

    def test_profile_str_representation(self):
        """Test the __str__ method of the Profile model."""
        self.assertEqual(str(self.profile), self.user.username)

    def test_profile_defaults(self):
        """Test the default values for Profile fields (if any)."""
        self.assertIsNone(self.profile.display_name, "Default display_name should be None or blank based on model def")

    def test_profile_can_update_display_name(self):
        """Test updating the display_name field."""
        new_display_name = "Test Display Name"
        self.profile.display_name = new_display_name
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_name, new_display_name)
