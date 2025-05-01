# shelfy/tests/test_views.py
# FIXED VERSION

from django.test import SimpleTestCase # Using SimpleTestCase as DB likely not needed
from unittest.mock import patch, MagicMock
import requests # Import requests as it's used by the client

# --- FIX: Import the client correctly ---
try:
    from shelfy.api_utils import MediaAPIClient
except ImportError:
    print("ERROR: Cannot import MediaAPIClient from shelfy.api_utils!")
    class MediaAPIClient: # Dummy class if import fails
         SEARCH_URLS = {}
         DETAIL_URLS = {}
         def search_media(self, *args, **kwargs): return []
         def get_media_details(self, *args, **kwargs): return {}
         def format_results(self, *args, **kwargs): return []
         def format_details(self, *args, **kwargs): return {}


# Mock data for successful responses (simplified)
MOCK_BOOK_SEARCH_RESPONSE_JSON = {
    "items": [{
        "id": "book123",
        "volumeInfo": {
            "title": "Test Book Title", "authors": ["Author One"], "publishedDate": "2023-01-01",
            "description": "Desc...", "imageLinks": {"thumbnail": "img.jpg"}, "categories": ["Fiction"]
        }
    }]
}
MOCK_MOVIE_DETAIL_RESPONSE_JSON = {
    "id": "movie456", "title": "Test Movie Title", "overview": "Overview...",
    "poster_path": "/poster.jpg", "release_date": "2022-05-10", "genres": [{"name": "Sci-Fi"}],
    "credits": {"crew": [{"name": "Director Name", "job": "Director"}]}
}
# Mock data for 404 or error responses
MOCK_API_404_RESPONSE = MagicMock(spec=requests.Response)
MOCK_API_404_RESPONSE.status_code = 404
MOCK_API_404_RESPONSE.json.return_value = {"error": "Not Found"}

MOCK_API_ERROR_RESPONSE = MagicMock(spec=requests.Response)
MOCK_API_ERROR_RESPONSE.status_code = 500
MOCK_API_ERROR_RESPONSE.json.return_value = {"error": "Server Error"}


# --- FIX: Rewrite test case to test the client methods directly ---
class MediaAPIClientUnitTestCase(SimpleTestCase): # Renamed & using SimpleTestCase
    """Tests the MediaAPIClient utility class methods directly."""

    def setUp(self):
        """Instantiate the client."""
        # --- FIX: Instantiate client directly ---
        self.client = MediaAPIClient()
        # Mock settings dependencies if MediaAPIClient relies on them directly at instantiation
        # Otherwise, mocking requests.get is usually sufficient

    # --- FIX: Use patch to mock the underlying HTTP library call ---
    # Target 'requests.get' within the module where it's USED (api_utils)
    @patch('shelfy.api_utils.requests.get')
    def test_search_media_book_success(self, mock_requests_get):
        """Test searching for books successfully."""
        # Configure mock response for the book search URL
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_BOOK_SEARCH_RESPONSE_JSON
        mock_requests_get.return_value = mock_response # All calls to get will return this

        query = "test query"
        results = self.client.search_media(query, media_type='book')

        # Assert requests.get was called correctly
        expected_url = self.client.ENDPOINTS['book']['search']
        expected_params = self.client.ENDPOINTS['book']['params'](query)
        mock_requests_get.assert_called_once_with(expected_url, params=expected_params)

        # Assert the results are formatted correctly
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Test Book Title")
        self.assertEqual(results[0]['external_id'], "book123")
        self.assertEqual(results[0]['media_type'], "book")
        self.assertEqual(results[0]['author'], "Author One")

    @patch('shelfy.api_utils.requests.get')
    def test_get_media_details_movie_success(self, mock_requests_get):
        """Test getting movie details successfully."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_MOVIE_DETAIL_RESPONSE_JSON
        mock_requests_get.return_value = mock_response

        media_type = 'movie'
        external_id = 'movie456'
        details = self.client.get_media_details(media_type, external_id)

        # Assert requests.get was called correctly
        expected_url = self.client.ENDPOINTS[media_type]['detail'].format(id=external_id)
        # The params lambda might need None passed if query isn't relevant for detail
        expected_params = self.client.ENDPOINTS[media_type]['params'](None)
        mock_requests_get.assert_called_once_with(expected_url, params=expected_params)


        # Assert the formatted details are correct
        self.assertEqual(details['title'], "Test Movie Title")
        self.assertIn("Overview...", details['description'])
        self.assertEqual(details['director'], "Director Name")
        self.assertNotIn('error', details)


    @patch('shelfy.api_utils.requests.get')
    def test_get_media_details_not_found(self, mock_requests_get):
        """Test getting details when the API returns 404."""
        mock_requests_get.return_value = MOCK_API_404_RESPONSE

        details = self.client.get_media_details('game', 'not_found_id')

        # Assert the client method handled the 404 by returning an error dict
        self.assertIn('error', details)
        self.assertIn('not found', details['error'])

    @patch('shelfy.api_utils.requests.get')
    def test_get_media_details_invalid_type(self, mock_requests_get):
        """Test getting details with an unsupported media type."""
        # This call shouldn't even reach requests.get
        details = self.client.get_media_details('podcast', '123')

        self.assertIn('error', details)
        self.assertIn('Invalid media type', details['error'])
        mock_requests_get.assert_not_called() # Verify no HTTP call was made

    # Add more tests here for:
    # - Searching other media types (movie, game)
    # - Searching across all types (media_type=None)
    # - Handling API errors (500 status code) during search/detail calls
    # - Cases where format_results/format_details might receive unexpected data


# IMPORTANT: Remove the old MediaAPITestCase class entirely if this replaces it.

# Keep other test classes in this file if they exist for actual Django views
# (like MediaSearchView, MediaDetailView if you have tests for them).