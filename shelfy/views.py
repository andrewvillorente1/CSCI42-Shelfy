from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.models import User
from django.db import connection
import random
import json
from django.shortcuts import get_object_or_404
from .models import Media

# Import the MediaAPIClient
from .api_utils import MediaAPIClient
from .forms import CommentForms
from .models import Media, Comment


class MediaSearchView(View):
    def get(self, request):
        query = request.GET.get("q")
        media_type = request.GET.get("media_type", "")

        if not query:
            return render(request, "media/search.html", {"search_results": [], "query": query, "media_type": media_type})

        results = MediaAPIClient.search_media(query, media_type)
        return render(request, "media/search.html", {"search_results": results, "query": query, "media_type": media_type})


class SearchSuggestionsView(View):
    def get(self, request):
        query = request.GET.get("q", "")

        if not query or len(query) < 2:
            return JsonResponse({"suggestions": []})

        # Get suggestions from API (limit to 5 results)
        suggestions = []

        # Get book suggestions
        book_results = MediaAPIClient.search_media(query, "book")[:2]
        for book in book_results:
            suggestions.append({
                "title": book["title"],
                "media_type": "book",
                "external_id": book["external_id"],
                "image": book["cover_image"],
                "author": book.get("author", "")
            })

        # Get movie suggestions
        movie_results = MediaAPIClient.search_media(query, "movie")[:2]
        for movie in movie_results:
            suggestions.append({
                "title": movie["title"],
                "media_type": "movie",
                "external_id": movie["external_id"],
                "image": movie["cover_image"],
                "year": movie.get("release_year", "")
            })

        # Get game suggestions
        game_results = MediaAPIClient.search_media(query, "game")[:1]
        for game in game_results:
            suggestions.append({
                "title": game["title"],
                "media_type": "game",
                "external_id": game["external_id"],
                "image": game["cover_image"],
                "year": game.get("release_year", "")
            })

        return JsonResponse({"suggestions": suggestions})


class MediaDetailView(View):
    def get(self, request, media_type, external_id):
        details = MediaAPIClient.get_media_details(media_type, external_id)

        if not details:
            return JsonResponse({"error": "Media not found"}, status=404)
        
        media, created = Media.objects.get_or_create(
            external_id=external_id,
            media_type=media_type,
            defaults={
                "title": details["title"],
                "description": details["description"],
                "cover_image": details["cover_image"],
                "release_year": details.get("release_year", None),
                "genre": details.get("genre", ""),
                "author": details.get("author", ""),
            }
        )
        
        comments = Comment.objects.all()
    
        return render(request, "media/media_detail.html", {
            "media": media,
            "comments": comments,
        })
    
    def post(self, request, media_type, external_id): 
        details = MediaAPIClient.get_media_details(media_type, external_id)

        if not details:
            return JsonResponse({"error": "Media not found"}, status=404)
        
        media, created = Media.objects.get_or_create( #https://docs.djangoproject.com/en/5.1/ref/models/querysets/#get-or-create
            external_id=external_id,
            defaults={
                "title": details["title"],
                "description": details["description"],
                "cover_image": details["cover_image"],
                "release_year": details.get("release_year", None),
                "genre": details.get("genre", ""),
                "author": details.get("author", ""),
                "media_type": media_type,
            }
        )
        form = CommentForms(request.POST)
        if form.is_valid():
            comment = form.save(commit=False) #https://stackoverflow.com/questions/12848605/django-modelform-what-is-savecommit-false-used-for --> GETS YOU A MODEL OBJECT
            comment.media = media
            comment.comment_author = self.request.user.profile
            comment.save()
            return redirect('media_detail', media_type = media_type, external_id=comment.media.external_id)
        else:
            return render(request, "media/media_detail.html", {"media": media, "form": form, "media_type": media_type, "external_id": external_id})



def home_view(request):
    """
    Enhanced home view that displays dynamic content from APIs and database.
    """
    context = {}

    # Get user statistics from database
    try:
        with connection.cursor() as cursor:
            # Count total users
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            context['total_users'] = cursor.fetchone()[0]

            # Get newest user
            cursor.execute(
                "SELECT username FROM auth_user ORDER BY date_joined DESC LIMIT 1")
            newest_user = cursor.fetchone()
            if newest_user:
                context['newest_user'] = newest_user[0]
    except Exception as e:
        print(f"Error getting user stats: {e}")
        context['total_users'] = 0

    # Get media statistics from database
    try:
        with connection.cursor() as cursor:
            # Check if media_search_media table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='media_search_media'")
            if cursor.fetchone():
                # Get total media count
                cursor.execute("SELECT COUNT(*) FROM media_search_media")
                context['total_media'] = cursor.fetchone()[0]

                # Get counts by media type
                cursor.execute("""
                  SELECT media_type, COUNT(*) as count 
                  FROM media_search_media 
                  GROUP BY media_type
              """)
                media_counts = {row[0]: row[1] for row in cursor.fetchall()}
                context['media_counts'] = media_counts

                # Get recent media
                cursor.execute("""
                  SELECT id, title, media_type, external_id, cover_image, release_year
                  FROM media_search_media
                  ORDER BY id DESC
                  LIMIT 6
              """)
                columns = [col[0] for col in cursor.description]
                context['recent_media'] = [
                    dict(zip(columns, row)) for row in cursor.fetchall()
                ]
    except Exception as e:
        print(f"Error getting media stats: {e}")

    # Get library statistics from database
    try:
        with connection.cursor() as cursor:
            # Check if user_library_libraryentry table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_library_libraryentry'")
            if cursor.fetchone():
                # Count total library entries
                cursor.execute(
                    "SELECT COUNT(*) FROM user_library_libraryentry")
                context['total_library_entries'] = cursor.fetchone()[0]

                # Count entries by status
                cursor.execute("""
                  SELECT status, COUNT(*) as count 
                  FROM user_library_libraryentry 
                  GROUP BY status
              """)
                status_counts = {row[0]: row[1] for row in cursor.fetchall()}
                context['status_counts'] = status_counts

                # Get popular media (most added to libraries)
                cursor.execute("""
                  SELECT m.id, m.title, m.media_type, m.external_id, m.cover_image, COUNT(*) as count
                  FROM media_search_media m
                  JOIN user_library_libraryentry l ON m.id = l.media_id
                  GROUP BY m.id
                  ORDER BY count DESC
                  LIMIT 6
              """)
                columns = [col[0] for col in cursor.description]
                context['popular_media'] = [
                    dict(zip(columns, row)) for row in cursor.fetchall()
                ]

                # Get recently completed media
                cursor.execute("""
                  SELECT m.id, m.title, m.media_type, m.external_id, m.cover_image, l.rating
                  FROM media_search_media m
                  JOIN user_library_libraryentry l ON m.id = l.media_id
                  WHERE l.status = 'completed'
                  ORDER BY l.updated_at DESC
                  LIMIT 6
              """)
                columns = [col[0] for col in cursor.description]
                context['completed_media'] = [
                    dict(zip(columns, row)) for row in cursor.fetchall()
                ]

                # If user is logged in, get their library items for personalized recommendations
                if request.user.is_authenticated:
                    cursor.execute("""
                      SELECT m.media_type, m.genre
                      FROM media_search_media m
                      JOIN user_library_libraryentry l ON m.id = l.media_id
                      WHERE l.user_id = %s AND l.rating >= 4
                      LIMIT 10
                  """, [request.user.id])
                    user_preferences = cursor.fetchall()
                    context['has_preferences'] = len(user_preferences) > 0
    except Exception as e:
        print(f"Error getting library stats: {e}")

    # Get dynamic content from APIs

    # Trending books
    trending_books = MediaAPIClient.search_media("bestseller", "book")[:6]
    context['trending_books'] = trending_books

    # Trending movies
    trending_movies = MediaAPIClient.search_media("popular", "movie")[:6]
    context['trending_movies'] = trending_movies

    # Trending games
    trending_games = MediaAPIClient.search_media("top rated", "game")[:6]
    context['trending_games'] = trending_games

    # Personalized recommendations based on user preferences
    if request.user.is_authenticated and context.get('has_preferences', False):
        # This would ideally use the user's preferences to make targeted API calls
        # For now, we'll just use some generic recommendations
        recommended_books = MediaAPIClient.search_media(
            "recommended fiction", "book")[:6]
        recommended_movies = MediaAPIClient.search_media(
            "must watch", "movie")[:6]
        recommended_games = MediaAPIClient.search_media("must play", "game")[
            :6]

        context['recommended_media'] = recommended_books + \
            recommended_movies + recommended_games
        random.shuffle(context['recommended_media'])
        context['recommended_media'] = context['recommended_media'][:6]

    # Friend recommendations (simulated)
    # In a real app, this would query friends' highly rated items
    friend_recommendations = []
    friend_books = MediaAPIClient.search_media("award winning", "book")[:2]
    friend_movies = MediaAPIClient.search_media(
        "critically acclaimed", "movie")[:2]
    friend_games = MediaAPIClient.search_media("indie", "game")[:2]

    for item in friend_books + friend_movies + friend_games:
        item['friend'] = random.choice(
            ["Alex", "Jordan", "Taylor", "Casey", "Morgan"])
        friend_recommendations.append(item)

    context['friend_recommendations'] = friend_recommendations

    return render(request, 'home.html', context)


def books_view(request):
    """
    View for displaying books.
    """
    # Get books from API
    books = MediaAPIClient.search_media("bestseller", "book")[:12]

    # Additional categories
    fiction_books = MediaAPIClient.search_media("fiction", "book")[:6]
    nonfiction_books = MediaAPIClient.search_media("nonfiction", "book")[:6]
    classic_books = MediaAPIClient.search_media(
        "classic literature", "book")[:6]

    context = {
        'books': books,
        'fiction_books': fiction_books,
        'nonfiction_books': nonfiction_books,
        'classic_books': classic_books,
        'media_type': 'book'
    }

    return render(request, 'media/books.html', context)


def movies_view(request):
    """
    View for displaying movies.
    """
    # Get movies from API
    movies = MediaAPIClient.search_media("popular", "movie")[:12]

    # Additional categories
    action_movies = MediaAPIClient.search_media("action", "movie")[:6]
    comedy_movies = MediaAPIClient.search_media("comedy", "movie")[:6]
    scifi_movies = MediaAPIClient.search_media("science fiction", "movie")[:6]

    context = {
        'movies': movies,
        'action_movies': action_movies,
        'comedy_movies': comedy_movies,
        'scifi_movies': scifi_movies,
        'media_type': 'movie'
    }

    return render(request, 'media/movies.html', context)


def games_view(request):
    """
    View for displaying games.
    """
    # Get games from API
    games = MediaAPIClient.search_media("top rated", "game")[:12]

    # Additional categories
    rpg_games = MediaAPIClient.search_media("rpg", "game")[:6]
    action_games = MediaAPIClient.search_media("action", "game")[:6]
    indie_games = MediaAPIClient.search_media("indie", "game")[:6]

    context = {
        'games': games,
        'rpg_games': rpg_games,
        'action_games': action_games,
        'indie_games': indie_games,
        'media_type': 'game'
    }

    return render(request, 'media/games.html', context)

def media_detail_api(request, media_type, external_id):
    """API endpoint to get media details for the modal view"""
    media = get_object_or_404(Media, media_type=media_type, external_id=external_id)
    
    # Return media details as JSON
    return JsonResponse({
        'title': media.title,
        'cover_image': media.cover_image,
        'description': media.description,
        'author': media.author,
        'director': media.director,
        'studio': media.studio,
        'release_year': media.release_year,
        'genre': media.genre,
        'media_type': media.media_type,
        'external_id': media.external_id,
    })


