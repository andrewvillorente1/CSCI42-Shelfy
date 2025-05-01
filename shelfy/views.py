from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.models import User
from django.db import connection
import random
import json
from django.shortcuts import get_object_or_404
from .models import Media
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q


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


# Update the SearchSuggestionsView class to better handle database-based suggestions

class SearchSuggestionsView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        # Debug print
        print(f"Received search suggestion request for query: {query}")

        if not query or len(query) < 2:
            return JsonResponse({"suggestions": []})

        # Get suggestions from database and API
        suggestions = []

        try:
            # First, try to get suggestions from the database
            db_suggestions = []

            # Search for media titles in the database that match the query
            db_media = Media.objects.filter(title__icontains=query)[:8]

            for media in db_media:
                suggestion = {
                    "title": media.title,
                    "media_type": media.media_type,
                    "external_id": media.external_id,
                }

                # Add media-specific details
                if media.media_type == "book":
                    suggestion["subtitle"] = media.author if media.author else "Book"
                elif media.media_type == "movie":
                    suggestion["subtitle"] = f"Movie — {media.release_year}" if media.release_year else "Movie"
                elif media.media_type == "game":
                    suggestion["subtitle"] = f"Game — {media.studio}" if media.studio else "Game"

                db_suggestions.append(suggestion)

            # Add database suggestions to the list
            suggestions.extend(db_suggestions)

            # If we don't have enough suggestions from the database, add some from the API
            if len(suggestions) < 8:
                # Try to get real suggestions from API
                try:
                    # Get book suggestions
                    book_results = MediaAPIClient.search_media(query, "book")[
                        :2]
                    for book in book_results:
                        suggestions.append({
                            "title": book["title"],
                            "media_type": "book",
                            "external_id": book["external_id"],
                            "subtitle": book.get("author", "Book")
                        })

                    # Get movie suggestions
                    movie_results = MediaAPIClient.search_media(query, "movie")[
                        :2]
                    for movie in movie_results:
                        suggestions.append({
                            "title": movie["title"],
                            "media_type": "movie",
                            "external_id": movie["external_id"],
                            "subtitle": f"Movie — {movie.get('release_year', '')}"
                        })

                    # Get game suggestions
                    game_results = MediaAPIClient.search_media(query, "game")[
                        :1]
                    for game in game_results:
                        suggestions.append({
                            "title": game["title"],
                            "media_type": "game",
                            "external_id": game["external_id"],
                            "subtitle": f"Game — {game.get('studio', '')}"
                        })
                except Exception as e:
                    print(f"Error fetching API suggestions: {e}")

            # Add direct search suggestion at the top
            suggestions.insert(0, {
                "title": query,
                "media_type": "search",
                "subtitle": "Search for exact term"
            })

            # Add category search suggestions if we still need more
            if len(suggestions) < 8:
                if not any(s["title"].lower() == f"{query} book".lower() for s in suggestions):
                    suggestions.append({
                        "title": f"{query} book",
                        "media_type": "book",
                        "subtitle": "Search for books"
                    })

                if not any(s["title"].lower() == f"{query} movie".lower() for s in suggestions):
                    suggestions.append({
                        "title": f"{query} movie",
                        "media_type": "movie",
                        "subtitle": "Search for movies"
                    })

                if not any(s["title"].lower() == f"{query} game".lower() for s in suggestions):
                    suggestions.append({
                        "title": f"{query} game",
                        "media_type": "game",
                        "subtitle": "Search for games"
                    })

            # Limit to 8 suggestions
            suggestions = suggestions[:8]

            print(f"Returning {len(suggestions)} suggestions")  # Debug print
        except Exception as e:
            print(f"Error in suggestions view: {e}")
            # Return a basic suggestion if everything fails
            suggestions = [{
                "title": query,
                "media_type": "search",
                "subtitle": "Search for exact term"
            }]

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
                "title": details.get("title", "Untitled"),
                "description": details.get("description", ""),
                "cover_image": details.get("cover_image", ""),
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

        # Add error handling for missing keys in the details dictionary
        try:
            media, created = Media.objects.get_or_create(
                external_id=external_id,
                media_type=media_type,
                defaults={
                    "title": details.get("title", "Untitled"),
                    "description": details.get("description", ""),
                    "cover_image": details.get("cover_image", ""),
                    "release_year": details.get("release_year"),
                    "genre": details.get("genre", ""),
                    "author": details.get("author", ""),
                }
            )

            form = CommentForms(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.media = media
                comment.comment_author = request.user.profile
                comment.save()
                return redirect('media_detail', media_type=media_type, external_id=comment.media.external_id)
            else:
                return render(request, "media/media_detail.html", {
                    "media": media,
                    "form": form,
                    "media_type": media_type,
                    "external_id": external_id
                })

        except Exception as e:
            # Log the error and return a user-friendly error message
            print(f"Error creating media: {e}")
            print(f"Details received: {details}")
            return JsonResponse({"error": "An error occurred while processing the media details"}, status=500)


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
    media = get_object_or_404(
        Media, media_type=media_type, external_id=external_id)

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


def media_search(request):
    query = request.GET.get('q', '')
    search_results = []

    if query:
        # Use MediaAPIClient to search for all media types
        results = MediaAPIClient.search_media(query)
        search_results = results

    return render(request, 'media/search.html', {
        'query': query,
        'search_results': search_results
    })


def search_suggestions(request):
    query = request.GET.get('q', '')

    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})

    try:
        # Get suggestions from APIs
        suggestions = []

        # Add book suggestions
        book_results = MediaAPIClient.search_media(query, "book")[:3]
        for book in book_results:
            suggestions.append({
                'title': book.get('title', 'Unknown Title'),
                'subtitle': book.get('author', 'Book'),
                'image': book.get('cover_image', '/static/images/placeholder.jpg'),
                'media_type': 'book',
                'external_id': book.get('external_id'),
                'year': book.get('release_year')
            })

        # Add movie suggestions
        movie_results = MediaAPIClient.search_media(query, "movie")[:3]
        for movie in movie_results:
            suggestions.append({
                'title': movie.get('title', 'Unknown Title'),
                'subtitle': f"Movie — {movie.get('release_year', '')}",
                'image': movie.get('cover_image', '/static/images/placeholder.jpg'),
                'media_type': 'movie',
                'external_id': movie.get('external_id'),
                'year': movie.get('release_year')
            })

        # Add game suggestions
        game_results = MediaAPIClient.search_media(query, "game")[:2]
        for game in game_results:
            suggestions.append({
                'title': game.get('title', 'Unknown Title'),
                'subtitle': f"Game — {game.get('release_year', '')}",
                'image': game.get('cover_image', '/static/images/placeholder.jpg'),
                'media_type': 'game',
                'external_id': game.get('external_id'),
                'year': game.get('release_year')
            })

        # Add direct search suggestion
        suggestions.insert(0, {
            'title': query,
            'subtitle': 'Search for exact term',
            'media_type': 'search',
            'recent': False
        })

        # Add search category suggestions
        if len(suggestions) < 8:
            category_suggestions = [
                {
                    'title': f"{query} book",
                    'subtitle': 'Search for books',
                    'media_type': 'book',
                    'recent': False
                },
                {
                    'title': f"{query} movie",
                    'subtitle': 'Search for movies',
                    'media_type': 'movie',
                    'recent': False
                },
                {
                    'title': f"{query} game",
                    'subtitle': 'Search for games',
                    'media_type': 'game',
                    'recent': False
                }
            ]

            # Add some category suggestions to fill out the list
            for suggestion in category_suggestions:
                if len(suggestions) < 8:
                    suggestions.append(suggestion)

        return JsonResponse({'suggestions': suggestions})
    except Exception as e:
        return JsonResponse({'error': str(e), 'suggestions': []})


def book_detail(request, book_id):
    book_details = MediaAPIClient.get_media_details("book", book_id)
    if not book_details:
        return render(request, 'media/search_not_found.html')
    return render(request, 'media/books.html', {'book': book_details})


def movie_detail(request, movie_id):
    movie_details = MediaAPIClient.get_media_details("movie", movie_id)
    if not movie_details:
        return render(request, 'media/search_not_found.html')
    return render(request, 'media/movies.html', {'movie': movie_details})


def game_detail(request, game_id):
    game_details = MediaAPIClient.get_media_details("game", game_id)
    if not game_details:
        return render(request, 'media/search_not_found.html')
    return render(request, 'media/games.html', {'game': game_details})


@login_required
def comments(request):
    comments = Comment.objects.all().order_by('-created_at')
    return render(request, 'comments.html', {'comments': comments})


@login_required
@require_POST
def add_comment(request):
    form = CommentForms(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.comment_author = request.user
        comment.save()
        return redirect('comments')
    return redirect('comments')
