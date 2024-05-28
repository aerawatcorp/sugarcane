from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.contrib import messages

from sachet.models import Catalog, Store


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "provider_url", "ttl", "updated_on", "action"]
    list_filter = ["is_obsolete"]
    search_fields = ["name", "provider"]

    change_list_template = "admin/sachet/catalog_change_list.html"

    def action(self, obj):
        return format_html('<a class="btn btn-info" href="{}" >Rebuild Node</a>',
            reverse('admin:rebuild_node_schema', args=[obj.pk]))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_buttons'] = [
            {'name': 'Rebuild Master', 'url': 'rebuild_master_schema/'},
        ]
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('rebuild_master_schema/', self.admin_site.admin_view(self.rebuild_master_schema)),
            path('rebuild_node_schema/<int:pk>/', self.admin_site.admin_view(self.rebuild_node_schema), name='rebuild_node_schema'),
        ]
        return custom_urls + urls
    
    def rebuild_master_schema(self, request):
        Catalog.write_master_schema_to_cache()
        messages.success(request, "Master schema rebuild completed")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    def rebuild_node_schema(self, request, pk):
        catalog = Catalog.objects.get(pk=pk)
        store: Store = catalog.get_lastest_store()
        if store:
            store.invalidate_cache()
            messages.success(request, "Store schema rebuild completed")
        else:
            messages.error(request, "Store schema rebuild completed",)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["catalog", "url", "version", "is_active", "expires_on", "updated_on"]
    list_filter = ["is_obsolete", "is_active"]
    search_fields = ["catalog__name", "catalog__provider"]
