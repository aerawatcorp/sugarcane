import logging
import traceback

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

from sachet.models import Catalog, Sachet

logger = logging.getLogger(__name__)


class CatalogViewset(ModelViewSet):
    queryset = Catalog.objects.filter(is_obsolete=False)
    serializer_class = None
    lookup_field = "slug"

    @action(methods=["GET"], detail=False, url_path="master-schema")
    def master_schema(self, request, *args, **kwargs):
        """Retrieve master schema and also write in cache"""
        try:
            data, _ = Catalog.get_master_schema()
            return Response(data)
        except Exception as exp:
            logger.error(f"[MASTER API] Retrieve error {exp} {traceback.format_exc()}")
            return Response(
                {"detail": "Could not fetch data"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=["GET"], detail=True, url_path="node-data")
    def node_data(self, request, *args, **kwargs):
        """Get node data and initiate write in cache"""
        sub_catalog = request.GET.urlencode()
        instance: Catalog = self.get_object()
        try:
            sachet: Sachet = instance.get_or_create_latest_store(sub_catalog=sub_catalog, headers=request.headers)
            data, _ = sachet.get_node_schema()
            return Response(data)
        except Sachet.DoesNotExist as exp:
            logger.error(f"[NODE API] Sachet not found {exp} {traceback.format_exc()}")
            return Response(
                {"detail": "Could not fetch data"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as exp:
            logger.error(f"[NODE API] Retrieve error {exp} {traceback.format_exc()}")
            return Response(
                {"detail": "Could not fetch data"}, status=status.HTTP_400_BAD_REQUEST
            )
