#datetimem and time zones
from datetime import datetime
import phonenumbers
from phonenumbers import timezone as pn_tz
from zoneinfo import ZoneInfo


#get timezone from number
def get_timezone_for_number(number: str | None, default: str = "America/New_York") -> ZoneInfo:
    if not number:
        return ZoneInfo(default)
    try:
        zones = pn_tz.time_zones_for_number(phonenumbers.parse(str(number)))
        return ZoneInfo(zones[0]) if zones and zones[0] != "Etc/Unknown" else ZoneInfo(default)
    except Exception:
        return ZoneInfo(default)

#get colloquial time of day string from timezoneInfo
def get_time_of_day_str(zone_info: ZoneInfo):
    hour = datetime.now(zone_info).hour
    if hour >= 23 or hour < 6:
        return ""
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"
