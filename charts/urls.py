from django.urls import path
from charts import views
from .views import AllView, MovieView, BookView, GameView

app_name = 'charts'

urlpatterns = [
    path('all-statistics', AllView.as_view(), name='charts'),
    path('all-count', views.all_count, name='all_count'),
    path('all-ratings', views.all_ratings, name='all_ratings'),
    path('movies', MovieView.as_view(), name='movie'),
    path('movies-chart', views.movies_chart, name='movies_charts'),
    path('movies-rating', views.movies_ratings, name='movies_ratings'),
    path('movies-director', views.movies_directors, name='movies_directors'),
    path('movies-release', views.movies_release_years, name='movies_release'),
    path('books', BookView.as_view(), name='book'),
    path('books-chart', views.books_chart, name='books_charts'),
    path('books-rating', views.books_ratings, name='books_ratings'),
    path('books-author', views.books_authors, name='books_authors'),
    path('books-release', views.books_release_years, name='books_release'),
    path('games', GameView.as_view(), name='game'),
    path('games-chart', views.games_chart, name='games_charts'),
    path('games-rating', views.games_ratings, name='games_ratings'),
    path('games-studio', views.games_studio, name='games_studio'),
    path('games-release', views.games_release_years, name='games_release'),
]