from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Profile
import time # Might be useful for checking save signals indirectly

class ProfileModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a user, which should trigger the signal to create a profile
        cls.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        # Retrieve the profile explicitly - useful if signal is slow or for clarity
        cls.profile = Profile.objects.get(user=cls.user)

    def test_profile_creation_signal(self):
        """Test if a Profile is automatically created when a User is created."""
        user_count = User.objects.count()
        profile_count = Profile.objects.count()

        new_user = User.objects.create_user(username='newuser', password='password123')

        self.assertEqual(User.objects.count(), user_count + 1)
        # Check that the post_save signal created a corresponding profile
        self.assertEqual(Profile.objects.count(), profile_count + 1)
        self.assertTrue(Profile.objects.filter(user=new_user).exists())

    def test_profile_str_representation(self):
        """Test the __str__ method of the Profile model."""
        self.assertEqual(str(self.profile), self.user.username)

    def test_profile_defaults(self):
        """Test the default values for Profile fields (if any)."""
        # In your current model, display_name allows blank/null
        self.assertIsNone(self.profile.display_name, "Default display_name should be None or blank based on model def")
        # Or self.assertEqual(self.profile.display_name, "") if default is blank string

    def test_profile_can_update_display_name(self):
        """Test updating the display_name field."""
        new_display_name = "Test Display Name"
        self.profile.display_name = new_display_name
        self.profile.save()
        # Refresh from DB to ensure it saved
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_name, new_display_name)

    # Note: Testing the save_user_profile signal directly is tricky.
    # It ensures profile.save() is called when user.save() is called.
    # This is often tested implicitly when testing views that update user/profile.
    # If you added fields to Profile that depend on User fields and are updated
    # in the signal, you could test those changes here.