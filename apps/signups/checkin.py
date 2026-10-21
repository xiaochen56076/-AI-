import hashlib
import hmac
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.utils import timezone

from apps.activities.models import Activity

WINDOW_SECONDS = 30
CHECKIN_EARLY_MINUTES = 30
CHECKIN_CODE_LENGTH = 8


def current_bucket(at=None) -> int:
    at = at or timezone.now()
    return int(at.timestamp()) // WINDOW_SECONDS


def _digest(secret: str, payload: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def code_for_bucket(activity: Activity, bucket: int) -> str:
    return _digest(activity.checkin_secret, f"{activity.pk}:{bucket}")[:CHECKIN_CODE_LENGTH].upper()


def static_code(activity: Activity) -> str:
    return _digest(activity.checkin_secret, f"{activity.pk}:static")[:CHECKIN_CODE_LENGTH].upper()


def generate_code(activity: Activity, at=None) -> tuple[str, datetime | None]:
    at = at or timezone.now()
    if activity.checkin_mode == Activity.CheckinMode.STATIC:
        return static_code(activity), None
    bucket = current_bucket(at)
    expires_at = datetime.fromtimestamp(
        (bucket + 1) * WINDOW_SECONDS, tz=timezone.get_current_timezone()
    )
    return code_for_bucket(activity, bucket), expires_at


def verify_code(activity: Activity, code: str, at=None) -> bool:
    submitted = (code or "").strip().upper()
    if len(submitted) != CHECKIN_CODE_LENGTH:
        return False
    at = at or timezone.now()
    if activity.checkin_mode == Activity.CheckinMode.STATIC:
        candidates = [static_code(activity)]
    elif activity.checkin_mode == Activity.CheckinMode.DYNAMIC:
        bucket = current_bucket(at)
        candidates = [code_for_bucket(activity, bucket + offset) for offset in (-1, 0, 1)]
    else:
        return False
    return any(hmac.compare_digest(submitted, candidate) for candidate in candidates)


def checkin_window(activity: Activity) -> tuple:
    return (
        activity.start_time - timedelta(minutes=CHECKIN_EARLY_MINUTES),
        activity.end_time,
    )


def is_checkin_open(activity: Activity, at=None) -> bool:
    at = at or timezone.now()
    start, end = checkin_window(activity)
    return (
        activity.status == Activity.Status.PUBLISHED
        and activity.checkin_mode != Activity.CheckinMode.NONE
        and start <= at <= end
    )


def qr_content(activity: Activity, code: str) -> str:
    return "campushub://checkin?" + urlencode({"activity_id": activity.pk, "code": code})
