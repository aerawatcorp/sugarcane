from rest_framework.routers import SimpleRouter

from sachet.apis import CatalogViewset

router = SimpleRouter()
router.register("catalogs", CatalogViewset, basename="catalogs")

urlpatterns = router.urls
