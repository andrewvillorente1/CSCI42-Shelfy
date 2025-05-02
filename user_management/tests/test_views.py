from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Profile
from unittest.mock import patch

class ViewAccessTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        cls.profile = Profile.objects.get(user=cls.user)
        cls.client = Client()
        cls.register_url = reverse('user_management:register')
        cls.login_url = reverse('user_management:login')
        cls.dashboard_url = reverse('user_management:dashboard')
        cls.update_profile_url = reverse('user_management:update_profile')

    def test_dashboard_redirects_if_not_logged_in(self):
        """Test dashboard view redirects to login if user is not authenticated."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302) 
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
        self.assertTemplateUsed(response, 'registration/login.html')

class RegistrationViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('user_management:register')
        self.dashboard_url = reverse('user_management:dashboard')
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
        self.assertIn('_auth_user_id', self.client.session)

        self.assertRedirects(response, self.dashboard_url)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Account created for newsignup!") 

    def test_register_username_taken_post(self):
        """Test registration POST with an existing username."""
        response = self.client.post(self.register_url, {
            'username': 'existinguser',
            'email': 'newsignup@example.com',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 200) 
        self.assertTemplateUsed(response, 'user_management/register.html')
        messages = list(response.context['messages'])
        self.assertTrue(any("Username already exists" in str(m) for m in messages))
        self.assertNotIn('_auth_user_id', self.client.session) 

    def test_register_email_taken_post(self):
        """Test registration POST with an existing email."""
        response = self.client.post(self.register_url, {
            'username': 'newsignup',
            'email': 'existing@example.com', 
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
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_management/register.html')
        messages = list(response.context['messages'])
        self.assertTrue(any("Email is required" in str(m) for m in messages))
        self.assertTrue(any("Password is required" in str(m) for m in messages))
        self.assertNotIn('_auth_user_id', self.client.session)


class DashboardViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123')
        cls.profile = Profile.objects.get(user=cls.user)

    def setUp(self):
        self.client = Client()
        self.client.login(username='testuser', password='password123')
        self.dashboard_url = reverse('user_management:dashboard')


    def test_dashboard_view_get(self):
        """Test dashboard view for logged-in user."""

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_management/dashboard.html')
        self.assertEqual(response.context['username'], self.user.username)
        self.assertEqual(response.context['profile'], self.profile)

        self.assertIn('movie_count', response.context)
        self.assertIn('book_count', response.context)
        self.assertIn('game_count', response.context)
        self.assertIn('all_count', response.context)

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

        response_redirected = self.client.get(self.dashboard_url)
        messages = list(response_redirected.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Profile updated successfully!')

    def test_update_profile_view_post_invalid(self):
        """Test update profile view POST request with invalid data (if possible)."""
        pass 


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
         self.assertRedirects(response, self.dashboard_url) 
         self.assertIn('_auth_user_id', self.client.session) 

     def test_login_failure_wrong_password(self):
         """Test login with incorrect password."""
         response = self.client.post(self.login_url, {
             'username': 'testuser',
             'password': 'wrongpassword',
         })
         self.assertEqual(response.status_code, 200) 
         self.assertTemplateUsed(response, 'registration/login.html')
         self.assertNotIn('_auth_user_id', self.client.session) 
         self.assertContains(response, "Please enter a correct username and password.") 

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