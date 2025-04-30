from django.db import models
from django.contrib.auth.models import User
from user_library.models import UserLibraryItem


class Shelf(models.Model):
    """
    A shelf is a collection of library items that a user wants to display publicly.
    Each user has one default shelf, but could have multiple shelves in the future.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='shelf')
    name = models.CharField(max_length=100, default="My Public Shelf")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s {self.name}"


class ShelfItem(models.Model):
    """
    A shelf item is a connection between a shelf and a library item.
    This allows users to add items from their library to their public shelf.
    """
    shelf = models.ForeignKey(
        Shelf, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(UserLibraryItem, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('shelf', 'item')
        ordering = ['-id']  # Order by ID instead of timestamp

    def __str__(self):
        return f"{self.item.media.title} on {self.shelf.name}"
