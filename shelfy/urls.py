"""
URL configuration for shelfy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from .views import MediaSearchView, MediaDetailView, home_view, SearchSuggestionsView, books_view, movies_view, games_view, media_detail_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user_management.urls')),
    path('library/', include('user_library.urls')),
    path("ai/", include("ai.urls")),
    path('socials/', include('socials.urls')),
    path('statistics/', include('charts.urls', namespace ='statistics')),
    # Home page URLs
    path('', home_view, name='home'),
    path('home/', home_view, name='home_alt'),

    # Search and detail URLs
    path('search/', MediaSearchView.as_view(), name='media_search'),
    path('<str:media_type>/<str:external_id>/',
         MediaDetailView.as_view(), name='media_detail'),

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='user_management/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='user_management/password_reset/password_reset_form.html'), 
        name='password_reset_form'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user_management/password_reset/password_reset_done.html'), 
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user_management/password_reset/password_reset_confirm.html'), 
        name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user_management/password_reset/password_reset_complete.html'), name='password_reset_complete'),


   # API endpoints for modal views
    path('api/media/<str:media_type>/<str:external_id>/', media_detail_api, name='media_detail_api'),

    path('books/', books_view, name='books'),
    path('movies/', movies_view, name='movies'),
    path('games/', games_view, name='games'),

]
