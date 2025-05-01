from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import MediaSearchView, MediaDetailView, home_view, SearchSuggestionsView, books_view, movies_view, games_view, media_detail_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('library/', include('user_library.urls')),
    path('user/', include('user_management.urls')),
    path('statistics/', include('charts.urls')),
    path('ai/', include('ai.urls')),
    path('socials/', include('socials.urls')),
    # Add this line to include shelves URLs
    path('shelf/', include('shelves.urls')),
    # Home page URLs
    path('home/', home_view, name='home_alt'),

    # Search and detail URLs
    path('search/', views.media_search, name='media_search'),
    path('search/suggestions/', SearchSuggestionsView.as_view(),
         name='search_suggestions'),
    path('<str:media_type>/<str:external_id>/',
         MediaDetailView.as_view(), name='media_detail'),
    path('book/<str:book_id>/', views.book_detail, name='book_detail'),
    path('movie/<str:movie_id>/', views.movie_detail, name='movie_detail'),
    path('game/<str:game_id>/', views.game_detail, name='game_detail'),

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
    path('api/media/<str:media_type>/<str:external_id>/',
         media_detail_api, name='media_detail_api'),

    path('books/', books_view, name='books'),
    path('movies/', movies_view, name='movies'),
    path('games/', games_view, name='games'),
    path('shelf/', include('shelves.urls', namespace='shelves')),
    path('comments/', views.comments, name='comments'),
    path('comments/add/', views.add_comment, name='add_comment'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
