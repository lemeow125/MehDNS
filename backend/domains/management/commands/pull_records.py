from domains.models import Domain, Subdomain
from accounts.models import CustomUser
from config.settings import TECHNITIUM_API_KEY, TECHNITIUM_SERVER_ADDRESS
import requests
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
import json


class Command(BaseCommand):
    # Unused
    help = "Pulls data from the existing DNS server into the local database"

    def handle(self, *args, **options):
        # Query the DNS Server for all zones to sync to DB
        response = requests.get(
            TECHNITIUM_SERVER_ADDRESS + "/api/zones/list?token=" + TECHNITIUM_API_KEY
        ).json()

        if response["status"] == "error":
            raise CommandError(response["errorMessage"])

        zones = response["response"]["zones"]

        # Filter out unwanted zones
        zones = [
            zone
            for zone in zones
            if zone["name"]
            not in [
                "0.in-addr.arpa",
                "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa",
                "127.in-addr.arpa",
                "255.in-addr.arpa",
                "localhost",
            ]
        ]

        for zone in zones:
            full_subdomain = zone["name"]
            domain = full_subdomain.split(".", 1)[1]
            subdomain = full_subdomain.split(".", 1)[0]

            # Get records
            response = requests.get(
                TECHNITIUM_SERVER_ADDRESS
                + "/api/zones/records/get?token="
                + TECHNITIUM_API_KEY
                + "&domain="
                + full_subdomain
                + "&zone="
                + full_subdomain
            ).json()

            if response["status"] == "error":
                raise CommandError(response["errorMessage"])

            DOMAIN = Domain.objects.filter(domain=domain).first()
            # If Domain does not exist, create it first
            if not DOMAIN:
                DOMAIN = Domain.objects.create(domain=domain)

            records = response["response"]["records"]

            # NS Record
            ns_record = next(
                (record for record in records if record["type"] == "NS"), None
            )
            comments = json.loads(ns_record["comments"])
            # Get user's email from NS record comment
            email = comments["owner"]

            # A Record
            a_record = next(
                (record for record in records if record["type"] == "A"), None
            )
            # Get IPv4 address from A record
            ipv4_address = a_record["rData"]["ipAddress"] if a_record else None

            # AAAA Record
            aaaa_record = next(
                (record for record in records if record["type"] == "AAAA"), None
            )
            # Get IPv4 address from A records
            ipv6_address = aaaa_record["rData"]["ipAddress"] if aaaa_record else None

            USER = CustomUser.objects.filter(email=email).first()
            if not USER:
                # Skip Subdomain creation if the owner does not exist in our records
                self.stdout.write(
                    self.style.WARNING(
                        "User "
                        + email
                        + "who owns "
                        + SUBDOMAIN.subdomain
                        + " not found in database. Skipping..."
                    )
                )
                continue

            SUBDOMAIN = Subdomain.objects.filter(subdomain=subdomain).first()
            if not SUBDOMAIN:
                # Create the Subdomain if it does not exist yet
                SUBDOMAIN = Subdomain.objects.create(
                    subdomain=subdomain,
                    domain=DOMAIN,
                    owner=USER,
                    A_record=ipv4_address,
                    AAAA_record=ipv6_address,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        "Created record" + SUBDOMAIN.subdomain + "owned by" + USER.email
                    )
                )
            else:
                # For Subdomains that exist already, overwrite existing fields to match the DNS server's
                SUBDOMAIN.owner = USER
                SUBDOMAIN.A_record = ipv4_address
                SUBDOMAIN.AAAA_record = ipv6_address
                SUBDOMAIN.save()

        cache.clear()
