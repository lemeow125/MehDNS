from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Domain, Subdomain


@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    model = Domain
    search_fields = ("id", "domain")
    list_display = ["id", "domain"]


@admin.register(Subdomain)
class SubdomainAdmin(ModelAdmin):
    model = Subdomain
    search_fields = ("id", "subdomain", "owner", "A_record")
    list_display = ["id", "subdomain", "owner", "A_record"]
