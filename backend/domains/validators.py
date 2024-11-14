from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


def validate_subdomain(value):
    def is_not_valid_subdomain(value):
        # Check if the subdomain contains only alphanumeric characters
        return not re.match(r"^[a-zA-Z0-9]+$", value)

    if is_not_valid_subdomain(value):
        raise ValidationError(
            _("Enter a valid subdomain without spaces or dots."),
            code="invalid",
            params={"protocol": _("Subdomain"), "value": value},
        )
