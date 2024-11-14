from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.db import models
from django.urls import reverse
from django.utils import timezone

from config.settings import REQUIRE_ACCOUNT_APPROVALS


class CustomUser(AbstractUser):
    # first_name inherited from base user class
    # last_name inherited from base user class
    # email inherited from base user class
    # TODO: Email length may not fit in DNS record comments for some providers
    # username inherited from base user class
    # password inherited from base user class
    # is_admin inherited from base user class

    # Used for onboarding processes
    # Set this to False later on once the user makes actions
    onboarding = models.BooleanField(default=True)

    # For API instances that require manual account approval
    approved = models.BooleanField(default=(not REQUIRE_ACCOUNT_APPROVALS))

    # Can be used to show tooltips for newer users
    @property
    def is_new(self):
        current_date = timezone.now()
        return self.date_joined + timedelta(days=1) < current_date

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def admin_url(self):
        return reverse("admin:users_customuser_change", args=(self.pk,))
