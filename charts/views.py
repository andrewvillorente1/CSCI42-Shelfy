from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Max, Value, CharField, Avg
from django.db.models.functions import Concat

from user_library.models import UserLibraryItem
from django.http import JsonResponse
from collections import defaultdict


class AverageRatingView(ListView):
    model = UserLibraryItem
    template_name = "chartjs/index.html"

    def get_context_data(self, **kwargs): # from Django Book/ Lecture
        context = super().get_context_data(**kwargs) #overides the other get_context
        # Average star ratings across all media
        rating = UserLibraryItem.objects.values_list("rating", flat=True)
        rating = list(filter(None, rating))
        # Gets All Movie ratings
        movie_rating = UserLibraryItem.objects.filter(media__media_type__iexact="movie").values_list("rating", flat=True)
        movie_rating = list(filter(None, movie_rating))
        # Gets All Book ratings
        book_rating = UserLibraryItem.objects.filter(media__media_type__iexact="book").values_list("rating", flat=True)
        book_rating = list(filter(None, book_rating))
        # Gets All Game ratings
        game_rating = UserLibraryItem.objects.filter(media__media_type__iexact="game").values_list("rating", flat=True)
        game_rating = list(filter(None, game_rating))
        # Gets Average star ratings of each component, rounded up by 2 decimals
        context['rating'] = round(sum(rating)/len(rating),2)
        context['movie_rating'] = round(sum(movie_rating)/len(movie_rating),2)
        context['book_rating'] = round(sum(book_rating)/len(book_rating),2)
        context['game_rating'] = round(sum(game_rating)/len(game_rating),2)
        movie_count = len(UserLibraryItem.objects.filter(media__media_type__iexact="movie"))
        context['movie_count'] = movie_count
        
        return context

def all_count(request):
    movie_count = len(UserLibraryItem.objects.filter(media__media_type__iexact="movie"))
    book_count = len(UserLibraryItem.objects.filter(media__media_type__iexact="book"))
    game_count = len(UserLibraryItem.objects.filter(media__media_type__iexact="game"))

    return JsonResponse(data={
        'movie_count': movie_count,
        'book_count': book_count,
        'game_count': game_count
    }) 

def all_ratings(request):
    ratings_count = defaultdict(int)

    all_rating = UserLibraryItem.objects.values_list("rating", flat=True)
    all_rating = list(filter(None, all_rating))
    # Gets All Movie ratings
    movie_ratings_count = defaultdict(int)
    movie_rating = UserLibraryItem.objects.filter(media__media_type__iexact="movie").values_list("rating", flat=True)
    movie_rating = list(filter(None, movie_rating))
    # Gets All Book ratings
    book_ratings_count = defaultdict(int)
    book_rating = UserLibraryItem.objects.filter(media__media_type__iexact="book").values_list("rating", flat=True)
    book_rating = list(filter(None, book_rating))
    # Gets All Game ratings
    game_ratings_count = defaultdict(int)
    game_rating = UserLibraryItem.objects.filter(media__media_type__iexact="game").values_list("rating", flat=True)
    game_rating = list(filter(None, game_rating))

    for rate in all_rating:
        ratings_count[rate]+=1
    for rate in movie_rating:
        movie_ratings_count[rate]+=1
    for rate in book_rating:
        book_ratings_count[rate]+=1
    for rate in game_rating:
        game_ratings_count[rate]+=1

    #for rate in all_rating:
        # if the a game has been rated, rate, add +1 to game_ratings_count[rate]
        # else, initialize as 0

    for rate in all_rating:
        if not movie_ratings_count[rate]:
            movie_ratings_count[rate] == 0
        if not book_ratings_count[rate]:
            book_ratings_count[rate] == 0
        if not game_ratings_count[rate]:
            game_ratings_count[rate] == 0
        
        


    rating = list(ratings_count.keys())
    all_counts = list(ratings_count.values())

    ratings_all_data = list(zip(rating,all_counts))
    
    ratings_all_data.sort(key=lambda x: x[0])

    sorted_rating, sorted_rating_counts = zip(*ratings_all_data)

    # return JsonResponse(data={
    #     'rating': sorted_rating,
    #     'movie': sorted_rating_counts
    # })

    movies = list(movie_ratings_count.keys())
    movies_count = list(movie_ratings_count.values())

    books = list(book_ratings_count.keys())
    books_count = list(book_ratings_count.values())

    games = list(game_ratings_count.keys())
    games_count = list(game_ratings_count.values())

    movies_count_data = list(zip(movies, movies_count))
    books_count_data = list(zip(books, books_count))
    games_count_data = list(zip(games, games_count))

    movies_count_data.sort(key=lambda x: x[0])
    books_count_data.sort(key=lambda x: x[0])
    games_count_data.sort(key=lambda x: x[0])

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

class MovieCountView(ListView):
    model = UserLibraryItem
    template_name = "chartjs/movies.html"

    def get_context_data(self, **kwargs): # from Django Book/ Lecture
        context = super().get_context_data(**kwargs) #overides the other get_context
        movie_count = len(UserLibraryItem.objects.filter(media__media_type__iexact="movie"))
        movie_rating = UserLibraryItem.objects.filter(media__media_type__iexact="movie").values_list("rating", flat=True)
        movie_rating = list(filter(None, movie_rating))
        context['movie_count'] = movie_count
        context['movie_rating'] = round(sum(movie_rating)/len(movie_rating),2)
        
        return context
    

def movies_chart(request):
    # Storing genre and corresponding number of movies with that genre
    genre_count = defaultdict(int)
    
    # Query all movies
    movie_genre = UserLibraryItem.objects.filter(media__media_type__iexact="movie")
    
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

    # Unzip the sorted data into separate lists again
    sorted_genres, sorted_movie_counts = zip(*genre_movie_data)

    return JsonResponse(data={
        'genre': list(sorted_genres),
        'movie': list(sorted_movie_counts),
    })

def movies_ratings(request):
    ratings_count = defaultdict(int)

    movie_rating = UserLibraryItem.objects.filter(media__media_type__iexact="movie").values_list("rating", flat=True)

    for rate in movie_rating:
        ratings_count[rate]+=1
    
    rating = list(ratings_count.keys())
    movie_counts = list(ratings_count.values())

    ratings_movie_data = list(zip(rating, movie_counts))
    
    ratings_movie_data.sort(key=lambda x: x[0])

    sorted_rating, sorted_rating_counts = zip(*ratings_movie_data)

    return JsonResponse(data={
        'rating': sorted_rating,
        'movie': sorted_rating_counts
    })

def movies_directors(request):
    director_count = defaultdict(int)
    
    movie_directors = UserLibraryItem.objects.filter(media__media_type__iexact="movie")
    
    for entry in movie_directors:
        # # Splitting the list of genres if a movie has more than one genre
        # directors = entry.media.director.split(",")
        
        # # Increment the count for each genre
        # for director in directors:
        #     director_count[director.strip()] += 1  # Cleans whitespace between genres
        director_count[entry.media.director] += 1

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

def movies_release_years(request):
    release_year_count = defaultdict(int)
    
    release_years = UserLibraryItem.objects.filter(media__media_type__iexact="movie")
    
    for entry in release_years:
        release_year_count[entry.media.release_year] += 1
    
    years = list(release_year_count.keys())
    years_count = list(release_year_count.values())

    release_year_movie_data = list(zip(years, years_count))
    
    release_year_movie_data.sort(key=lambda x: x[0])

    sorted_years, sorted_years_counts = zip(*release_year_movie_data)

    return JsonResponse(data={
        'release_year': list(sorted_years),
        'movie': list(sorted_years_counts),
    })