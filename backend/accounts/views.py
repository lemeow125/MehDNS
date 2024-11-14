from accounts import serializers
from accounts.models import CustomUser
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from djoser.conf import settings
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response


class CustomUserViewSet(DjoserUserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = serializers.CustomUserSerializer
    permission_classes = settings.PERMISSIONS.activation
    token_generator = default_token_generator

    def get_queryset(self):
        user = self.request.user
        # If user is admin, show all active users
        if user.is_superuser:
            key = "users"
            # Get cache
            queryset = cache.get(key)
            # Set cache if stale or does not exist
            if not queryset:
                queryset = CustomUser.objects.filter(is_active=True)
                cache.set(key, queryset, 60 * 60)
            return queryset
        else:
            key = f"user:{user.id}"
            queryset = cache.get(key)
            if not queryset:
                queryset = CustomUser.objects.filter(is_active=True)
                cache.set(key, queryset, 60 * 60)
            return queryset

    @action(
        methods=["post"], detail=False, url_path="activation", url_name="activation"
    )
    def activation(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.is_active = True
        user.save()

        # Construct a response with user's first name, last name, and email
        user_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
        }

        # Clear cache
        cache.delete("users")
        cache.delete(f"user:{user.id}")

        return Response(user_data, status=status.HTTP_200_OK)
