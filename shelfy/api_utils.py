import requests
from django.conf import settings


class MediaAPIClient:
    """Utility class for interacting with external media APIs."""

    ENDPOINTS = {
        "book": {
            "search": "https://www.googleapis.com/books/v1/volumes",
            "detail": "https://www.googleapis.com/books/v1/volumes/{id}",
            "params": lambda q: {"q": q, "key": settings.GOOGLE_BOOKS_API_KEY},
        },
        "movie": {
            "search": "https://api.themoviedb.org/3/search/movie",
            "detail": "https://api.themoviedb.org/3/movie/{id}",
            "params": lambda q: {"query": q, "api_key": settings.TMDB_API_KEY},
        },
        "game": {
            "search": "https://api.rawg.io/api/games",
            "detail": "https://api.rawg.io/api/games/{id}",
            "params": lambda q: {"search": q, "key": settings.RAWG_API_KEY},
        },
    }

    @classmethod
    def search_media(cls, query, media_type=None):
        """Searches for books, movies, or games."""
        results = []
        for type_, data in cls.ENDPOINTS.items():
            if media_type and media_type != type_:
                continue  # Skip unrelated media types

            response = requests.get(
                data["search"], params=data["params"](query))
            if response.status_code == 200:
                results.extend(cls.format_results(type_, response.json()))
        return results

    @classmethod
    def get_media_details(cls, media_type, external_id):
        """Fetches details of a specific media item."""
        if media_type not in cls.ENDPOINTS:
            return {"error": "Invalid media type"}

        response = requests.get(
            cls.ENDPOINTS[media_type]["detail"].format(id=external_id),
            params=cls.ENDPOINTS[media_type]["params"](None),
        )
        if response.status_code == 200:
            return cls.format_details(media_type, response.json())
        return {"error": f"{media_type.capitalize()} not found"}

    @staticmethod
    def format_results(media_type, data):
        """Formats search results based on media type."""
        if media_type == "book":
            return [
                {
                    "title": item["volumeInfo"].get("title"),
                    "description": item["volumeInfo"].get("description"),
                    "cover_image": item["volumeInfo"].get("imageLinks", {}).get("thumbnail"),
                    "release_year": item["volumeInfo"].get("publishedDate", "").split("-")[0],
                    "genre": ", ".join(item["volumeInfo"].get("categories", [])),
                    "author": ", ".join(item["volumeInfo"].get("authors", [])),
                    "external_id": item["id"],
                    "media_type": "book",
                }
                for item in data.get("items", [])
            ]
        if media_type == "movie":
            return [
                {
                    "title": movie.get("title"),
                    "description": movie.get("overview"),
                    "cover_image": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}",
                    "release_year": movie.get("release_date", "").split("-")[0],
                    "external_id": str(movie.get("id")),
                    "media_type": "movie",
                }
                for movie in data.get("results", [])
            ]
        if media_type == "game":
            return [
                {
                    "title": game.get("name"),
                    "cover_image": game.get("background_image"),
                    "release_year": game.get("released", "").split("-")[0] if game.get("released") else None,
                    "external_id": str(game.get("id")),
                    "media_type": "game",
                }
                for game in data.get("results", [])
            ]
        return []

    @staticmethod
    def format_details(media_type, data):
        """Formats detailed view based on media type."""
        if media_type == "book":
            volume = data.get("volumeInfo", {})
            return {
                "title": volume.get("title"),
                "description": volume.get("description"),
                "cover_image": volume.get("imageLinks", {}).get("thumbnail"),
                "release_year": volume.get("publishedDate", "").split("-")[0],
                "genre": ", ".join(volume.get("categories", [])),
                "author": ", ".join(volume.get("authors", [])),
            }
        if media_type == "movie":
            return {
                "title": data.get("title"),
                "description": data.get("overview"),
                "cover_image": f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}",
                "release_year": data.get("release_date", "").split("-")[0],
                "genre": ", ".join([genre["name"] for genre in data.get("genres", [])]),
                "director": next(
                    (crew["name"] for crew in data.get("credits", {}).get(
                        "crew", []) if crew["job"] == "Director"),
                    None
                ),
            }
        if media_type == "game":
            return {
                "title": data.get("name"),
                "description": data.get("description_raw"),
                "cover_image": data.get("background_image"),
                "release_year": data.get("released", "").split("-")[0] if data.get("released") else None,
                "genre": ", ".join([genre["name"] for genre in data.get("genres", [])]),
                "studio": ", ".join([dev["name"] for dev in data.get("developers", [])]) if data.get("developers") else None,
            }
        return {}
