from django.test import SimpleTestCase
from django.urls import reverse, resolve
from ..views import (
    LibraryIndexView, AddToLibraryView, EditLibraryItemView,
    UpdateLibraryStatusView, DeleteLibraryItemView
)
from ..models import hashids # Import hashids for encoding test ID

class LibraryUrlResolveTests(SimpleTestCase):

    def test_index_url_resolves(self):
        """Test library index URL resolves."""
        url = reverse('user_library:index')
        self.assertEqual(resolve(url).func.view_class, LibraryIndexView)

    def test_add_url_resolves(self):
        """Test add to library URL resolves."""
        url = reverse('user_library:add')
        self.assertEqual(resolve(url).func.view_class, AddToLibraryView)

    def test_edit_url_resolves(self):
        """Test edit library item URL resolves."""
        # We need a plausible hashid, even if the item doesn't exist for URL resolution
        test_id = 1
        test_hashid = hashids.encode(test_id)
        url = reverse('user_library:edit', kwargs={'hashid': test_hashid})
        self.assertEqual(resolve(url).func.view_class, EditLibraryItemView)

    def test_update_url_resolves(self):
        """Test update library item status URL resolves."""
        test_id = 1
        url = reverse('user_library:update', kwargs={'item_id': test_id})
        self.assertEqual(resolve(url).func.view_class, UpdateLibraryStatusView)

    def test_delete_url_resolves(self):
        """Test delete library item URL resolves."""
        test_id = 1
        url = reverse('user_library:delete', kwargs={'item_id': test_id})
        self.assertEqual(resolve(url).func.view_class, DeleteLibraryItemView)