from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.views import LoginView
from user_library.models import UserLibraryItem
from .models import Profile
from .forms import ProfileForm, UserRegistrationForm
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Custom login view
class CustomLoginView(LoginView):
    template_name = 'user_management/login.html'
    
    def get_success_url(self):
        next_url = self.request.POST.get('next', None)
        if next_url:
            return next_url
        return super().get_success_url()

# Add CSRF cookie to ensure it's available
@ensure_csrf_cookie
def register(request):
    if request.method == 'POST':
        # Get form data directly from POST
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Basic validation
        errors = []
        if not username:
            errors.append("Username is required")
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            errors.append("Username already exists")
        if User.objects.filter(email=email).exists():
            errors.append("Email already exists")
            
        # If no errors, create user
        if not errors:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Create profile
                Profile.objects.create(user=user)
                
                # Log the user in
                login(request, user)
                
                # Redirect to dashboard
                messages.success(request, f"Account created for {username}!")
                return redirect('user_management:dashboard')
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                errors.append(f"Error creating account: {str(e)}")
        
        # If there are errors, display them
        for error in errors:
            messages.error(request, error)
            
    # For GET requests or if POST had errors
    return render(request, 'user_management/register.html')

@login_required
def dashboard(request):
    user_profile = Profile.objects.get(user=request.user)
    movie_count = len(UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="movie"))
    book_count = len(UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="book"))
    game_count = len(UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="game"))
    all_count = movie_count + book_count + game_count
    context = {
        'username': request.user.username,
        'profile': user_profile,
        'movie_count': movie_count,
        'book_count': book_count,
        'game_count': game_count,
        'all_count': all_count,
    }
    return render(request, 'user_management/dashboard.html', context)

@login_required
def update_profile(request):
    user_profile = Profile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_management:dashboard')
    else:
        form = ProfileForm(instance=user_profile)
    
    return render(request, 'user_management/update_profile.html', {'form': form})

