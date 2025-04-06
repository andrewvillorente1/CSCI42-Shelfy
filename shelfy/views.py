from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
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
