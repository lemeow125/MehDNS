from django.urls import include, path
from .views import DomainViewSet, SubdomainViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"domains", DomainViewSet, basename="Domains")
router.register(r"subdomains", SubdomainViewSet, basename="Subdomains")
urlpatterns = [
    path("/", include(router.urls)),
]
