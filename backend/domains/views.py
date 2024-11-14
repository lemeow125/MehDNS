from django.core.cache import cache
from rest_framework import viewsets
from .models import Domain, Subdomain
from .serializers import DomainSerializer, SubdomainSerializer
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class DomainViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "delete"]
    serializer_class = DomainSerializer

    def get_object(self):
        pk = self.kwargs.get("pk")
        cache_key = f"domain:{pk}"

        obj = cache.get(cache_key)
        if obj is None:
            logger.debug("CACHE MISS")
            obj = super().get_object()
            cache.set(cache_key, obj, 60 * 60)  # Cache for 1 hour
        else:
            logger.debug("CACHE HIT")
            return obj

    def get_queryset(self):
        key = f"domains"
        queryset = cache.get(key)
        if not queryset:
            queryset = Domain.objects.all()
            cache.set(key, queryset, 60 * 60)
        return queryset


class SubdomainViewSet(viewsets.ModelViewSet):
    serializer_class = SubdomainSerializer
    http_method_names = ["get", "patch", "post", "delete"]
    permission_classes = [IsAuthenticated]

    # TODO: Add per object caching in def get_object()

    def get_queryset(self):
        if self.request.user.is_superuser:
            key = "subdomains"
            queryset = cache.get(key)
            if not queryset:
                queryset = Subdomain.objects.all()
                cache.set(key, queryset, 60 * 60)
            return queryset
        else:
            key = f"subdomains_user:{self.request.user.id}"
            queryset = cache.get(key)
            if not queryset:
                queryset = Subdomain.objects.filter(owner=self.request.user.id)
                cache.set(key, queryset, 60 * 60)
            return queryset
