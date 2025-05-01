
from django.test import TestCase
from django.contrib.auth.models import User
from ..forms import ProfileForm, UserRegistrationForm
from ..models import Profile

class ProfileFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password123')
        # Profile is created by signal
        cls.profile = Profile.objects.get(user=cls.user)

    def test_profile_form_valid(self):
        """Test ProfileForm with valid data."""
        form_data = {'display_name': 'New Display Name'}
        form = ProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())

    def test_profile_form_save(self):
        """Test saving the ProfileForm."""
        new_display_name = "Saved Name"
        form_data = {'display_name': new_display_name}
        form = ProfileForm(data=form_data, instance=self.profile)
        if form.is_valid():
            form.save()
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.display_name, new_display_name)
        else:
            self.fail(f"ProfileForm was not valid: {form.errors}")

    # Add more tests if ProfileForm had more fields or complex validation

class UserRegistrationFormTests(TestCase):

    def test_registration_form_valid(self):
        """Test UserRegistrationForm with valid data."""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_registration_form_missing_data(self):
        """Test UserRegistrationForm with missing fields."""
        form_data = {'username': 'newuser'} # Missing email and password
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('password', form.errors)

    def test_registration_form_username_taken(self):
        """Test UserRegistrationForm with an already existing username."""
        User.objects.create_user(username='existinguser', password='password123')
        form_data = {
            'username': 'existinguser', # This username already exists
            'email': 'new@example.com',
            'password': 'password123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'], ["This username is already taken."])

    def test_registration_form_email_taken(self):
        """Test UserRegistrationForm with an already existing email."""
        User.objects.create_user(username='anotheruser', password='password123', email='existing@example.com')
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com', # This email already exists
            'password': 'password123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'], ["This email is already registered."])