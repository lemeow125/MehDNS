from config.settings import TECHNITIUM_API_KEY, TECHNITIUM_SERVER_ADDRESS
import requests
import json
from domains.models import Domain, Subdomain
from accounts.models import CustomUser
import requests
from django.core.cache import cache

# TODO: Refactor tasks to support both multiple DNS backends (Technitium, PowerDNS, Cloudflare, etc.)


def update_ns_zone_comments(zone, owner_email):
    comment = {"owner": owner_email}

    comment = json.dumps(comment)

    # Update Zone NS record comment section to contain owner email
    response = requests.get(
        TECHNITIUM_SERVER_ADDRESS
        + "/api/zones/records/update?token="
        + TECHNITIUM_API_KEY
        + "&domain="
        + zone
        + "&zone="
        + zone
        + "&type=NS&overwrite=true&nameServer=ns1.06222001.xyz&comments="
        + comment
    ).json()

    if response["status"] == "error":
        raise Exception(f"DNS API Failure: {response['errorMessage']}")


def create_zone(zone, owner_email, overwrite=False):
    # Create DNS Zone
    response = requests.get(
        TECHNITIUM_SERVER_ADDRESS
        + "/api/zones/create?token="
        + TECHNITIUM_API_KEY
        + "&zone="
        + zone
        + "&type=Primary"
    ).json()
    if response["status"] == "error":
        if "Zone already exists" in response["errorMessage"] and overwrite:
            pass
        else:
            raise Exception(response["errorMessage"])

    update_ns_zone_comments(zone, owner_email)


def delete_zone(zone):
    # Delete DNS Zone
    response = requests.get(
        TECHNITIUM_SERVER_ADDRESS
        + "/api/zones/delete?token="
        + TECHNITIUM_API_KEY
        + "&zone="
        + zone
    ).json()
    if response["status"] == "error":
        raise Exception(f"DNS API Failure: {response['errorMessage']}")


def update_a_record(subdomain, a_record):
    # Updates the A record for a zone or creates one if it doesn't exist yet
    response = requests.get(
        TECHNITIUM_SERVER_ADDRESS
        + "/api/zones/records/add?token="
        + TECHNITIUM_API_KEY
        + "&zone="
        + subdomain
        + "&domain="
        + subdomain
        + "&ipAddress="
        + a_record
        + "&type=A&overwrite=true&ttl=60"
    ).json()
    if response["status"] == "error":
        # TODO: Push error notification here
        raise Exception(f"DNS API Failure: {response['errorMessage']}")


def update_aaaa_record(subdomain, aaaa_record):
    # Updates the AAAA record for a zone or creates one if it doesn't exist yet
    response = requests.get(
        TECHNITIUM_SERVER_ADDRESS
        + "/api/zones/records/add?token="
        + TECHNITIUM_API_KEY
        + "&zone="
        + subdomain
        + "&domain="
        + subdomain
        + "&ipAddress="
        + aaaa_record
        + "&type=AAAA&overwrite=true&ttl=60"
    ).json()
    if response["status"] == "error":
        # TODO: Push error notification here
        raise Exception(f"DNS API Failure: {response['errorMessage']}")


def update_txt_record(subdomain, txt_record):
    # Updates the TXT record for a zone or creates one if it doesn't exist yet
    response = requests.get(
        TECHNITIUM_SERVER_ADDRESS
        + "/api/zones/records/add?token="
        + TECHNITIUM_API_KEY
        + "&zone="
        + subdomain
        + "&domain="
        + subdomain
        + "&text="
        + txt_record
        + "&type=TXT&overwrite=true&ttl=60"
    ).json()
    if response["status"] == "error":
        # TODO: Push error notification here
        # Revert TXT record in DB to value in DNS server
        SUBDOMAIN = Subdomain.objects.get(full_subdomain=subdomain)
        SUBDOMAIN.TXT_record = txt_record
        SUBDOMAIN.save()
        raise Exception(f"DNS API Failure: {response['errorMessage']}")


def pull_records():
    # Query the DNS Server for all zones to sync to DB
    response = requests.get(
        TECHNITIUM_SERVER_ADDRESS + "/api/zones/list?token=" + TECHNITIUM_API_KEY
    ).json()

    if response["status"] == "error":
        raise Exception(response["errorMessage"])

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
            raise Exception(response["errorMessage"])

        DOMAIN = Domain.objects.filter(domain=domain).first()
        # If Domain does not exist, create it first
        if not DOMAIN:
            DOMAIN = Domain.objects.create(domain=domain)

        records = response["response"]["records"]

        # NS Record
        ns_record = next((record for record in records if record["type"] == "NS"), None)
        comments = json.loads(ns_record["comments"])
        # Get user's email from NS record comment
        email = comments["owner"]

        # A Record
        a_record = next((record for record in records if record["type"] == "A"), None)
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
            print(
                "User "
                + email
                + "who owns "
                + SUBDOMAIN.subdomain
                + " not found in database. Skipping..."
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
            print("Created record" + SUBDOMAIN.subdomain + "owned by" + USER.email)

        else:
            # For Subdomains that exist already, overwrite existing fields to match the DNS server's
            SUBDOMAIN.owner = USER
            SUBDOMAIN.A_record = ipv4_address
            SUBDOMAIN.AAAA_record = ipv6_address
            SUBDOMAIN.save()

    cache.clear()
