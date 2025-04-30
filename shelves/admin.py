from django.contrib import admin
from .models import Shelf, ShelfItem


class ShelfItemInline(admin.TabularInline):
    model = ShelfItem
    extra = 1


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ('user', 'name')
    search_fields = ('user__username', 'name')
    inlines = [ShelfItemInline]


@admin.register(ShelfItem)
class ShelfItemAdmin(admin.ModelAdmin):
    list_display = ('shelf', 'item')
    list_filter = ('shelf__user',)
    search_fields = ('shelf__user__username', 'item__media__title')
