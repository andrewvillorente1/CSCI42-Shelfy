from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Profile
# IMPORTANT: If dashboard view depends on models from other apps (like UserLibraryItem),
# you'll need to import them and potentially mock them or create test instances.
# from user_library.models import UserLibraryItem # Example import
from unittest.mock import patch # Useful for mocking external dependencies

class ViewAccessTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        # Profile created by signal
        cls.profile = Profile.objects.get(user=cls.user)
        cls.client = Client()
        cls.register_url = reverse('user_management:register')
        cls.login_url = reverse('user_management:login')
        cls.dashboard_url = reverse('user_management:dashboard')
        cls.update_profile_url = reverse('user_management:update_profile')

    def test_dashboard_redirects_if_not_logged_in(self):
        """Test dashboard view redirects to login if user is not authenticated."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302) # Should redirect
        # Default login URL usually contains settings.LOGIN_URL
        self.assertRedirects(response, f'{self.login_url}?next={self.dashboard_url}')

    def test_update_profile_redirects_if_not_logged_in(self):
        """Test update_profile view redirects to login if user is not authenticated."""
        response = self.client.get(self.update_profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'{self.login_url}?next={self.update_profile_url}')

    def test_register_page_accessible(self):
        """Test register view is accessible via GET."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_management/register.html')

    def test_login_page_accessible(self):
        """Test login view is accessible via GET."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html') # Check template name

class RegistrationViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('user_management:register')
        self.dashboard_url = reverse('user_management:dashboard')
        # Create an existing user to test conflicts
        User.objects.create_user(username='existinguser', email='existing@example.com', password='password123')

    def test_register_successful_post(self):
        """Test successful user registration via POST."""
        user_count_before = User.objects.count()
        profile_count_before = Profile.objects.count()
        response = self.client.post(self.register_url, {
            'username': 'newsignup',
            'email': 'newsignup@example.com',
            'password': 'password123',
        })

        self.assertEqual(User.objects.count(), user_count_before + 1)
        self.assertEqual(Profile.objects.count(), profile_count_before + 1)

        # Check if user is logged in after registration
        self.assertIn('_auth_user_id', self.client.session)

        # Check for redirect to dashboard
        self.assertRedirects(response, self.dashboard_url)

        # Optional: Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Account created for newsignup!") # Match your message text

    def test_register_username_taken_post(self):
        """Test registration POST with an existing username."""
        response = self.client.post(self.register_url, {
            'username': 'existinguser', # Already exists
            'email': 'newsignup@example.com',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 200) # Should re-render the form
        self.assertTemplateUsed(response, 'user_management/register.html')
        messages = list(response.context['messages'])
        self.assertTrue(any("Username already exists" in str(m) for m in messages))
        self.assertNotIn('_auth_user_id', self.client.session) # Should not be logged in

    def test_register_email_taken_post(self):
        """Test registration POST with an existing email."""
        response = self.client.post(self.register_url, {
            'username': 'newsignup',
            'email': 'existing@example.com', # Already exists
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_management/register.html')
        messages = list(response.context['messages'])
        self.assertTrue(any("Email already exists" in str(m) for m in messages))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_register_missing_fields_post(self):
        """Test registration POST with missing fields."""
        response = self.client.post(self.register_url, {
            'username': 'newsignup',
            # Missing email and password
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_management/register.html')
        messages = list(response.context['messages'])
        # Check your specific error messages from the view
        self.assertTrue(any("Email is required" in str(m) for m in messages))
        self.assertTrue(any("Password is required" in str(m) for m in messages))
        self.assertNotIn('_auth_user_id', self.client.session)


class DashboardViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123')
        cls.profile = Profile.objects.get(user=cls.user)
        # If UserLibraryItem is needed, create some test instances:
        # Assuming UserLibraryItem has fields 'user', 'media' (with sub-field 'media_type')
        # You might need to create dummy Media objects first
        # Example:
        # media_movie = Media.objects.create(title="Test Movie", media_type="movie")
        # media_book = Media.objects.create(title="Test Book", media_type="book")
        # UserLibraryItem.objects.create(user=cls.user, media=media_movie)
        # UserLibraryItem.objects.create(user=cls.user, media=media_book)

    def setUp(self):
        self.client = Client()
        self.client.login(username='testuser', password='password123')
        self.dashboard_url = reverse('user_management:dashboard')

    # Use patch if UserLibraryItem is complex or in another app you don't want to fully set up
    # @patch('user_management.views.UserLibraryItem') # Patch where it's used
    # def test_dashboard_view_get(self, MockUserLibraryItem):
        # # Setup mock return values
        # mock_manager = MockUserLibraryItem.objects.filter.return_value
        # mock_manager.__len__.side_effect = [2, 1, 0] # Example counts for movie, book, game

    def test_dashboard_view_get(self):
        """Test dashboard view for logged-in user."""
        # --- IF NOT MOCKING: Ensure you created necessary UserLibraryItem instances in setUpTestData ---

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_management/dashboard.html')
        self.assertEqual(response.context['username'], self.user.username)
        self.assertEqual(response.context['profile'], self.profile)

        # Check counts (these depend on UserLibraryItem setup or mocking)
        # Replace 0s with expected counts based on setUpTestData or mocks
        self.assertIn('movie_count', response.context)
        # self.assertEqual(response.context['movie_count'], 0)
        self.assertIn('book_count', response.context)
        # self.assertEqual(response.context['book_count'], 0)
        self.assertIn('game_count', response.context)
        # self.assertEqual(response.context['game_count'], 0)
        self.assertIn('all_count', response.context)
        # self.assertEqual(response.context['all_count'], 0)


class UpdateProfileViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123')
        cls.profile = Profile.objects.get(user=cls.user)

    def setUp(self):
        self.client = Client()
        self.client.login(username='testuser', password='password123')
        self.update_profile_url = reverse('user_management:update_profile')
        self.dashboard_url = reverse('user_management:dashboard')

    def test_update_profile_view_get(self):
        """Test update profile view GET request."""
        response = self.client.get(self.update_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_management/update_profile.html')
        self.assertIn('form', response.context)
        # Check if the form instance is correct
        self.assertEqual(response.context['form'].instance, self.profile)

    def test_update_profile_view_post_success(self):
        """Test update profile view POST request with valid data."""
        new_display_name = "Updated Name"
        response = self.client.post(self.update_profile_url, {
            'display_name': new_display_name
        })

        # Check for redirect to dashboard on success
        self.assertRedirects(response, self.dashboard_url)

        # Refresh profile from DB and check if updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_name, new_display_name)

        # Optional: Check for success message
        # Follow redirect to check messages on the *next* page
        response_redirected = self.client.get(self.dashboard_url)
        messages = list(response_redirected.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Profile updated successfully!')

    def test_update_profile_view_post_invalid(self):
        """Test update profile view POST request with invalid data (if possible)."""
        # Example: If display_name had max_length constraint smaller than this
        # invalid_name = "a" * 200
        # response = self.client.post(self.update_profile_url, {
        #     'display_name': invalid_name
        # })
        # self.assertEqual(response.status_code, 200) # Re-renders form
        # self.assertTemplateUsed(response, 'user_management/update_profile.html')
        # self.assertIn('form', response.context)
        # self.assertFalse(response.context['form'].is_valid())
        # self.assertIn('display_name', response.context['form'].errors)
        pass # Your current ProfileForm doesn't have much validation to test failure easily


# You might also want tests for the LoginView if you customized it significantly
# or just to ensure the login process works as expected.
class LoginViewTests(TestCase):
     @classmethod
     def setUpTestData(cls):
         cls.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')

     def setUp(self):
        self.client = Client()
        self.login_url = reverse('user_management:login')
        self.dashboard_url = reverse('user_management:dashboard') # Default success URL

     def test_login_success(self):
         """Test successful login."""
         response = self.client.post(self.login_url, {
             'username': 'testuser',
             'password': 'password123',
         })
         # Default success url for LoginView is settings.LOGIN_REDIRECT_URL
         # Check if you've overridden get_success_url
         # Here assuming it redirects to dashboard based on common practice
         # self.assertRedirects(response, settings.LOGIN_REDIRECT_URL) # Use this if default
         self.assertRedirects(response, self.dashboard_url) # Use this if dashboard is the target
         self.assertIn('_auth_user_id', self.client.session) # Check if logged in

     def test_login_failure_wrong_password(self):
         """Test login with incorrect password."""
         response = self.client.post(self.login_url, {
             'username': 'testuser',
             'password': 'wrongpassword',
         })
         self.assertEqual(response.status_code, 200) # Re-renders login form
         self.assertTemplateUsed(response, 'registration/login.html') # Or your custom template
         self.assertNotIn('_auth_user_id', self.client.session) # Should not be logged in
         self.assertContains(response, "Please enter a correct username and password.") # Check for error message

     def test_login_failure_wrong_username(self):
         """Test login with non-existent username."""
         response = self.client.post(self.login_url, {
             'username': 'nouser',
             'password': 'password123',
         })
         self.assertEqual(response.status_code, 200)
         self.assertTemplateUsed(response, 'registration/login.html')
         self.assertNotIn('_auth_user_id', self.client.session)
         self.assertContains(response, "Please enter a correct username and password.")