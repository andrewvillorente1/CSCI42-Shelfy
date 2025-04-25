from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import DetailView, CreateView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from .models import Shelf, ShelfItem
from user_library.models import UserLibraryItem


class UserShelvesView(LoginRequiredMixin, CreateView):
    model = Shelf
    fields = ['name', 'description']
    template_name = 'shelves/user_shelves.html'
    success_url = reverse_lazy('shelves:user_shelves')
    context_object_name = 'form'

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Shelf created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shelves'] = Shelf.objects.filter(user=self.request.user)
        context['library_items'] = UserLibraryItem.objects.filter(
            user=self.request.user)
        return context


class PublicShelfView(DetailView):
    model = Shelf
    template_name = 'shelves/public_shelf.html'
    context_object_name = 'shelf'

    def get_object(self):
        username = self.kwargs['username']
        user = get_object_or_404(User, username=username)
        return get_object_or_404(Shelf, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shelf = self.get_object()
        context["items"] = ShelfItem.objects.filter(
            shelf=shelf).select_related('item__media')
        return context


class AddToShelfView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        shelf_id = request.POST.get("shelf_id")
        item_id = request.POST.get("item_id")

        if not shelf_id or not item_id:
            messages.error(request, "Missing required parameters.")
            return redirect("shelves:user_shelves")

        shelf = get_object_or_404(Shelf, id=shelf_id, user=request.user)
        user_library_item = get_object_or_404(
            UserLibraryItem, id=item_id, user=request.user)

        # Get item title safely
        item_title = "Item"
        if hasattr(user_library_item, 'media') and user_library_item.media:
            if hasattr(user_library_item.media, 'title'):
                item_title = user_library_item.media.title
            elif hasattr(user_library_item, 'title'):
                item_title = user_library_item.title

        if ShelfItem.objects.filter(shelf=shelf, item=user_library_item).exists():
            messages.info(
                request, f"{item_title} is already on '{shelf.name}'.")
        else:
            ShelfItem.objects.create(shelf=shelf, item=user_library_item)
            messages.success(request, f"Added {item_title} to '{shelf.name}'.")

        return redirect("shelves:user_shelves")


class RemoveFromShelfView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        shelf_id = request.POST.get("shelf_id")
        item_id = request.POST.get("item_id")

        if not shelf_id or not item_id:
            messages.error(request, "Missing required parameters.")
            return redirect("shelves:user_shelves")

        shelf = get_object_or_404(Shelf, id=shelf_id, user=request.user)
        shelf_item = ShelfItem.objects.filter(
            shelf=shelf, item__id=item_id).first()

        if shelf_item:
            # Get item title safely
            item_title = "Item"
            if hasattr(shelf_item.item, 'media') and shelf_item.item.media:
                if hasattr(shelf_item.item.media, 'title'):
                    item_title = shelf_item.item.media.title
                elif hasattr(shelf_item.item, 'title'):
                    item_title = shelf_item.item.title

            shelf_item.delete()
            messages.success(
                request, f"Removed {item_title} from '{shelf.name}'.")
        else:
            messages.warning(request, f"Item not found on '{shelf.name}'.")

        return redirect("shelves:user_shelves")


class ShelfItemDetailView(DetailView):
    model = ShelfItem
    template_name = 'shelves/shelf_item_detail.html'
    context_object_name = 'shelf_item'

    def get_object(self):
        username = self.kwargs['username']
        item_id = self.kwargs['item_id']

        user = get_object_or_404(User, username=username)
        # Find the shelf that contains this item for this user
        shelf_item = get_object_or_404(ShelfItem,
                                       item__id=item_id,
                                       shelf__user=user)
        return shelf_item

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["library_item"] = self.object.item
        if hasattr(self.object.item, 'media'):
            context["media"] = self.object.item.media
        return context
