from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.middleware.csrf import get_token
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.urls import reverse
from .models import UserLibraryItem
from .forms import LibraryItemEditForm
from shelfy.models import Media
from shelfy.api_utils import MediaAPIClient
from hashids import Hashids


class LibraryIndexView(LoginRequiredMixin, ListView):
    model = UserLibraryItem
    template_name = "user_library/index.html"
    context_object_name = "library"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["star_range"] = range(5)

        # Make sure all library items have valid media_type and external_id
        for item in context["library"]:
            if not item.media.media_type or not item.media.external_id:
                # Log the issue for debugging
                print(
                    f"Warning: Invalid media data for item {item.id}: media_type='{item.media.media_type}', external_id='{item.media.external_id}'")

        return context

    def get_queryset(self):
        return UserLibraryItem.objects.filter(user=self.request.user)


class AddToLibraryView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        media_type = request.POST.get("media_type")
        external_id = request.POST.get("external_id")

        # Validate required parameters
        if not media_type or not external_id:
            return JsonResponse({
                "success": False,
                "message": "Media type and external ID are required."
            }, status=400)

        media, created = Media.objects.get_or_create(
            external_id=external_id,
            media_type=media_type,
            defaults=self.fetch_and_format_media(media_type, external_id),
        )

        if UserLibraryItem.objects.filter(user=request.user, media=media).exists():
            return JsonResponse({"success": False, "message": "Slow down, collector! This one's already in your library."}, status=400)

        UserLibraryItem.objects.create(
            user=request.user, media=media, status="planned")
        return JsonResponse({"success": True, "message": "Nice pick! It's now in your library."})

    def fetch_and_format_media(self, media_type, external_id):
        media_data = MediaAPIClient.get_media_details(media_type, external_id)

        if "error" in media_data:
            messages.error(
                self.request, "Uh-oh! Our media scouts couldn't retrieve the details. Try again later?")
            return {}

        formatted_data = {
            "title": media_data.get("title"),
            "description": media_data.get("description"),
            "cover_image": media_data.get("cover_image"),
            "release_year": media_data.get("release_year"),
            "genre": media_data.get("genre"),
        }

        if media_type == "book":
            formatted_data["author"] = media_data.get("author")
        elif media_type == "movie":
            formatted_data["director"] = media_data.get("director")
        elif media_type == "game":
            formatted_data["studio"] = media_data.get("studio")

        return formatted_data


hashids = Hashids(salt="your_secret_salt", min_length=6)


class EditLibraryItemView(LoginRequiredMixin, UpdateView):
    model = UserLibraryItem
    form_class = LibraryItemEditForm
    template_name = "user_library/edit.html"

    def get_object(self, queryset=None):
        hashid = self.kwargs.get("hashid")
        id_tuple = hashids.decode(hashid)
        if id_tuple:
            return get_object_or_404(UserLibraryItem, id=id_tuple[0])
        else:
            raise Http404(
                "Hmm… this library entry seems to be lost in the void. Are you sure it exists?")

    def get_success_url(self):
        return reverse("user_library:index")


class UpdateLibraryStatusView(LoginRequiredMixin, View):
    @method_decorator(require_POST)
    def post(self, request, item_id):
        item = get_object_or_404(
            UserLibraryItem, id=item_id, user=request.user)
        new_status = request.POST.get("status")

        if new_status in dict(UserLibraryItem.STATUS_CHOICES):
            item.status = new_status
            item.save()

            # return updated status + CSRF token for security
            return JsonResponse({
                "success": True,
                "new_status": item.get_status_display(),
                "csrf_token": get_token(request)
            })
        return JsonResponse({"success": False, "error": "Hmm… that status doesn't exist in this universe. Try again with a valid one!"}, status=400)


class DeleteLibraryItemView(LoginRequiredMixin, View):
    def post(self, request, item_id, *args, **kwargs):
        entry = get_object_or_404(
            UserLibraryItem, id=item_id, user=request.user)
        entry.delete()
        messages.success(request, "Poof! Gone from your library.")
        return redirect("user_library:index")
