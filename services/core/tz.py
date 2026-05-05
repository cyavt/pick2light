"""
Timezone helper — standardize all timestamps to Asia/Ho_Chi_Minh (UTC+7).
"""

from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))


def now_vn() -> datetime:
    """Return current time in Vietnam timezone (UTC+7), as naive datetime."""
    return datetime.now(VN_TZ).replace(tzinfo=None)
