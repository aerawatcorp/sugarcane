from django.contrib import admin

from sachet.models import Catalog, Store


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "provider_url", "ttl", "updated_on"]
    list_filter = ["is_obsolete"]
    search_fields = ["name", "provider"]


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["catalog", "url", "version", "is_active", "expires_on", "updated_on"]
    list_filter = ["is_obsolete", "is_active"]
    search_fields = ["catalog__name", "catalog__provider"]
