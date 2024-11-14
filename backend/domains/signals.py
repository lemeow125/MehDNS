from django.db.models.signals import pre_delete, post_delete, pre_save, post_save
from django.core.cache import cache
from django.dispatch import receiver
from .tasks import create_zone, delete_zone, update_a_record, update_aaaa_record, update_txt_record, update_ns_zone_comments
from .models import Domain, Subdomain


@receiver(post_delete, sender=Domain)
def domain_post_delete(sender, instance, **kwargs):
    cache.delete(f"domains")


@receiver(post_save, sender=Domain)
def domain_post_save(sender, instance, **kwargs):
    cache.delete(f"domains")


@receiver(pre_delete, sender=Subdomain)
def subdomain_pre_delete(sender, instance, **kwargs):
    delete_zone(instance.full_domain)
    cache.delete(f"subdomains")
    cache.delete(f"subdomains:{instance.owner.id}")


@receiver(pre_save, sender=Subdomain)
def subdomain_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        create_zone(instance.full_domain, instance.owner.email)
    if instance.A_record:
        update_a_record(instance.full_domain, instance.A_record)
    if instance.AAAA_record:
        update_aaaa_record(instance.full_domain, instance.AAAA_record)
    if instance.TXT_record:
        update_txt_record(instance.full_domain, instance.TXT_record)
    update_ns_zone_comments(instance.full_domain, instance.owner.email)


@receiver(post_save, sender=Subdomain)
def subdomain_post_save(sender, instance, created, **kwargs):
    # Delete cache after save
    cache.delete(f"subdomains")
    cache.delete(f"subdomains:{instance.owner.id}")
