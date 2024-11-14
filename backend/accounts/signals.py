from config.settings import get_secret
from django.db.models.signals import post_migrate, pre_delete, post_save
from django.dispatch import receiver

from .models import CustomUser
from django.core.cache import cache


@receiver(pre_delete, sender=CustomUser)
def user_pre_delete(sender, instance, **kwargs):
    cache.delete(f"users")
    cache.delete(f"user:{instance.id}")


@receiver(post_save, sender=CustomUser)
def user_post_save(sender, instance, **kwargs):
    cache.delete(f"users")
    cache.delete(f"user:{instance.id}")


@receiver(post_migrate)
def create_admin_user(sender, **kwargs):
    # Function to fill in users table with test data on dev/staging
    if sender.name == "accounts":
        ADMIN_USER = CustomUser.objects.filter(email=get_secret("ADMIN_EMAIL")).first()
        if not ADMIN_USER:
            ADMIN_USER = CustomUser.objects.create_superuser(
                username=get_secret("ADMIN_USERNAME"),
                email=get_secret("ADMIN_EMAIL"),
                password=get_secret("ADMIN_PASSWORD"),
            )

            print("Created admin account:", ADMIN_USER.email)

            ADMIN_USER.first_name = "MehDNS"
            ADMIN_USER.last_name = "Admin"
            ADMIN_USER.is_active = True
            ADMIN_USER.save()
