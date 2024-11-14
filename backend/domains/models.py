from typing import Any, Iterable
from django.core.cache import cache
from django.db import models
from django.core.validators import validate_ipv4_address, validate_ipv6_address
from .validators import validate_subdomain


class Domain(models.Model):
    domain = models.CharField(max_length=32, null=False, unique=True)

    def __str__(self):
        return self.domain

    def save(self, **kwargs):
        cache.delete(f"domains")
        super().save(**kwargs)


class Subdomain(models.Model):
    subdomain = models.CharField(
        max_length=16,
        null=False,
        blank=False,
        unique=True,
        validators=[validate_subdomain],
    )
    domain = models.ForeignKey(
        "domains.Domain", on_delete=models.CASCADE, null=False, blank=False
    )
    owner = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE, null=False
    )
    A_record = models.CharField(
        max_length=16, null=True, blank=True, validators=[validate_ipv4_address]
    )
    AAAA_record = models.CharField(
        max_length=40, null=True, blank=True, validators=[validate_ipv6_address]
    )
    TXT_record = models.CharField(max_length=128, null=True, blank=True)

    @property
    def full_domain(self):
        return f"{self.subdomain}.{self.domain}"
