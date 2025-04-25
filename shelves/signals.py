from django.db.models.signals import post_save
from django.dispatch import receiver
from user_management.models import Profile
from .models import Shelf

@receiver(post_save, sender=Profile)
def create_default_shelf(sender, instance, created, **kwargs):
    if not Shelf.objects.filter(user=instance.user).exists():
        display_name = instance.display_name if instance.display_name else instance.user.username
        shelf = Shelf.objects.create(user=instance.user, name=f"{display_name}'s Shelf")