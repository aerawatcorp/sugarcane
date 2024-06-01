import logging

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.contrib import messages

from sachet.models import Catalog, Sachet
from sachet.tasks import fetch_catalog_content
from sugarlib.constants import MASTER_KEY, MASTER_KEY_VERBOSED
from sugarlib.redis_client import r1_cane as r1
from sugarlib.redis_helpers import r_delete

logger = logging.getLogger(__name__)


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "provider",
        "provider_url",
        "ttl",
        "is_live",
        "latest_version",
        "latest_expiry",
        "updated_on",
        "action",
    ]
    list_filter = ["is_obsolete", "is_live"]
    search_fields = ["name", "provider", "latest_version"]

    change_list_template = "admin/sachet/catalog_change_list.html"

    def action(self, obj):
        return format_html(
            '<a class="btn btn-info" href="{}" >Rebuild Nodes</a>',
            reverse("admin:rebuild_all_node_schema", args=[obj.pk]),
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["custom_buttons"] = [
            {"name": "Invalidate Master", "url": "invalidate_master_cache/"},
        ]
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "invalidate_master_cache/",
                self.admin_site.admin_view(self.invalidate_master_cache),
            ),
            path(
                "rebuild_all_node_schema/<int:pk>/",
                self.admin_site.admin_view(self.rebuild_all_node_schema),
                name="rebuild_all_node_schema",
            ),
        ]
        return custom_urls + urls

    def invalidate_master_cache(self, request):
        r_delete(r1, MASTER_KEY)
        r_delete(r1, MASTER_KEY_VERBOSED)
        logger.info(
            f"[MASTER] Master rebuild invalidated by {request.user} ({request.user.id})"
        )
        messages.success(request, "Master cache invalidated successfully.")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

    def rebuild_all_node_schema(self, request, pk):
        try:
            catalog = Catalog.objects.get(pk=pk)
            fetch_catalog_content(catalog.id)
            messages.success(request, "Node rebuild task has been initiated")
        except Sachet.DoesNotExist:
            messages.error(
                request,
                "Sachet schema not found",
            )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@admin.register(Sachet)
class SachetAdmin(admin.ModelAdmin):
    list_display = [
        "catalog",
        "sub_catalog",
        "url",
        "version",
        "is_active",
        "expires_on",
        "updated_on",
        "action",
    ]
    list_filter = ["is_obsolete", "is_active"]
    search_fields = ["catalog__name", "catalog__provider"]

    def action(self, obj):
        return format_html(
            '<a class="btn btn-info" href="{}" title="Force the build of node">Force Rebuild Node</a>',
            reverse("admin:rebuild_node_schema", args=[obj.pk]),
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "rebuild_node_schema/<int:pk>/",
                self.admin_site.admin_view(self.rebuild_node_schema),
                name="rebuild_node_schema",
            ),
        ]
        return custom_urls + urls

    def rebuild_node_schema(self, request, pk):
        sachet = Sachet.objects.get(pk=pk)
        # Might need to change the headers
        obj = sachet.catalog.get_or_create_latest_store(
            sachet.sub_catalog, force=True, headers=request.headers
        )
        obj_url = reverse("admin:sachet_store_change", args=[obj.pk])

        message = format_html(
            f'Node rebuild completed <a href="{obj_url}" style="color:#ffffff">{obj}</a>',
        )
        messages.success(request, message)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
