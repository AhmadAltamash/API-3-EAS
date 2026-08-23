from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python < 3.9 fallback - shouldn't be hit given this project's
    # requirements, but avoids a hard crash on import.
    ZoneInfo = None


class SendTimeService:
    """
    Given a buyer's country and (optionally) US state / Canadian
    province, works out:

      - their local timezone
      - the current local time and day there
      - the equivalent current time in India (IST)
      - a recommended B2B cold-email send window, shown in both their
        local time and the corresponding IST window for today

    Timezone mapping is done at the state/province level, which is an
    approximation for states/provinces that span more than one zone
    (e.g. Texas, Michigan, Ontario) - it uses whichever zone covers the
    majority of that state/province's population, not a precise
    per-city lookup. When no state/province is known at all, it falls
    back to that country's single most common business timezone.

    DST is handled automatically: zoneinfo resolves the correct UTC
    offset for "today" in each zone, so the IST conversion is correct
    whether or not the US/Canada side is currently observing daylight
    saving time.
    """

    IST_ZONE = "Asia/Kolkata"

    # Recommended B2B cold-email window. This is NOT an assumption -
    # multiple 2025-2026 studies (SalesHandy, Snov.io, Instantly,
    # Growleads, aggregated across 400+ campaigns and 10M+ emails)
    # converge on Tuesday-Thursday, 9:30-11:30 AM in the recipient's
    # local time as the strongest open/reply window, with a secondary
    # ~2 PM peak. Both are surfaced so this can be adjusted later
    # without touching the rest of the app.
    PRIMARY_WINDOW = (9, 30, 11, 30)
    SECONDARY_WINDOW_HOUR = 14
    RECOMMENDED_DAYS = "Tuesday - Thursday"

    US_STATE_TIMEZONES = {
        "AL": "America/Chicago", "AK": "America/Anchorage",
        "AZ": "America/Phoenix", "AR": "America/Chicago",
        "CA": "America/Los_Angeles", "CO": "America/Denver",
        "CT": "America/New_York", "DE": "America/New_York",
        "FL": "America/New_York", "GA": "America/New_York",
        "HI": "Pacific/Honolulu", "ID": "America/Boise",
        "IL": "America/Chicago", "IN": "America/Indiana/Indianapolis",
        "IA": "America/Chicago", "KS": "America/Chicago",
        "KY": "America/New_York", "LA": "America/Chicago",
        "ME": "America/New_York", "MD": "America/New_York",
        "MA": "America/New_York", "MI": "America/Detroit",
        "MN": "America/Chicago", "MS": "America/Chicago",
        "MO": "America/Chicago", "MT": "America/Denver",
        "NE": "America/Chicago", "NV": "America/Los_Angeles",
        "NH": "America/New_York", "NJ": "America/New_York",
        "NM": "America/Denver", "NY": "America/New_York",
        "NC": "America/New_York", "ND": "America/Chicago",
        "OH": "America/New_York", "OK": "America/Chicago",
        "OR": "America/Los_Angeles", "PA": "America/New_York",
        "RI": "America/New_York", "SC": "America/New_York",
        "SD": "America/Chicago", "TN": "America/Chicago",
        "TX": "America/Chicago", "UT": "America/Denver",
        "VT": "America/New_York", "VA": "America/New_York",
        "WA": "America/Los_Angeles", "WV": "America/New_York",
        "WI": "America/Chicago", "WY": "America/Denver",
        "DC": "America/New_York",
    }

    # Saskatchewan is worth flagging in passing: unlike the rest of
    # Canada it does not observe daylight saving time, so its offset
    # relative to IST shifts by an hour when the rest of North America
    # springs forward/falls back. zoneinfo handles this correctly on
    # its own via America/Regina - no special-casing needed here.
    CA_PROVINCE_TIMEZONES = {
        "AB": "America/Edmonton", "BC": "America/Vancouver",
        "MB": "America/Winnipeg", "NB": "America/Moncton",
        "NL": "America/St_Johns", "NS": "America/Halifax",
        "NT": "America/Yellowknife", "NU": "America/Iqaluit",
        "ON": "America/Toronto", "PE": "America/Halifax",
        "QC": "America/Toronto", "SK": "America/Regina",
        "YT": "America/Whitehorse",
    }

    # Fallback when only the country is known (no state/province) -
    # picks that country's most common business timezone as a rough
    # default, clearly flagged as such in the returned data.
    COUNTRY_DEFAULT_TIMEZONES = {
        "United States": "America/New_York",
        "Canada": "America/Toronto",
    }

    def get_timezone_name(self, country, state=None):

        state_clean = (state or "").strip().upper()

        if country == "United States" and state_clean in self.US_STATE_TIMEZONES:
            return self.US_STATE_TIMEZONES[state_clean], "state"

        if country == "Canada" and state_clean in self.CA_PROVINCE_TIMEZONES:
            return self.CA_PROVINCE_TIMEZONES[state_clean], "province"

        default_tz = self.COUNTRY_DEFAULT_TIMEZONES.get(country)

        if default_tz:
            return default_tz, "country-default"

        return None, None

    def get_send_time_info(self, country, state=None):
        """
        Returns None when the country isn't US/Canada or a timezone
        can't be resolved. Otherwise returns a dict describing local
        time, IST time, and the recommended send window in both.
        """

        if not ZoneInfo:
            return None

        tz_name, precision = self.get_timezone_name(country, state)

        if not tz_name:
            return None

        try:
            local_zone = ZoneInfo(tz_name)
            ist_zone = ZoneInfo(self.IST_ZONE)
        except Exception:
            return None

        now_local = datetime.now(local_zone)
        now_ist = now_local.astimezone(ist_zone)

        start_h, start_m, end_h, end_m = self.PRIMARY_WINDOW

        window_start_local = now_local.replace(
            hour=start_h, minute=start_m, second=0, microsecond=0
        )

        window_end_local = now_local.replace(
            hour=end_h, minute=end_m, second=0, microsecond=0
        )

        secondary_local = now_local.replace(
            hour=self.SECONDARY_WINDOW_HOUR, minute=0,
            second=0, microsecond=0
        )

        window_start_ist = window_start_local.astimezone(ist_zone)
        window_end_ist = window_end_local.astimezone(ist_zone)
        secondary_ist = secondary_local.astimezone(ist_zone)

        return {
            "timezone": tz_name,
            "precision": precision,
            "local_time": now_local.strftime("%I:%M %p").lstrip("0"),
            "local_day": now_local.strftime("%A"),
            "ist_time": now_ist.strftime("%I:%M %p").lstrip("0"),
            "recommended_days": self.RECOMMENDED_DAYS,
            "primary_window_local": (
                f"{window_start_local.strftime('%I:%M %p').lstrip('0')}"
                f" - {window_end_local.strftime('%I:%M %p').lstrip('0')}"
            ),
            "primary_window_ist": (
                f"{window_start_ist.strftime('%I:%M %p').lstrip('0')}"
                f" - {window_end_ist.strftime('%I:%M %p').lstrip('0')} IST"
            ),
            "secondary_window_local": secondary_local.strftime("%I:%M %p").lstrip("0"),
            "secondary_window_ist": secondary_ist.strftime("%I:%M %p").lstrip("0") + " IST",
        }
