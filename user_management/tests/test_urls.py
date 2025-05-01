from django.test import SimpleTestCase
from django.urls import reverse, resolve
from ..views import update_profile, register, dashboard # Import your actual view functions/classes
# Import the built-in LoginView if you are using it directly in urls.py
from django.contrib.auth.views import LoginView

class UrlResolveTests(SimpleTestCase):

    def test_update_profile_url_resolves(self):
        """Test that the 'update_profile' URL resolves to the correct view."""
        url = reverse('user_management:update_profile')
        # Use resolve(url).func for function views
        # Use resolve(url).func.view_class for class-based views' .as_view()
        self.assertEqual(resolve(url).func, update_profile)

    def test_register_url_resolves(self):
        """Test that the 'register' URL resolves to the correct view."""
        url = reverse('user_management:register')
        self.assertEqual(resolve(url).func, register)

    def test_dashboard_url_resolves(self):
        """Test that the 'dashboard' URL resolves to the correct view."""
        url = reverse('user_management:dashboard')
        self.assertEqual(resolve(url).func, dashboard)

    def test_login_url_resolves(self):
        """Test that the 'login' URL resolves to the correct view."""
        url = reverse('user_management:login')
        # For Django's built-in views used with .as_view()
        self.assertEqual(resolve(url).func.view_class, LoginView)

    # Add tests for any other URLs you have in user_management/urls.py