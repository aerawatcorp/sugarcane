import logging
import traceback

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

from sachet.models import Catalog, Store
from sachet.tasks import initiate_node_rebuild

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
            logging.error(f"[MASTER API] Retrieve error {exp} {traceback.format_exc()}")
            return Response(
                {"detail": "Could not fetch data"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=["GET"], detail=True, url_path="node-data")
    def node_data(self, request, *args, **kwargs):
        """Get node data and initiate write in cache"""
        try:
            sub_catalog = request.GET.urlencode()
            instance: Catalog = self.get_object()
            store: Store = instance.get_lastest_store(sub_catalog=sub_catalog)
            data, _ = store.get_node_schema()
            initiate_node_rebuild(instance.id, sub_catalog)
            return Response(data)
        except Store.DoesNotExist as exp:
            logging.error(f"[NODE API] Store not found {exp} {traceback.format_exc()}")
            return Response(
                {"detail": "Could not fetch data"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as exp:
            logging.error(f"[NODE API] Retrieve error {exp} {traceback.format_exc()}")
            return Response(
                {"detail": "Could not fetch data"}, status=status.HTTP_400_BAD_REQUEST
            )
