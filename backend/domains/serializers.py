from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework.serializers import ModelSerializer, SlugRelatedField
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from .models import Domain, Subdomain
from accounts.models import CustomUser
from django.core.cache import cache


class DomainSerializer(ModelSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = Domain
        read_only_fields = ["id"]
        fields = ["id", "domain"]

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise PermissionDenied

        cache.delete(f"subdomains")

        return super().create(validated_data)

    def destroy(self, request, *args, **kwargs):
        user = self.context["request"].user
        if not user.is_superuser:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()
        self.perform_destroy(instance)

        cache.delete(f"subdomains")

        return Response(status=status.HTTP_204_NO_CONTENT)


class SubdomainSerializer(ModelSerializer):
    owner = SlugRelatedField(
        many=False,
        slug_field="id",
        queryset=CustomUser.objects.all(),
        required=False,
        write_only=True,
    )
    domain = SlugRelatedField(
        many=False, slug_field="domain", queryset=Domain.objects.all(), required=True
    )

    class Meta(BaseUserSerializer.Meta):
        model = Subdomain
        read_only_fields = ["id", "owner", "full_domain"]
        fields = [
            "id",
            "owner",
            "domain",
            "subdomain",
            "full_domain",
            "A_record",
            "AAAA_record",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        if "owner" not in validated_data:
            validated_data["owner"] = user
        else:
            if validated_data["owner"] != user:
                raise PermissionDenied(
                    "You do not have permission to create subdomains for other users"
                )

        cache.delete(f"subdomains")
        cache.delete(f"subdomains_user:{user.id}")

        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if instance.owner != user:
            raise PermissionDenied
        validated_data.pop("domain", None)
        validated_data.pop("subdomain", None)
        cache.delete(f"subdomains")
        cache.delete(f"subdomains_user:{user.id}")
        return super().update(instance, validated_data)

    def destroy(self, request, *args, **kwargs):
        user = self.context["request"].user
        if instance.owner != user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        instance = self.get_object()
        self.perform_destroy(instance)

        cache.delete(f"subdomains")
        cache.delete(f"subdomains_user:{user.id}")
        return Response(status=status.HTTP_204_NO_CONTENT)
