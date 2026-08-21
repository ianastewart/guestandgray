import hashlib

from django.conf import settings
from django.core.cache import cache


class ThrottleAdminEmails:
    """Caps how many admin-error emails go out in a rolling window, so a
    recurring exception (crash loop, a bot hammering a broken URL) can't
    turn into a flood of mail from the django@ SMTP account to ADMINS.

    Applied as a filter on the 'mail_admins' logging handler. Rate-limits
    per distinct error (same logger/exception/message) and separately
    enforces a global cap across all errors, both backed by the cache
    framework so the limit holds across worker processes.
    """

    def filter(self, record):
        limit = getattr(settings, "ADMIN_ERROR_EMAIL_LIMIT", 5)
        period = getattr(settings, "ADMIN_ERROR_EMAIL_PERIOD", 600)

        signature = self._signature(record)
        if self._over_limit(f"admin-email-throttle:{signature}", limit, period):
            return False
        if self._over_limit("admin-email-throttle:__global__", limit, period):
            return False
        return True

    @staticmethod
    def _signature(record):
        try:
            exc_name = ""
            if record.exc_info and record.exc_info[0]:
                exc_name = record.exc_info[0].__name__
            raw = f"{record.name}:{exc_name}:{record.getMessage()}"
        except Exception:
            raw = f"{record.name}:{record.pathname}:{record.lineno}"
        return hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()

    @staticmethod
    def _over_limit(key, limit, period):
        cache.add(key, 0, period)
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, period)
            count = 1
        return count > limit
