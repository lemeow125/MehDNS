from domains.models import Subdomain
from django.core.management.base import BaseCommand
from domains.tasks import (
    create_zone,
    update_a_record,
    update_aaaa_record,
    update_ns_zone_comments,
    update_txt_record,
)
import json


class Command(BaseCommand):
    help = "Pushes data from local database into an existing DNS server"

    def handle(self, *args, **options):

        for SUBDOMAIN in Subdomain.objects.all().prefetch_related("owner"):
            try:
                create_zone(SUBDOMAIN.full_domain, SUBDOMAIN.owner)
            except:
                pass

            if SUBDOMAIN.A_record:
                update_a_record(SUBDOMAIN.A_record, SUBDOMAIN.full_domain)

            if SUBDOMAIN.AAAA_record:
                update_aaaa_record(SUBDOMAIN.AAAA_record, SUBDOMAIN.full_domain)

            update_ns_zone_comments(SUBDOMAIN.full_domain, SUBDOMAIN.owner.email)
            if SUBDOMAIN.A_record:
                update_a_record(SUBDOMAIN.full_domain, SUBDOMAIN.A_record)
            if SUBDOMAIN.AAAA_record:
                update_aaaa_record(SUBDOMAIN.full_domain, SUBDOMAIN.AAAA_record)
            if SUBDOMAIN.TXT_record:
                update_txt_record(SUBDOMAIN.full_domain, SUBDOMAIN.TXT_record)
