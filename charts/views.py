from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.list import ListView

# from django.views.generic.edit import CreateView, UpdateView, DeleteView

# from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# from django.db.models import Max, Value, CharField, Avg
# from django.db.models.functions import Concat

from user_library.models import UserLibraryItem
from django.http import JsonResponse
from collections import defaultdict


'''
Helper functions set-up
'''

def sort_data(rating_data):
    return sorted(rating_data.items())

def get_average_rating(request, media_type=None):
    """
    Helper function to calculate the average rating for a given media type.
    If no media_type is given, it calculates the average across all media types.
    """
    if media_type:
        ratings = UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact=media_type).values_list("rating", flat=True)
    else:
        ratings = UserLibraryItem.objects.filter(user=request.user).values_list("rating", flat=True)
    
    ratings = list(filter(None, ratings))
    return round(sum(ratings) / len(ratings), 2) if ratings else 0

def count_ratings(ratings_query):
    """
    Helper function to count ratings from a queryset.
    """
    ratings_count = defaultdict(int)
    ratings = list(filter(None, ratings_query))

    for rate in ratings:
        ratings_count[rate] += 1

    # makes sure that all ratings have a value
    for rating in range(1, 6):
        if rating not in ratings_count:
            ratings_count[rating] = 0

    return ratings_count

def count_release_years(ratings_query):
    """
    Helper function to count release years from a queryset.
    """
    years_count = defaultdict(int)
    years = list(filter(None, ratings_query))

    for year in years:
        years_count[year.media.release_year] += 1

    return years_count


''' Classes '''
class AllView(ListView):
    model = UserLibraryItem
    template_name = "chartjs/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get average ratings for each media type
        context['rating'] = get_average_rating(self.request)
        context['movie_rating'] = get_average_rating(self.request, 'movie')
        context['book_rating'] = get_average_rating(self.request, 'book')
        context['game_rating'] = get_average_rating(self.request, 'game')

        return context
    

class MovieView(ListView):
    model = UserLibraryItem
    template_name = "chartjs/movies.html"

    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs)
        movie_count = len(UserLibraryItem.objects.filter(user=self.request.user, media__media_type__iexact="movie"))
        context['movie_count'] = movie_count
        context['movie_rating'] = get_average_rating(self.request, 'movie')
        
        return context
    

class BookView(ListView):
    model = UserLibraryItem
    template_name = "chartjs/books.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        book_count = len(UserLibraryItem.objects.filter(user=self.request.user, media__media_type__iexact="book"))
        context['book_count'] = book_count
        context['book_rating'] = get_average_rating(self.request, 'book')
        
        return context
    
class GameView(ListView):
    model = UserLibraryItem
    template_name = "chartjs/games.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game_count = len(UserLibraryItem.objects.filter(user=self.request.user, media__media_type__iexact="game"))
        context['game_count'] = game_count
        context['game_rating'] = get_average_rating(self.request, 'game')
        
        return context
    
# Count of All Media Types
def all_count(request):
    movie_count = len(UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="movie"))
    book_count = len(UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="book"))
    game_count = len(UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="game"))

    return JsonResponse(data={
        'movie_count': movie_count,
        'book_count': book_count,
        'game_count': game_count
    }) 


''' Functions for Ratings '''
# Count of all ratings across all media types
def all_ratings(request):
    # Get all ratings
    all_ratings = UserLibraryItem.objects.filter(user = request.user).values_list("rating", flat=True)

    # Get ratings per media type
    movie_ratings_count = count_ratings(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="movie").values_list("rating", flat=True)
    )
    book_ratings_count = count_ratings(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="book").values_list("rating", flat=True)
    )
    game_ratings_count = count_ratings(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="game").values_list("rating", flat=True)
    )

    # Get the overall ratings count
    ratings_count = count_ratings(all_ratings)

    # Prepare the data for the response
    ratings_all_data = sort_data(ratings_count)
    movies_count_data = sort_data(movie_ratings_count)
    books_count_data = sort_data(book_ratings_count)
    games_count_data = sort_data(game_ratings_count)

    # Unzip the sorted data into separate lists for ratings and counts
    sorted_rating, sorted_rating_counts = zip(*ratings_all_data)
    sorted_movies, sorted_movies_count = zip(*movies_count_data)
    sorted_books, sorted_books_count = zip(*books_count_data)
    sorted_games, sorted_games_count = zip(*games_count_data)

    return JsonResponse(data={
        'rating': sorted_rating,
        'movie_rating': sorted_movies,
        'movie': sorted_movies_count,
        'book_rating': sorted_books,
        'book': sorted_books_count,
        'game_rating': sorted_games,
        'game': sorted_games_count
    })
    
# count of movie ratings
def movies_ratings(request):
    movie_ratings_count = count_ratings(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="movie").values_list("rating", flat=True)
    )
    
    movies_count_data = sort_data(movie_ratings_count)

    sorted_rating, sorted_rating_counts = zip(*movies_count_data)

    return JsonResponse(data={
        'rating': sorted_rating,
        'movie': sorted_rating_counts
    })

def books_ratings(request):
    book_ratings_count = count_ratings(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="book").values_list("rating", flat=True)
    )
    
    books_count_data = sort_data(book_ratings_count)

    sorted_rating, sorted_rating_counts = zip(*books_count_data)

    return JsonResponse(data={
        'rating': sorted_rating,
        'book': sorted_rating_counts
    })

def games_ratings(request):
    ratings_count = count_ratings(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="game").values_list("rating", flat=True)
    )
    
    count_data = sort_data(ratings_count)

    sorted_rating, sorted_rating_counts = zip(*count_data)

    return JsonResponse(data={
        'rating': sorted_rating,
        'game': sorted_rating_counts
    })

''' Functions for genres '''
# count of movie genres

def movies_chart(request):
    # Storing genre and corresponding number of movies with that genre
    genre_count = defaultdict(int)
    
    # Query all movies
    movie_genre = UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="movie")

    
    # Count the number of movies in each genre
    for entry in movie_genre:
        # Splitting the list of genres if a movie has more than one genre
        genres = entry.media.genre.split(",")
        
        # Increment the count for each genre
        for genre in genres:
            genre_count[genre.strip()] += 1  # Cleans whitespace between genres
    


    # Prepare the genre and movie count lists
    genres = list(genre_count.keys())
    movie_counts = list(genre_count.values())

    # Combine genre and movie count into a list of tuples
    genre_movie_data = list(zip(genres, movie_counts))
    
    # Sort the list by movie counts in descending order
    genre_movie_data.sort(key=lambda x: x[1], reverse=True)

    top_10_genres_movies = genre_movie_data

    # Unzip the sorted data into separate lists again
    sorted_genres, sorted_movie_counts = zip(*top_10_genres_movies)


    return JsonResponse(data={
        'genre': list(sorted_genres),
        'movie': list(sorted_movie_counts),
    })


def books_chart(request):
    genre_count = defaultdict(int)
    
    book_genre = UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="book")
    
    for entry in book_genre:
        genres = entry.media.genre.split("/")
        
        for genre in genres:
            genre_count[genre.strip()] += 1 
    
    genres = list(genre_count.keys())
    book_counts = list(genre_count.values())
    genre_book_data = list(zip(genres, book_counts))
    
    genre_book_data.sort(key=lambda x: x[1], reverse=True)
    top_10_genres_books = genre_book_data[:10]

    sorted_genres, sorted_book_counts = zip(*top_10_genres_books)

    return JsonResponse(data={
        'genre': list(sorted_genres),
        'book': list(sorted_book_counts),
    })

def games_chart(request):
    genre_count = defaultdict(int)
    
    game_genre = UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="game")
    
    for entry in game_genre:
        genres = entry.media.genre.split(",")
        
        for genre in genres:
            genre_count[genre.strip()] += 1 
    
    genres = list(genre_count.keys())
    game_counts = list(genre_count.values())
    genre_game_data = list(zip(genres, game_counts))
    
    genre_game_data.sort(key=lambda x: x[1], reverse=True)
    top_10_genres_games = genre_game_data[:10]

    sorted_genres, sorted_game_counts = zip(*top_10_genres_games)

    return JsonResponse(data={
        'genre': list(sorted_genres),
        'game': list(sorted_game_counts),
    })

'''
Functions for Release Years
'''

def movies_release_years(request):
    movie_release_years_count = count_release_years(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="movie")
    )
    
    movies_count_data = sort_data(movie_release_years_count)

    sorted_years, sorted_rating_counts = zip(*movies_count_data)

    return JsonResponse(data={
        'release_year': sorted_years,
        'movie': sorted_rating_counts
    })

def books_release_years(request):
    book_release_years_count = count_release_years(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="book")
    )
    
    books_count_data = sort_data(book_release_years_count)

    sorted_years, sorted_rating_counts = zip(*books_count_data)

    return JsonResponse(data={
        'release_year': sorted_years,
        'book': sorted_rating_counts
    })

def games_release_years(request):
    release_years_count = count_release_years(
        UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="game")
    )
    
    count_data = sort_data(release_years_count)

    sorted_years, sorted_rating_counts = zip(*count_data)

    return JsonResponse(data={
        'release_year': sorted_years,
        'game': sorted_rating_counts
    })

'''
functions that are not final 
(Directors/Authors/Publishers)
'''

def movies_directors(request):
    director_count = defaultdict(int)
    
    movie_directors = UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="movie")
    
    for entry in movie_directors:
        if entry.media.studio:
            directors = entry.media.studio
            director_count[directors] += 1
        else:
            directors = "Unknown"
            director_count[directors] += 1

    # Prepare the genre and movie count lists
    directors = list(director_count.keys())
    director_counts = list(director_count.values())

    # Combine genre and movie count into a list of tuples
    director_movie_data = list(zip(directors, director_counts))
    
    # Sort the list by movie counts in descending order
    director_movie_data.sort(key=lambda x: x[1], reverse=True)

    # Unzip the sorted data into separate lists again
    sorted_directors, sorted_movie_counts = zip(*director_movie_data)

    return JsonResponse(data={
        'director': list(sorted_directors),
        'movie': list(sorted_movie_counts),
    })

def books_authors(request):
    director_count = defaultdict(int)
    
    movie_directors = UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="book")
    
    for entry in movie_directors:
        # Splitting the list of genres if a movie has more than one genre
        directors = entry.media.author.split(',')
        
        # Increment the count for each genre
        for director in directors:
            director_count[director.strip()] += 1  # Cleans whitespace between genres
        # director_count[entry.media.author] += 1

    # Prepare the genre and movie count lists
    directors = list(director_count.keys())
    director_counts = list(director_count.values())

    # Combine genre and movie count into a list of tuples
    director_movie_data = list(zip(directors, director_counts))
    
    # Sort the list by movie counts in descending order
    director_movie_data.sort(key=lambda x: x[1], reverse=True)

    # Unzip the sorted data into separate lists again
    sorted_directors, sorted_movie_counts = zip(*director_movie_data)

    return JsonResponse(data={
        'author': list(sorted_directors),
        'book': list(sorted_movie_counts),
    })

def games_studio(request):
    director_count = defaultdict(int)
    
    movie_directors = UserLibraryItem.objects.filter(user=request.user, media__media_type__iexact="game")
    
    for entry in movie_directors:
        # # Splitting the list of genres if a movie has more than one genre
        if entry.media.studio:
            directors = entry.media.studio
            director_count[directors] += 1
        else:
            directors = "Unknown"
            director_count[directors] += 1
            

    # Prepare the genre and movie count lists
    directors = list(director_count.keys())
    director_counts = list(director_count.values())

    # Combine genre and movie count into a list of tuples
    director_movie_data = list(zip(directors, director_counts))
    
    # Sort the list by movie counts in descending order
    director_movie_data.sort(key=lambda x: x[1], reverse=True)

    # Unzip the sorted data into separate lists again
    sorted_directors, sorted_movie_counts = zip(*director_movie_data)

    return JsonResponse(data={
        'studio': list(sorted_directors),
        'game': list(sorted_movie_counts),
    })