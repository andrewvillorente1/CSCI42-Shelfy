from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import MediaSearchView, MediaDetailView, home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user_management.urls')),
    path('library/', include('user_library.urls')),

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
        template_name='user_management/password_reset/password_reset_form.html'), name='password_reset_form'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user_management/password_reset/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user_management/password_reset/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user_management/password_reset/password_reset_complete.html'), name='password_reset_complete'),
]
