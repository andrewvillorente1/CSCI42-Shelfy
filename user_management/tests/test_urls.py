from django.test import SimpleTestCase
from django.urls import reverse, resolve
from ..views import update_profile, register, dashboard
from django.contrib.auth.views import LoginView

class UrlResolveTests(SimpleTestCase):

    def test_update_profile_url_resolves(self):
        """Test that the 'update_profile' URL resolves to the correct view."""
        url = reverse('user_management:update_profile')
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
        self.assertEqual(resolve(url).func.view_class, LoginView)