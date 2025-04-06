from django.urls import path
from charts import views
from .views import AverageRatingView, MovieCountView

app_name = 'charts'

urlpatterns = [
    path('all-statistics', AverageRatingView.as_view(), name='charts'),
    path('all-count', views.all_count, name='all_count'),
    path('all-ratings', views.all_ratings, name='all_ratings'),
    path('movies', MovieCountView.as_view(), name='movie'),
    path('movies-chart', views.movies_chart, name='movies_charts'),
    path('movies-rating', views.movies_ratings, name='movies_ratings'),
    path('movies-director', views.movies_directors, name='movies_directors'),
    path('movies-release', views.movies_release_years, name='movies_release')
]