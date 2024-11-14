from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification


@receiver(post_save, sender=Notification)
def clear_cache_after_notification_update(sender, instance, **kwargs):
    # Clear cache
    cache.delete("notifications")
    cache.delete(f"notifications_user:{instance.recipient.id}")
