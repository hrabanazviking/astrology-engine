#!/usr/bin/env python3
"""
ASTROLOGY ENGINE — Volmarr's Longhall / Hermes Divination Skill
================================================================
Full-spectrum astrological computation for the Hermes Agent.

Capabilities:
  natal          Full natal chart — planets, houses, aspects, dignities, lots
  transit        Current sky transiting natal positions
  synastry       Two-chart overlay for relationship analysis
  solar-return   Solar return chart for a given year
  progressions   Secondary progressed chart
  lunar          Current lunar phase, void-of-course, next lunation
  planet-hours   Planetary hours for today or a given date
  aspect-grid    Full aspect matrix for a chart
  dignity        Complete dignity table for a chart
  lots           Arabic Lots / Hermetic Parts for a chart
  antiscia       Antiscia and contra-antiscia for a chart
  hellenistic    Sect, bonification, joy, triplicity, and sect light

Usage:
  python3 astrology_engine.py natal --date 1975-11-22 --time 14:30 --city Indianapolis --nation US --name Volmarr
  python3 astrology_engine.py transit --date 1975-11-22 --time 14:30 --city Indianapolis --nation US
  python3 astrology_engine.py synastry --date1 1975-11-22 --date2 1980-03-15
  python3 astrology_engine.py solar-return --date 1975-11-22 --time 14:30 --city Indianapolis --nation US --year 2026
  python3 astrology_engine.py progressions --date 1975-11-22 --time 14:30 --city Indianapolis --nation US --prog-date 2026-05-03
  python3 astrology_engine.py lunar
  python3 astrology_engine.py planet-hours --date 2026-05-03 --lat 39.7684 --lon -86.1581
  python3 astrology_engine.py lots --date 1975-11-22 --time 14:30 --city Indianapolis --nation US
  python3 astrology_engine.py hellenistic --date 1975-11-22 --time 14:30 --city Indianapolis --nation US
"""

import argparse
import datetime
import sys
import io
import math
import textwrap
import warnings

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Suppress verbose kerykeion geonames warning
warnings.filterwarnings("ignore", message=".*GEONAMES.*")
warnings.filterwarnings("ignore", message=".*geonames.*")

try:
    import swisseph as swe
    SWE = True
except ImportError:
    SWE = False
    print("WARNING: pyswisseph not installed. pip install pyswisseph", file=sys.stderr)

try:
    from kerykeion import AstrologicalSubject
    KK = True
except ImportError:
    KK = False

# ---------------------------------------------------------------------------
# GEO / TIMEZONE BACKENDS  (loaded lazily — only on first use)
# ---------------------------------------------------------------------------
_nominatim  = None   # geopy Nominatim geocoder instance
_tf         = None   # TimezoneFinder instance
_GEO_AVAIL  = None   # bool: is geopy available?
_TZ_AVAIL   = None   # bool: is timezonefinder available?

def _geo():
    """Lazily initialise Nominatim geocoder."""
    global _nominatim, _GEO_AVAIL
    if _GEO_AVAIL is None:
        try:
            from geopy.geocoders import Nominatim
            _nominatim = Nominatim(user_agent="volmarr_astrology_engine/3.0", timeout=6)
            _GEO_AVAIL = True
        except Exception:
            _GEO_AVAIL = False
    return _nominatim if _GEO_AVAIL else None

def _tzf():
    """Lazily initialise TimezoneFinder."""
    global _tf, _TZ_AVAIL
    if _TZ_AVAIL is None:
        try:
            from timezonefinder import TimezoneFinder
            _tf = TimezoneFinder()
            _TZ_AVAIL = True
        except Exception:
            _TZ_AVAIL = False
    return _tf if _TZ_AVAIL else None

import logging
logging.getLogger("geopy").setLevel(logging.ERROR)
logging.getLogger("kerykeion").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

W = 76  # output width

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_SYMBOL = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
ELEMENTS = {
    "Aries": "Fire", "Taurus": "Earth", "Gemini": "Air", "Cancer": "Water",
    "Leo": "Fire", "Virgo": "Earth", "Libra": "Air", "Scorpio": "Water",
    "Sagittarius": "Fire", "Capricorn": "Earth", "Aquarius": "Air", "Pisces": "Water",
}
MODALITIES = {
    "Aries": "Cardinal", "Taurus": "Fixed", "Gemini": "Mutable",
    "Cancer": "Cardinal", "Leo": "Fixed", "Virgo": "Mutable",
    "Libra": "Cardinal", "Scorpio": "Fixed", "Sagittarius": "Mutable",
    "Capricorn": "Cardinal", "Aquarius": "Fixed", "Pisces": "Mutable",
}

# Planets and their Swiss Ephemeris IDs
PLANETS = {
    "Sun":      0,
    "Moon":     1,
    "Mercury":  2,
    "Venus":    3,
    "Mars":     4,
    "Jupiter":  5,
    "Saturn":   6,
    "Uranus":   7,
    "Neptune":  8,
    "Pluto":    9,
    "Chiron":   15,
    "Ceres":    17,
    "Pallas":   18,
    "Juno":     19,
    "Vesta":    20,
    "N.Node":   10,   # True Node
    "S.Node":   -1,   # Calculated as 180 from N.Node
}

PLANET_SYMBOL = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
    "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
    "Chiron": "⚷", "Ceres": "⚳", "Pallas": "⚴", "Juno": "⚵", "Vesta": "⚶",
    "N.Node": "☊", "S.Node": "☋",
}

PLANET_KEYWORDS = {
    "Sun":     "Identity · ego · vitality · purpose · the conscious self",
    "Moon":    "Emotion · instinct · memory · the unconscious · the mother",
    "Mercury": "Mind · communication · thought · travel · wit · commerce",
    "Venus":   "Love · beauty · pleasure · values · attraction · what we desire",
    "Mars":    "Drive · ambition · desire · aggression · war · will to act",
    "Jupiter": "Expansion · luck · philosophy · higher learning · faith · abundance",
    "Saturn":  "Discipline · structure · karma · time · restriction · mastery",
    "Uranus":  "Revolution · sudden change · genius · liberation · the unexpected",
    "Neptune": "Dreams · illusion · spirituality · dissolution · the mystical",
    "Pluto":   "Transformation · death/rebirth · power · shadow · the underworld",
    "Chiron":  "Wounded healer · core wound · teaching through suffering",
    "Ceres":   "Nurture · grief · cycles of loss and return · harvest",
    "Pallas":  "Wisdom · strategy · craft · pattern recognition · justice",
    "Juno":    "Partnership · commitment · equality · betrayal in union",
    "Vesta":   "Devotion · sacred flame · focus · sacrifice · the priestess",
    "N.Node":  "Soul's direction · karmic growth · the path forward",
    "S.Node":  "Past life gifts · karmic comfort zone · what must be released",
}

# Norse god correspondences for planets
NORSE_CORRESPONDENCES = {
    "Sun":     "Sól — the radiant one, light of the world-tree",
    "Moon":    "Máni — the moon-god, measurer of time and tides",
    "Mercury": "Oðinn — master of runes, speech, traveler between worlds",
    "Venus":   "Freyja — goddess of love, beauty, war, and seiðr",
    "Mars":    "Týr — god of justice, battle, and the sacred oath",
    "Jupiter": "Þórr — protector, law-giver, might of expansion",
    "Saturn":  "Oðinn in his Allfather aspect — time, fate, and hard wisdom",
    "Uranus":  "Loki — chaos-bringer, liberator, the trickster who reshapes",
    "Neptune": "Njörðr — god of sea, mist, dissolution, and the deep",
    "Pluto":   "Hel — ruler of Niflheim, death, transformation, the unseen",
    "Chiron":  "Mímir — the wounded sage whose severed head holds all wisdom",
    "N.Node":  "The Norns drawing wyrd-thread toward Urðarbrunnr",
    "S.Node":  "The wyrd already woven — what the Norns cut away",
}

# Rune correspondences for signs
SIGN_RUNES = {
    "Aries":       ("Tiwaz", "ᛏ", "Justice, sacrifice, directed will"),
    "Taurus":      ("Fehu",  "ᚠ", "Wealth, cattle, primal fire of creation"),
    "Gemini":      ("Ansuz", "ᚨ", "Divine breath, Oðinn's speech, inspiration"),
    "Cancer":      ("Berkano","ᛒ", "Birth, the birch, nurturing, the hidden"),
    "Leo":         ("Sowilo","ᛋ", "The sun, victory, life-force, wholeness"),
    "Virgo":       ("Jera",  "ᛃ", "Harvest, cycles, patience, right action"),
    "Libra":       ("Gebo",  "ᚷ", "Gift, exchange, sacred union, balance"),
    "Scorpio":     ("Hagalaz","ᚺ", "Hailstorm, disruption, radical transformation"),
    "Sagittarius": ("Raidho","ᚱ", "The ride, journey, cosmic order, the quest"),
    "Capricorn":   ("Isa",   "ᛁ", "Ice, stillness, ego-structure, frozen will"),
    "Aquarius":    ("Laguz", "ᛚ", "Water, flow, the unconscious, psychic depth"),
    "Pisces":      ("Perthro","ᛈ", "The dice cup, fate, mystery, the hidden well"),
}

# Aspects: name -> (angle, orb_for_luminaries, orb_for_others, glyph, quality)
ASPECTS = {
    "Conjunction":  (0,   10, 8,  "☌", "fusion"),
    "Opposition":   (180, 10, 8,  "☍", "polarity"),
    "Trine":        (120, 8,  7,  "△", "harmony"),
    "Square":       (90,  8,  7,  "□", "tension"),
    "Sextile":      (60,  6,  5,  "⚹", "opportunity"),
    "Quincunx":     (150, 3,  3,  "⚻", "adjustment"),
    "Semi-Square":  (45,  3,  2,  "∠", "friction"),
    "Sesquisquare": (135, 3,  2,  "⚼", "agitation"),
    "Semi-Sextile": (30,  2,  2,  "⌛", "subtle link"),
    "Quintile":     (72,  2,  2,  "Q", "creative"),
    "Bi-Quintile":  (144, 2,  2,  "bQ","creative"),
    "Septile":      (51.43, 1, 1, "S", "fated"),
}

# Essential dignities
DOMICILE = {
    "Sun":     ["Leo"],
    "Moon":    ["Cancer"],
    "Mercury": ["Gemini", "Virgo"],
    "Venus":   ["Taurus", "Libra"],
    "Mars":    ["Aries", "Scorpio"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn":  ["Capricorn", "Aquarius"],
    "Uranus":  ["Aquarius"],
    "Neptune": ["Pisces"],
    "Pluto":   ["Scorpio"],
}
DETRIMENT = {
    "Sun":     ["Aquarius"],
    "Moon":    ["Capricorn"],
    "Mercury": ["Sagittarius", "Pisces"],
    "Venus":   ["Aries", "Scorpio"],
    "Mars":    ["Libra", "Taurus"],
    "Jupiter": ["Gemini", "Virgo"],
    "Saturn":  ["Cancer", "Leo"],
    "Uranus":  ["Leo"],
    "Neptune": ["Virgo"],
    "Pluto":   ["Taurus"],
}
EXALTATION = {
    "Sun":     "Aries",
    "Moon":    "Taurus",
    "Mercury": "Virgo",
    "Venus":   "Pisces",
    "Mars":    "Capricorn",
    "Jupiter": "Cancer",
    "Saturn":  "Libra",
    "Uranus":  "Scorpio",
    "Neptune": "Cancer",
    "Pluto":   "Aries",
    "N.Node":  "Gemini",
}
FALL = {v: k for k, v in EXALTATION.items() if isinstance(v, str)}
# Exaltation degrees (traditional)
EXALTATION_DEG = {
    "Sun": ("Aries", 19), "Moon": ("Taurus", 3),
    "Mercury": ("Virgo", 15), "Venus": ("Pisces", 27),
    "Mars": ("Capricorn", 28), "Jupiter": ("Cancer", 15),
    "Saturn": ("Libra", 21),
}

# Ptolemaic terms (Egyptian bounds)
TERMS = {
    "Aries":       [("Jupiter",0,6),("Venus",6,12),("Mercury",12,20),("Mars",20,25),("Saturn",25,30)],
    "Taurus":      [("Venus",0,8),("Mercury",8,14),("Jupiter",14,22),("Saturn",22,27),("Mars",27,30)],
    "Gemini":      [("Mercury",0,6),("Jupiter",6,12),("Venus",12,17),("Mars",17,24),("Saturn",24,30)],
    "Cancer":      [("Mars",0,7),("Venus",7,13),("Mercury",13,19),("Jupiter",19,26),("Saturn",26,30)],
    "Leo":         [("Jupiter",0,6),("Venus",6,11),("Saturn",11,18),("Mercury",18,24),("Mars",24,30)],
    "Virgo":       [("Mercury",0,7),("Venus",7,17),("Jupiter",17,21),("Mars",21,28),("Saturn",28,30)],
    "Libra":       [("Saturn",0,6),("Mercury",6,14),("Jupiter",14,21),("Venus",21,28),("Mars",28,30)],
    "Scorpio":     [("Mars",0,7),("Venus",7,11),("Mercury",11,19),("Jupiter",19,24),("Saturn",24,30)],
    "Sagittarius": [("Jupiter",0,12),("Venus",12,17),("Mercury",17,21),("Saturn",21,26),("Mars",26,30)],
    "Capricorn":   [("Mercury",0,7),("Jupiter",7,14),("Venus",14,22),("Saturn",22,26),("Mars",26,30)],
    "Aquarius":    [("Mercury",0,7),("Venus",7,13),("Jupiter",13,20),("Mars",20,25),("Saturn",25,30)],
    "Pisces":      [("Venus",0,12),("Jupiter",12,16),("Mercury",16,19),("Mars",19,28),("Saturn",28,30)],
}

# Decans / faces (each 10 degrees, traditional Chaldean order)
DECANS = {
    "Aries":       [("Mars",0),("Sun",10),("Venus",20)],
    "Taurus":      [("Mercury",0),("Moon",10),("Saturn",20)],
    "Gemini":      [("Jupiter",0),("Mars",10),("Sun",20)],
    "Cancer":      [("Venus",0),("Mercury",10),("Moon",20)],
    "Leo":         [("Saturn",0),("Jupiter",10),("Mars",20)],
    "Virgo":       [("Sun",0),("Venus",10),("Mercury",20)],
    "Libra":       [("Moon",0),("Saturn",10),("Jupiter",20)],
    "Scorpio":     [("Mars",0),("Sun",10),("Venus",20)],
    "Sagittarius": [("Mercury",0),("Moon",10),("Saturn",20)],
    "Capricorn":   [("Jupiter",0),("Mars",10),("Sun",20)],
    "Aquarius":    [("Venus",0),("Mercury",10),("Moon",20)],
    "Pisces":      [("Saturn",0),("Jupiter",10),("Mars",20)],
}

# Triplicity rulers (day / night / participating)
TRIPLICITY = {
    "Fire":  ("Sun",   "Jupiter", "Saturn"),
    "Earth": ("Venus", "Moon",    "Mars"),
    "Air":   ("Saturn","Mercury", "Jupiter"),
    "Water": ("Venus", "Mars",    "Moon"),
}

# Planetary joys by house (Hellenistic)
PLANETARY_JOY = {
    "Mercury": 1, "Moon": 3, "Venus": 5, "Mars": 6,
    "Sun": 9, "Jupiter": 11, "Saturn": 12,
}

# House meanings (brief)
HOUSE_KEYWORDS = [
    (1,  "Self · appearance · body · first impressions · the persona"),
    (2,  "Resources · money · possessions · self-worth · what sustains"),
    (3,  "Communication · siblings · local travel · early learning · the mind"),
    (4,  "Home · family · roots · ancestry · the foundation of the soul"),
    (5,  "Creativity · romance · children · pleasure · self-expression"),
    (6,  "Work · health · daily routine · service · the body as tool"),
    (7,  "Partnership · marriage · open enemies · projection · the other"),
    (8,  "Death · transformation · shared resources · occult · the shadow"),
    (9,  "Philosophy · religion · long travel · higher learning · the quest"),
    (10, "Career · public image · father · ambition · legacy · the peak"),
    (11, "Friends · community · hopes · ideals · the collective · the future"),
    (12, "Hidden enemies · karma · isolation · spirituality · the unconscious"),
]

# Planetary hours order (Chaldean sequence)
CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
DAY_RULERS = {
    0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury",
    4: "Jupiter", 5: "Venus", 6: "Saturn",
}  # weekday (Mon=0) -> day ruler

# Arabic Lots formulas: (name, day_formula, night_formula)
# Formula: (from_planet, to_planet, add_asc) -- all longitudes
# Day: ASC + to - from   Night: ASC + from - to
LOTS_FORMULAS = [
    ("Lot of Fortune",    "Moon",    "Sun"),
    ("Lot of Spirit",     "Sun",     "Moon"),
    ("Lot of Eros",       "Venus",   "Spirit"),    # Spirit = computed
    ("Lot of Necessity",  "Mercury", "Fortune"),   # Fortune = computed
    ("Lot of Courage",    "Mars",    "Fortune"),
    ("Lot of Victory",    "Jupiter", "Spirit"),
    ("Lot of Nemesis",    "Saturn",  "Fortune"),
]

# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def hr(char="─"):
    return char * W

def header(title, subtitle=None):
    print()
    print("╔" + "═" * (W - 2) + "╗")
    line = f"  ✦ {title} ✦"
    print("║" + line.center(W - 2) + "║")
    if subtitle:
        sub = f"  {subtitle}"
        print("║" + sub.center(W - 2) + "║")
    print("╚" + "═" * (W - 2) + "╝")
    print()

def section(title):
    print()
    print(f"  ┌─ {title} " + "─" * max(0, W - len(title) - 6) + "┐")

def wrap_print(text, indent=4):
    for line in textwrap.wrap(text, W - indent):
        print(" " * indent + line)

def deg_to_sign(deg):
    """Convert ecliptic longitude to sign, degree, minutes."""
    deg = deg % 360
    idx = int(deg // 30)
    d = int(deg % 30)
    m = int((deg % 1) * 60)
    return SIGNS[idx], idx, d, m

def sign_idx(sign_name):
    return SIGNS.index(sign_name)

def lon_from_sign_deg(sign, deg):
    return SIGNS.index(sign) * 30 + deg

def angle_diff(a, b):
    """Shortest arc between two longitudes."""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d

def julian_day(year, month, day, hour=12.0):
    if SWE:
        return swe.julday(year, month, day, hour)
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return float(jdn) + (hour - 12.0) / 24.0

def parse_date_time(date_str, time_str=None):
    """Parse date/time strings. Returns (y, mo, d, local_hour). No timezone conversion."""
    y, mo, d = map(int, date_str.split("-"))
    hour = 12.0
    if time_str:
        parts = time_str.split(":")
        hour = float(parts[0]) + float(parts[1]) / 60.0
    return y, mo, d, hour


def resolve_timezone(lat, lon):
    """Return IANA timezone name for a lat/lon, or None if unavailable."""
    tf = _tzf()
    if tf and lat is not None and lon is not None:
        try:
            return tf.timezone_at(lng=float(lon), lat=float(lat))
        except Exception:
            pass
    return None


def local_to_utc(year, month, day, local_hour, tz_name):
    """Convert a local datetime to UTC. Returns (utc_hour, utc_offset_str).

    Uses pytz with full historical DST data — handles old/unusual rules correctly.
    Falls back to local_hour if pytz unavailable.
    """
    try:
        import pytz
        tz = pytz.timezone(tz_name)
        h  = int(local_hour)
        mi = int(round((local_hour - h) * 60))
        # localize handles DST ambiguity: is_dst=False = standard time (safe for birth times)
        local_dt = tz.localize(datetime.datetime(year, month, day, h, mi, 0), is_dst=None)
    except Exception:
        try:
            import pytz
            tz = pytz.timezone(tz_name)
            h  = int(local_hour)
            mi = int(round((local_hour - h) * 60))
            local_dt = tz.localize(datetime.datetime(year, month, day, h, mi, 0), is_dst=False)
        except Exception:
            return local_hour, "UTC±?"
    try:
        import pytz
        utc_dt = local_dt.astimezone(pytz.utc)
        utc_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        offset   = local_dt.utcoffset()
        total_m  = int(offset.total_seconds() / 60)
        sign     = "+" if total_m >= 0 else "-"
        abs_m    = abs(total_m)
        utc_offset_str = f"UTC{sign}{abs_m//60:02d}:{abs_m%60:02d}"
        return utc_hour, utc_offset_str
    except Exception:
        return local_hour, "UTC±?"


def resolve_birth(date_str, time_str, city, nation="",
                  lat_override=None, lon_override=None):
    """One-stop resolution of birth data → (y, mo, d, utc_hour, lat, lon, tz_name, tz_label).

    Steps:
      1. Parse date/time (local)
      2. Geocode city → (lat, lon)
      3. Lookup IANA timezone for that location
      4. Convert local time → UTC
      5. Return everything needed for Julian day and display

    Returns:
      y, mo, d       — integers
      utc_hour       — float (hours in UT/UTC for swe.julday)
      lat, lon       — floats
      tz_name        — IANA name e.g. "America/Indiana/Indianapolis"
      tz_label       — display string e.g. "14:30 LT  →  19:30 UTC  (UTC-05:00 EST)"
      time_known     — False if time_str was None (noon default used)
    """
    y, mo, d, local_hour = parse_date_time(date_str, time_str)
    time_known = time_str is not None

    lat, lon, city_resolved = geocode_city(city, nation, lat_override, lon_override)
    city_default_used = not city_resolved

    tz_name = resolve_timezone(lat, lon)

    if tz_name and time_known:
        utc_hour, utc_offset_str = local_to_utc(y, mo, d, local_hour, tz_name)
        utc_h = int(utc_hour)
        utc_m = int(round((utc_hour - utc_h) * 60))
        lh = int(local_hour)
        lm = int(round((local_hour - lh) * 60))
        tz_label = (f"{lh:02d}:{lm:02d} LT  →  {utc_h:02d}:{utc_m:02d} UTC  "
                    f"({utc_offset_str}  {tz_name})")
    elif tz_name and not time_known:
        utc_hour = local_hour  # noon is close enough without known time
        tz_label = f"Time unknown — using 12:00 noon  ({tz_name})"
    else:
        utc_hour = local_hour
        tz_label = "Timezone unknown — treating input as UTC"

    return y, mo, d, utc_hour, lat, lon, tz_name or "UTC", tz_label, time_known, city_default_used

def geocode_city(city, nation="", lat_override=None, lon_override=None):
    """Resolve city → (lat, lon, city_resolved).
    
    city_resolved is True if the city name was actually matched (not defaulted).

    Priority:
      1. Explicit --lat / --lon flags
      2. Nominatim (OpenStreetMap, no API key, requires internet)
      3. kerykeion built-in geonames DB
      4. Hardcoded ~120-city fallback table
      5. Warn + return (0, 0)
    """
    if lat_override is not None and lon_override is not None:
        return float(lat_override), float(lon_override), False

    # --- Nominatim (most accurate, works for any city worldwide) ---
    if city:
        geo = _geo()
        if geo:
            query = f"{city}, {nation}".strip(", ")
            try:
                loc = geo.geocode(query)
                if loc:
                    return loc.latitude, loc.longitude, True
                # Retry without nation code in case nation is a 2-letter code that confuses it
                if nation and len(nation) == 2:
                    loc2 = geo.geocode(city)
                    if loc2:
                        return loc2.latitude, loc2.longitude, True
            except Exception:
                pass

    # --- kerykeion geonames ---
    if KK and city:
        try:
            import logging
            logging.disable(logging.CRITICAL)
            tmp = AstrologicalSubject("_", 2000, 1, 1, 12, 0, city, nation or "")
            logging.disable(logging.NOTSET)
            if tmp.lat and tmp.lng:
                return tmp.lat, tmp.lng, True
        except Exception:
            pass

    # --- hardcoded fallback (~400 cities: US state capitals, top US metros, major world) ---
    CITIES = {
        # ── US — Indiana region (home) ──
        "indianapolis": (39.7684, -86.1581),
        "angola": (41.6337, -84.9994),
        "fort wayne": (41.0793, -85.1394),
        "south bend": (41.6764, -86.2520),
        "elkhart": (41.6815, -85.9775),
        "gary": (41.5934, -87.3464),
        "lafayette": (40.4167, -86.8753),
        "west lafayette": (40.4259, -86.9081),
        "muncie": (40.1934, -85.3864),
        "terre haute": (39.4662, -87.3414),
        "bloomington": (39.1653, -86.5264),
        "evansville": (37.9715, -87.5698),
        "carmel": (39.9784, -86.1180),
        "fishers": (39.9517, -86.0197),
        "noblesville": (40.0496, -86.0086),
        # ── US — State Capitals (all 50) ──
        "montgomery": (32.3792, -86.3071),
        "juneau": (58.3019, -134.4197),
        "phoenix": (33.4484, -112.0740),
        "little rock": (34.7465, -92.2896),
        "sacramento": (38.5816, -121.4944),
        "denver": (39.7392, -104.9903),
        "hartford": (41.7658, -72.6734),
        "dover": (39.1582, -75.5244),
        "tallahassee": (30.4383, -84.2807),
        "atlanta": (33.7490, -84.3880),
        "honolulu": (21.3069, -157.8583),
        "boise": (43.6150, -116.2023),
        "springfield": (39.8017, -89.6437),
        "indianapolis": (39.7684, -86.1581),
        "des moines": (41.6005, -93.6091),
        "topeka": (39.0473, -95.6892),
        "frankfort": (38.1870, -84.8683),
        "baton rouge": (30.4583, -91.1403),
        "augusta": (44.3106, -69.7796),
        "annapolis": (38.9786, -76.4918),
        "boston": (42.3601, -71.0589),
        "lansing": (42.7325, -84.5555),
        "st. paul": (44.9537, -93.0900),
        "jackson": (32.2988, -90.1848),
        "jefferson city": (38.5721, -92.1893),
        "helena": (46.5927, -112.0361),
        "lincoln": (40.8081, -96.7003),
        "carson city": (39.1600, -119.7528),
        "concord": (43.2087, -71.5376),
        "trenton": (40.2206, -74.7566),
        "santa fe": (35.6872, -105.9378),
        "albany": (42.6526, -73.7562),
        "raleigh": (35.7796, -78.6382),
        "bismarck": (46.8083, -100.7837),
        "columbus": (39.9612, -82.9988),
        "oklahoma city": (35.4676, -97.5164),
        "salem": (44.9426, -123.0351),
        "harrisburg": (40.2698, -76.8756),
        "providence": (41.8240, -71.4128),
        "columbia": (34.0007, -81.0348),
        "pierre": (44.3683, -100.3512),
        "nashville": (36.1627, -86.7816),
        "austin": (30.2672, -97.7431),
        "salt lake city": (40.7608, -111.8910),
        "montpelier": (44.2601, -72.5806),
        "richmond": (37.5407, -77.4360),
        "olympia": (47.0379, -122.9007),
        "charleston": (38.3498, -81.6326),
        "madison": (43.0731, -89.4012),
        "cheyenne": (41.1400, -104.8197),
        # ── US — Northeast ──
        "new york": (40.7128, -74.0060),
        "new york city": (40.7128, -74.0060),
        "nyc": (40.7128, -74.0060),
        "manhattan": (40.7831, -73.9712),
        "brooklyn": (40.6782, -73.9442),
        "schenectady": (42.7603, -73.9334),
        "buffalo": (42.8864, -78.8784),
        "rochester": (43.1566, -77.6088),
        "philadelphia": (39.9526, -75.1652),
        "pittsburgh": (40.4406, -79.9959),
        "washington": (38.9072, -77.0369),
        "washington dc": (38.9072, -77.0369),
        "baltimore": (39.2904, -76.6122),
        "newark": (40.7357, -74.1724),
        "jersey city": (40.7178, -74.0436),
        "boston": (42.3601, -71.0589),
        "worcester": (42.2626, -71.8023),
        "springfield ma": (42.1015, -72.5898),
        "portland me": (43.6591, -70.2568),
        "burlington vt": (44.4759, -73.2121),
        "manchester nh": (42.9956, -71.4548),
        # ── US — Midwest ──
        "chicago": (41.8781, -87.6298),
        "detroit": (42.3314, -83.0458),
        "cincinnati": (39.1031, -84.5120),
        "cleveland": (41.4993, -81.6944),
        "minneapolis": (44.9778, -93.2650),
        "milwaukee": (43.0389, -87.9065),
        "kansas city": (39.0997, -94.5786),
        "st. louis": (38.6270, -90.1994),
        "st louis": (38.6270, -90.1994),
        "memphis": (35.1495, -90.0490),
        "louisville": (38.2527, -85.7585),
        "columbus": (39.9612, -82.9988),
        "indianapolis": (39.7684, -86.1581),
        "omaha": (41.2565, -95.9345),
        "wichita": (37.6889, -97.3360),
        "duluth": (46.7867, -92.1005),
        "fargo": (46.8772, -96.7898),
        "sioux falls": (43.5446, -96.7311),
        "grand rapids": (42.9634, -85.6681),
        "dayton": (39.7589, -84.1916),
        "akron": (41.0814, -81.5190),
        "toledo": (41.6639, -83.5552),
        "ann arbor": (42.2808, -83.7430),
        "madison": (43.0731, -89.4012),
        # ── US — South ──
        "houston": (29.7604, -95.3698),
        "dallas": (32.7767, -96.7970),
        "san antonio": (29.4241, -98.4936),
        "miami": (25.7617, -80.1918),
        "jacksonville": (30.3322, -81.6557),
        "charlotte": (35.2271, -80.8431),
        "new orleans": (29.9511, -90.0715),
        "orlando": (28.5384, -81.3792),
        "tampa": (27.9506, -82.4572),
        "nashville": (36.1627, -86.7816),
        "raleigh": (35.7796, -78.6382),
        "charleston": (32.7766, -79.9311),
        "savannah": (32.0809, -81.0912),
        "richmond": (37.5407, -77.4360),
        "virginia beach": (36.8529, -75.9780),
        "atlanta": (33.7490, -84.3880),
        "chattanooga": (35.0458, -85.3097),
        "birmingham al": (33.5186, -86.8104),
        "mobile": (30.6954, -88.0399),
        "jackson ms": (32.2988, -90.1848),
        "little rock": (34.7465, -92.2896),
        "baton rouge": (30.4583, -91.1403),
        "lexington": (38.0406, -84.5037),
        "knoxville": (35.9606, -83.9207),
        # ── US — Southwest ──
        "los angeles": (34.0522, -118.2437),
        "san francisco": (37.7749, -122.4194),
        "san diego": (32.7157, -117.1611),
        "las vegas": (36.1699, -115.1398),
        "phoenix": (33.4484, -112.0740),
        "albuquerque": (35.0844, -106.6504),
        "el paso": (31.7619, -106.4850),
        "tucson": (32.2226, -110.9747),
        "austin": (30.2672, -97.7431),
        "dallas": (32.7767, -96.7970),
        "fort worth": (32.7555, -97.3308),
        "oklahoma city": (35.4676, -97.5164),
        "santa fe": (35.6872, -105.9378),
        "reno": (39.5296, -119.8138),
        # ── US — Northwest / Mountain ──
        "seattle": (47.6062, -122.3321),
        "portland": (45.5051, -122.6750),
        "portland or": (45.5051, -122.6750),
        "denver": (39.7392, -104.9903),
        "salt lake city": (40.7608, -111.8910),
        "boise": (43.6150, -116.2023),
        "spokane": (47.6588, -117.4260),
        "tacoma": (47.2465, -122.4384),
        "eugene": (44.0521, -123.0868),
        "bend": (44.0582, -121.3153),
        "missoula": (46.8720, -113.9940),
        "billings": (45.7833, -108.5007),
        "anchorage": (61.2181, -149.9003),
        "fairbanks": (64.8378, -147.7164),
        # ── US — Mountain West ──
        "phoenix": (33.4484, -112.0740),
        "tucson": (32.2226, -110.9747),
        "mesa": (33.4152, -111.8314),
        "chandler": (33.3062, -111.8412),
        "scottsdale": (33.4942, -111.9260),
        "las vegas": (36.1699, -115.1398),
        "albuquerque": (35.0844, -106.6504),
        "denver": (39.7392, -104.9903),
        "colorado springs": (38.8339, -104.8214),
        "aurora": (39.7294, -104.8319),
        "salt lake city": (40.7608, -111.8910),
        "provo": (40.2338, -111.6585),
        "boise": (43.6150, -116.2023),
        "cheyenne": (41.1400, -104.8197),
        "casper": (42.8346, -106.3251),
        # ── Canada ──
        "toronto": (43.6532, -79.3832),
        "vancouver": (49.2827, -123.1207),
        "montreal": (45.5017, -73.5673),
        "ottawa": (45.4215, -75.6972),
        "calgary": (51.0447, -114.0719),
        "edmonton": (53.5461, -113.4938),
        "winnipeg": (49.8951, -97.1384),
        "halifax": (44.6488, -63.5752),
        "quebec city": (46.8139, -71.2080),
        "victoria": (48.4284, -123.3656),
        "regina": (50.4452, -104.6189),
        "saskatoon": (52.1294, -106.3469),
        "st. john's": (47.5615, -52.7126),
        # ── Nordic ──
        "oslo": (59.9139, 10.7522),
        "stockholm": (59.3293, 18.0686),
        "copenhagen": (55.6761, 12.5683),
        "helsinki": (60.1699, 24.9384),
        "reykjavik": (64.1355, -21.8954),
        "bergen": (60.3913, 5.3221),
        "tromso": (69.6496, 18.9560),
        "gothenburg": (57.7089, 11.9746),
        "malmo": (55.6050, 13.0000),
        "tampere": (61.4978, 23.7610),
        "oulu": (65.0121, 25.4681),
        "turku": (60.4518, 22.2666),
        "helsingoer": (56.0362, 12.6136),
        "stavanger": (58.9700, 5.7330),
        "trondheim": (63.4305, 10.3951),
        "uppsala": (59.8586, 17.6389),
        "lund": (55.7047, 13.1910),
        "umea": (63.8258, 20.2630),
        "tartu": (58.3782, 26.7147),
        "tallinn": (59.4370, 24.7536),
        "rikshospitalet": (59.9509, 10.7291),
        "odense": (55.4038, 10.3794),
        # ── British Isles ──
        "london": (51.5074, -0.1278),
        "dublin": (53.3498, -6.2603),
        "edinburgh": (55.9533, -3.1883),
        "manchester": (53.4808, -2.2426),
        "birmingham uk": (52.4862, -1.8904),
        "birmingham": (52.4862, -1.8904),
        "glasgow": (55.8642, -4.2518),
        "bristol": (51.4545, -2.5879),
        "cambridge": (52.2053, 0.1218),
        "oxford": (51.7520, -1.2577),
        "bath": (51.3803, -2.3580),
        "york": (53.9591, -1.0815),
        "cardiff": (51.4816, -3.1791),
        "liverpool": (53.4106, -2.9779),
        "leeds": (53.8008, -1.5491),
        "sheffield": (53.3811, -1.4701),
        "nottingham": (52.9548, -1.1581),
        "belfast": (54.5973, -5.9301),
        "cork": (51.8985, -8.4756),
        "galway": (53.2707, -9.0568),
        "limerick": (52.6680, -8.6305),
        "aberdeen": (57.1497, -2.0943),
        "inverness": (57.4778, -4.2247),
        "canterbury": (51.2766, 1.0735),
        "brighton": (50.8225, -0.1372),
        # ── Western Europe ──
        "paris": (48.8566, 2.3522),
        "lyon": (45.7640, 4.8357),
        "marseille": (43.2965, 5.3698),
        "toulouse": (43.6047, 1.4442),
        "nice": (43.7102, 7.2620),
        "bordeaux": (44.8378, -0.5792),
        "strasbourg": (48.5734, 7.7521),
        "berlin": (52.5200, 13.4050),
        "munich": (48.1351, 11.5820),
        "hamburg": (53.5511, 9.9937),
        "frankfurt": (50.1109, 8.6821),
        "cologne": (50.9375, 6.9603),
        "dresden": (51.0504, 13.7373),
        "dusseldorf": (51.2277, 6.7735),
        "stuttgart": (48.7758, 9.1829),
        "nuremberg": (49.4521, 11.0767),
        "heidelberg": (49.4126, 8.7538),
        "rome": (41.9028, 12.4964),
        "milan": (45.4642, 9.1900),
        "florence": (43.7696, 11.2558),
        "venice": (45.4408, 12.3155),
        "naples": (40.8518, 14.2681),
        "turin": (45.0703, 7.6869),
        "bologna": (44.4949, 11.3426),
        "madrid": (40.4168, -3.7038),
        "barcelona": (41.3874, 2.1686),
        "valencia": (39.4699, -0.3763),
        "seville": (37.3891, -5.9845),
        "bilbao": (43.2630, -2.9350),
        "amsterdam": (52.3676, 4.9041),
        "rotterdam": (51.9244, 4.4777),
        "the hague": (52.0705, 4.3007),
        "brussels": (50.8503, 4.3517),
        "antwerp": (51.2194, 4.4025),
        "luxembourg": (49.6117, 6.1300),
        "zurich": (47.3769, 8.5417),
        "geneva": (46.2044, 6.1432),
        "basel": (47.5596, 7.5886),
        "bern": (46.9480, 7.4474),
        "vienna": (48.2082, 16.3738),
        "salzburg": (47.8095, 13.0550),
        "innsbruck": (47.2692, 11.4041),
        # ── Southern & Eastern Europe ──
        "lisbon": (38.7223, -9.1393),
        "porto": (41.1579, -8.6291),
        "athens": (37.9838, 23.7275),
        "thessaloniki": (40.6401, 22.9444),
        "istanbul": (41.0082, 28.9784),
        "ankara": (39.9334, 32.8597),
        "prague": (50.0755, 14.4378),
        "budapest": (47.4979, 19.0402),
        "warsaw": (52.2297, 21.0122),
        "krakow": (50.0647, 19.9450),
        "bucharest": (44.4268, 26.1025),
        "sofia": (42.6977, 23.3219),
        "belgrade": (44.7866, 20.4489),
        "zagreb": (45.8150, 15.9819),
        "ljubljana": (46.0569, 14.5058),
        "bratislava": (48.1486, 17.1077),
        "moscow": (55.7558, 37.6173),
        "st. petersburg": (59.9343, 30.3351),
        "novosibirsk": (55.0084, 82.9357),
        "yekaterinburg": (56.8389, 60.6057),
        "kazan": (55.7887, 49.1221),
        "riga": (56.9496, 24.1052),
        "vilnius": (54.6872, 25.2797),
        "tallinn": (59.4370, 24.7536),
        # ── Middle East ──
        "dubai": (25.2048, 55.2708),
        "abu dhabi": (24.4539, 54.3773),
        "riyadh": (24.7136, 46.6753),
        "jeddah": (21.5433, 39.1728),
        "doha": (25.2854, 51.5310),
        "tehran": (35.6892, 51.3890),
        "istanbul": (41.0082, 28.9784),
        "tel aviv": (32.0853, 34.7818),
        "jerusalem": (31.7683, 35.2137),
        "beirut": (33.8938, 35.5018),
        "cairo": (30.0444, 31.2357),
        "alexandria": (31.2001, 29.9187),
        "amman": (31.9454, 35.9284),
        "muscat": (23.5880, 58.3829),
        "kuwait city": (29.3759, 47.9774),
        # ── Asia-Pacific ──
        "tokyo": (35.6762, 139.6503),
        "osaka": (34.6937, 135.5023),
        "kyoto": (35.0116, 135.7681),
        "yokohama": (35.4437, 139.6380),
        "nagoya": (35.1815, 136.9066),
        "sapporo": (43.0621, 141.3544),
        "fukuoka": (33.5904, 130.4017),
        "beijing": (39.9042, 116.4074),
        "shanghai": (31.2304, 121.4737),
        "guangzhou": (23.1291, 113.2644),
        "shenzhen": (22.5431, 114.0579),
        "chengdu": (30.5728, 104.0668),
        "hangzhou": (30.2741, 120.1551),
        "nanjing": (32.0603, 118.7969),
        "wuhan": (30.5928, 114.3055),
        "xian": (34.3416, 108.9398),
        "hong kong": (22.3193, 114.1694),
        "taipei": (25.0330, 121.5654),
        "seoul": (37.5665, 126.9780),
        "busan": (35.1796, 129.0756),
        "incheon": (37.4563, 126.7052),
        "pyongyang": (39.0392, 125.7625),
        "mumbai": (19.0760, 72.8777),
        "delhi": (28.6139, 77.2090),
        "new delhi": (28.6139, 77.2090),
        "kolkata": (22.5726, 88.3639),
        "chennai": (13.0827, 80.2707),
        "bangalore": (12.9716, 77.5946),
        "hyderabad": (17.3850, 78.4867),
        "pune": (18.5204, 73.8567),
        "jaipur": (26.9124, 75.7873),
        "bangkok": (13.7563, 100.5018),
        "chiang mai": (18.7883, 98.9853),
        "singapore": (1.3521, 103.8198),
        "jakarta": (-6.2088, 106.8456),
        "bali": (-8.3405, 115.0920),
        "manila": (14.5995, 120.9842),
        "ho chi minh city": (10.8231, 106.6297),
        "hanoi": (21.0278, 105.8342),
        "kuala lumpur": (3.1390, 101.6869),
        "phnom penh": (11.5564, 104.9282),
        "yangon": (16.8661, 96.1951),
        # ── East & Southeast Asia ──
        "sydney": (-33.8688, 151.2093),
        "melbourne": (-37.8136, 144.9631),
        "brisbane": (-27.4698, 153.0251),
        "perth": (-31.9505, 115.8605),
        "adelaide": (-34.9285, 138.6007),
        "auckland": (-36.8485, 174.7633),
        "wellington": (-41.2866, 174.7756),
        "christchurch": (-43.5321, 172.6362),
        # ── Latin America ──
        "mexico city": (19.4326, -99.1332),
        "guadalajara": (20.6597, -103.3496),
        "monterrey": (25.6866, -100.3161),
        "cancun": (21.1619, -86.8515),
        "tivat": (21.1619, -86.8515),
        "bogota": (4.7110, -74.0721),
        "medellin": (6.2442, -75.5812),
        "buenos aires": (-34.6037, -58.3816),
        "cordoba": (-31.4201, -64.1888),
        "santiago": (-33.4489, -70.6693),
        "valparaiso": (-33.0472, -71.6127),
        "lima": (-12.0464, -77.0428),
        "cusco": (-13.5320, -71.9675),
        "sao paulo": (-23.5505, -46.6333),
        "rio de janeiro": (-22.9068, -43.1729),
        "brasilia": (-15.7975, -47.8919),
        "salvador": (-12.9714, -38.5124),
        "recife": (-8.0476, -34.8770),
        "caracas": (10.4806, -66.9036),
        "havana": (23.1136, -82.3666),
        "quito": (-0.1807, -78.4678),
        "la paz": (-16.4897, -68.1193),
        "montevideo": (-34.9011, -56.1645),
        "asuncion": (-25.2637, -57.5759),
        # ── Africa ──
        "cairo": (30.0444, 31.2357),
        "alexandria": (31.2001, 29.9187),
        "lagos": (6.5244, 3.3792),
        "abuja": (9.0579, 7.4951),
        "nairobi": (-1.2921, 36.8219),
        "mombasa": (-4.0435, 39.6669),
        "johannesburg": (-26.2041, 28.0473),
        "cape town": (-33.9249, 18.4241),
        "durban": (-29.8587, 31.0218),
        "pretoria": (-25.7479, 28.2293),
        "casablanca": (33.5731, -7.5898),
        "marrakech": (31.6295, -7.9811),
        "tangier": (35.7595, -5.8340),
        "accra": (5.6037, -0.1870),
        "addis ababa": (9.0250, 38.7469),
        "dar es salaam": (-6.7924, 39.2083),
        "kampala": (0.3476, 32.5825),
        "kigali": (-1.9403, 29.8735),
        "maputo": (-25.9692, 32.5732),
        "algiers": (36.7538, 3.0588),
        "tunis": (36.8065, 10.1815),
        "dakar": (14.7167, -17.4677),
        "kinshasa": (-4.4419, 15.2663),
        "harare": (-17.8252, 31.0335),
        "lusaka": (-15.3875, 28.3228),
        # ── South/Central Asia ──
        "dhaka": (23.8103, 90.4125),
        "kathmandu": (27.7172, 85.3240),
        "karachi": (24.8607, 67.0011),
        "lahore": (31.5204, 74.3589),
        "islamabad": (33.6844, 73.0479),
        "colombo": (6.9271, 79.8612),
        "kabul": (34.5553, 69.2075),
        "tientSin": (39.1422, 117.1767),
        "ulaanbaatar": (47.8864, 106.9052),
    }
    result = CITIES.get(city.lower())
    if result:
        return result[0], result[1], True
    print(f"  WARNING: city '{city}' not in fallback table — defaulting to 0°N 0°E. Use --lat/--lon for accuracy.",
          file=sys.stderr)
    return (0.0, 0.0, False)

# ---------------------------------------------------------------------------
# CORE CALCULATION ENGINE
# ---------------------------------------------------------------------------

def calc_planet_positions(jd, tropical=True):
    """Calculate all planetary positions. Returns dict of planet -> data."""
    if not SWE:
        return {}
    flags = swe.FLG_SPEED
    if not tropical:
        flags |= swe.FLG_SIDEREAL
        swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)

    positions = {}
    for name, pid in PLANETS.items():
        if name == "S.Node":
            continue
        if pid < 0:
            continue
        try:
            result, _ = swe.calc_ut(jd, pid, flags)
            lon = result[0]
            lat = result[1]
            speed = result[3]
            sign, sidx, deg, mins = deg_to_sign(lon)
            positions[name] = {
                "longitude": lon,
                "sign": sign,
                "sign_idx": sidx,
                "degree": deg,
                "minutes": mins,
                "latitude": lat,
                "speed": speed,
                "retrograde": speed < 0,
            }
        except Exception:
            pass

    # South Node = opposite of North Node
    if "N.Node" in positions:
        nn = positions["N.Node"]["longitude"]
        sn_lon = (nn + 180) % 360
        sign, sidx, deg, mins = deg_to_sign(sn_lon)
        positions["S.Node"] = {
            "longitude": sn_lon,
            "sign": sign, "sign_idx": sidx,
            "degree": deg, "minutes": mins,
            "latitude": 0, "speed": -positions["N.Node"]["speed"],
            "retrograde": True,
        }

    return positions

def calc_houses(jd, lat, lon, system=b"P"):
    """Calculate house cusps using Placidus (default). Returns list of 12 cusp longitudes."""
    if not SWE:
        return [i * 30.0 for i in range(12)], 0.0, 0.0
    try:
        cusps, ascmc = swe.houses(jd, lat, lon, system)
        asc = ascmc[0]
        mc  = ascmc[1]
        return list(cusps), asc, mc  # 12 elements, index 0 = H1 cusp ... index 11 = H12 cusp
    except Exception:
        return [i * 30.0 for i in range(12)], 0.0, 0.0

def planet_house(planet_lon, cusps):
    """Determine which house a planet is in, given 12 cusp longitudes."""
    for i in range(12):
        cusp_start = cusps[i] % 360
        cusp_end = cusps[(i + 1) % 12] % 360
        lon = planet_lon % 360
        if cusp_start <= cusp_end:
            if cusp_start <= lon < cusp_end:
                return i + 1
        else:  # wraps 360
            if lon >= cusp_start or lon < cusp_end:
                return i + 1
    return 1

def calc_aspects(positions, luminaries=("Sun", "Moon")):
    """Return list of (p1, p2, aspect_name, orb, quality, glyph)."""
    planet_list = [p for p in positions if positions[p].get("longitude") is not None]
    results = []
    for i, p1 in enumerate(planet_list):
        for p2 in planet_list[i+1:]:
            lon1 = positions[p1]["longitude"]
            lon2 = positions[p2]["longitude"]
            diff = angle_diff(lon1, lon2)
            for asp_name, (angle, orb_lum, orb_other, glyph, quality) in ASPECTS.items():
                orb = orb_lum if (p1 in luminaries or p2 in luminaries) else orb_other
                actual_orb = abs(diff - angle)
                if actual_orb <= orb:
                    # Applying or separating
                    applying = (positions[p1]["speed"] - positions[p2]["speed"]) > 0
                    results.append((p1, p2, asp_name, round(actual_orb, 2), quality, glyph, applying))
    return sorted(results, key=lambda x: x[3])

def essential_dignity(planet, sign, degree):
    """Return dignity score and labels for a planet at a position."""
    labels = []
    score = 0

    if sign in DOMICILE.get(planet, []):
        labels.append("Domicile ★★★★★")
        score += 5
    elif sign in DETRIMENT.get(planet, []):
        labels.append("Detriment ✗✗")
        score -= 5

    if EXALTATION.get(planet) == sign:
        # Check for exact or near-exact exaltation degree (bonus +1 within 3°)
        ex_data = EXALTATION_DEG.get(planet)
        if ex_data and ex_data[0] == sign:
            deg_diff = abs(degree - ex_data[1])
            if deg_diff <= 1:
                labels.append(f"Exact Exaltation ★★★★★  (within {deg_diff:.0f}° of {ex_data[1]}° {sign})")
                score += 5
            elif deg_diff <= 3:
                labels.append(f"Exaltation ★★★★  (near exact: {deg_diff:.0f}° from {ex_data[1]}° {sign})")
                score += 4
            else:
                labels.append("Exaltation ★★★★")
                score += 4
        else:
            labels.append("Exaltation ★★★★")
            score += 4
    elif FALL.get(sign) == planet:
        labels.append("Fall ✗")
        score -= 4

    # Triplicity
    elem = ELEMENTS.get(sign, "")
    if elem in TRIPLICITY:
        trip = TRIPLICITY[elem]
        if planet in trip:
            idx = trip.index(planet)
            label = ["Triplicity Day ★★★", "Triplicity Night ★★★", "Triplicity Part ★"][idx]
            labels.append(label)
            score += 3

    # Terms (Egyptian)
    for term_planet, start, end in TERMS.get(sign, []):
        if start <= degree < end and term_planet == planet:
            labels.append(f"Terms ★★  ({start}°–{end}°)")
            score += 2
            break

    # Decan/Face
    for face_planet, start in DECANS.get(sign, []):
        end = start + 10
        if start <= degree < end and face_planet == planet:
            labels.append(f"Face/Decan ★  ({start}°–{end-1}°)")
            score += 1
            break

    if not labels:
        labels.append("Peregrine — no essential dignity")

    return score, labels

def mutual_reception(positions):
    """Find planets in each other's domicile (mutual reception)."""
    found = []
    for p1, d1 in positions.items():
        for p2, d2 in positions.items():
            if p1 >= p2:
                continue
            sign1 = d1.get("sign")
            sign2 = d2.get("sign")
            if sign1 in DOMICILE.get(p2, []) and sign2 in DOMICILE.get(p1, []):
                found.append((p1, p2, sign1, sign2))
    return found

def calc_antiscia(positions):
    """Antiscia: mirror across the Cancer/Capricorn axis (0° Cancer = 0° Cancer).
    Contra-antiscia: mirror across 0° Aries / 0° Libra."""
    results = {}
    for p, d in positions.items():
        lon = d.get("longitude")
        if lon is None:
            continue
        # Antiscia axis: 0 Cancer (90°) and 0 Capricorn (270°)
        # antiscia longitude = 180 - lon (mod 360)  ... standard formula
        antiscia_lon = (180 - lon) % 360
        # Contra-antiscia axis: 0 Aries / 0 Libra
        contra_lon = (360 - lon) % 360

        a_sign, _, a_deg, a_min = deg_to_sign(antiscia_lon)
        c_sign, _, c_deg, c_min = deg_to_sign(contra_lon)
        results[p] = {
            "antiscia_lon": antiscia_lon,
            "antiscia": f"{a_sign} {a_deg}°{a_min:02d}'",
            "contra_lon": contra_lon,
            "contra": f"{c_sign} {c_deg}°{c_min:02d}'",
        }
    return results

def is_day_chart(sun_lon, asc_lon):
    """Sun above horizon = day chart (Sun between Asc and Desc going via top)."""
    # Sun is in day if its longitude is within 180° of ASC going counter-clockwise (above horizon)
    diff = (sun_lon - asc_lon) % 360
    return diff <= 180

def calc_lots(positions, asc_lon, day_chart):
    """Calculate Arabic Lots. Returns dict of lot_name -> longitude."""
    lots = {}
    fortune_lon = None

    def lot(from_p, to_p):
        try:
            f = positions[from_p]["longitude"]
            t = positions[to_p]["longitude"]
            if day_chart:
                return (asc_lon + t - f) % 360
            else:
                return (asc_lon + f - t) % 360
        except KeyError:
            return None

    # Fortune
    fl = lot("Moon", "Sun")
    if fl is not None:
        lots["Lot of Fortune"] = fl
        fortune_lon = fl

    # Spirit
    sl = lot("Sun", "Moon")
    if sl is not None:
        lots["Lot of Spirit"] = sl

    # Use computed Fortune for remaining lots
    if fortune_lon is not None and "Lot of Spirit" in lots:
        spirit_lon = lots["Lot of Spirit"]

        # Eros: ASC + Venus - Spirit (day) / ASC + Spirit - Venus (night)
        if "Venus" in positions:
            v = positions["Venus"]["longitude"]
            if day_chart:
                lots["Lot of Eros"] = (asc_lon + v - spirit_lon) % 360
            else:
                lots["Lot of Eros"] = (asc_lon + spirit_lon - v) % 360

        # Necessity: ASC + Fortune - Mercury (day) / reverse
        if "Mercury" in positions:
            merc = positions["Mercury"]["longitude"]
            if day_chart:
                lots["Lot of Necessity"] = (asc_lon + fortune_lon - merc) % 360
            else:
                lots["Lot of Necessity"] = (asc_lon + merc - fortune_lon) % 360

        # Courage: ASC + Mars - Fortune
        if "Mars" in positions:
            m = positions["Mars"]["longitude"]
            if day_chart:
                lots["Lot of Courage"] = (asc_lon + m - fortune_lon) % 360
            else:
                lots["Lot of Courage"] = (asc_lon + fortune_lon - m) % 360

        # Victory: ASC + Jupiter - Spirit
        if "Jupiter" in positions:
            j = positions["Jupiter"]["longitude"]
            if day_chart:
                lots["Lot of Victory"] = (asc_lon + j - spirit_lon) % 360
            else:
                lots["Lot of Victory"] = (asc_lon + spirit_lon - j) % 360

        # Nemesis: ASC + Saturn - Fortune
        if "Saturn" in positions:
            s = positions["Saturn"]["longitude"]
            if day_chart:
                lots["Lot of Nemesis"] = (asc_lon + s - fortune_lon) % 360
            else:
                lots["Lot of Nemesis"] = (asc_lon + fortune_lon - s) % 360

    return lots

def calc_lunar_phase(sun_lon, moon_lon):
    """Return lunar phase name and percentage illuminated."""
    diff = (moon_lon - sun_lon) % 360
    pct = diff / 360.0
    phases = [
        (0,   22.5,  "New Moon",         "🌑"),
        (22.5, 67.5, "Waxing Crescent",  "🌒"),
        (67.5, 112.5,"First Quarter",    "🌓"),
        (112.5,157.5,"Waxing Gibbous",   "🌔"),
        (157.5,202.5,"Full Moon",        "🌕"),
        (202.5,247.5,"Waning Gibbous",   "🌖"),
        (247.5,292.5,"Last Quarter",     "🌗"),
        (292.5,337.5,"Waning Crescent",  "🌘"),
        (337.5,360,  "Balsamic",         "🌑"),
    ]
    for start, end, name, glyph in phases:
        if start <= diff < end:
            illumination = round(50 * (1 - math.cos(math.radians(diff))))
            return name, glyph, diff, illumination
    return "Dark Moon", "🌑", diff, 0

def next_lunation(jd_start):
    """Find next New Moon and Full Moon from jd_start."""
    if not SWE:
        return None, None
    results = []
    for phase_type in [0, 2]:  # 0=New Moon, 2=Full Moon
        try:
            ret, jd_out = swe.mooncross_ut(phase_type, jd_start, swe.FLG_SWIEPH)
            if ret >= 0:
                results.append(jd_out)
            else:
                results.append(None)
        except Exception:
            results.append(None)
    return results[0], results[1]

def void_of_course(jd, moon_lon, positions):
    """Check if Moon is void of course — no applying major aspects before sign ingress.

    Uses exact aspect targeting: for each planet, compute the Moon longitude that would
    form an exact major aspect, then check if that longitude lies between now and ingress.
    Far more accurate and fast compared to step-scanning.
    """
    moon_sign_idx = int(moon_lon // 30)
    moon_sign_end = (moon_sign_idx + 1) * 30.0   # next sign boundary (tropical lon)
    moon_speed = positions.get("Moon", {}).get("speed", 13.2)
    degrees_to_ingress = (moon_sign_end - moon_lon) % 30
    hours_to_ingress = (degrees_to_ingress / moon_speed) * 24 if moon_speed > 0.01 else 999

    # Only check major aspects for VOC (classical definition)
    MAJOR_ASPECTS = {k: v for k, v in ASPECTS.items()
                     if k in ("Conjunction", "Opposition", "Trine", "Square", "Sextile")}

    next_aspect = None  # (planet, aspect_name, moon_lon_at_exact, orb_now)

    for pname, pdata in positions.items():
        if pname in ("Moon", "S.Node"):
            continue
        plon = pdata.get("longitude")
        if plon is None:
            continue
        pspeed = pdata.get("speed", 0.0)

        for asp_name, (angle, orb_l, orb_o, glyph, quality) in MAJOR_ASPECTS.items():
            # Target Moon longitude for exact aspect (two solutions per aspect type)
            for target_moon in [(plon + angle) % 360, (plon - angle) % 360]:
                # Is this target between moon_lon and moon_sign_end (going forward)?
                if moon_speed > 0:
                    # Forward motion: moon_lon → moon_sign_end
                    if moon_lon <= target_moon < moon_sign_end:
                        degrees_away = target_moon - moon_lon
                    elif moon_sign_end <= 360 and target_moon < moon_lon:
                        # wraps — not in this sign window
                        continue
                    else:
                        continue
                else:
                    continue  # retrograde Moon is extremely rare; skip

                # Confirm aspect is applying (Moon gaining on aspect point)
                # Moon is applying if current orb is decreasing:
                # relative speed of Moon vs planet in this aspect
                current_diff = angle_diff(moon_lon, plon)
                current_orb = abs(current_diff - angle)
                # planet will also move; approximate future planet lon
                hours_to_exact = (degrees_away / moon_speed) * 24 if moon_speed > 0 else 999
                future_plon = (plon + pspeed * hours_to_exact / 24) % 360
                future_diff = angle_diff(target_moon, future_plon)
                future_orb = abs(future_diff - angle)

                if future_orb < current_orb + 2:  # aspect is actually applying / within range
                    if next_aspect is None or degrees_away < next_aspect[3]:
                        next_aspect = (pname, asp_name, glyph, degrees_away, hours_to_exact)
                    return False, hours_to_ingress  # not VOC — found an applying aspect

    return True, hours_to_ingress

def planetary_hours(date, lat, lon):
    """Calculate planetary hours for a given date and location."""
    if not SWE:
        return []
    jd = julian_day(date.year, date.month, date.day, 12.0)
    # Get sunrise and sunset
    try:
        ret, sunrise = swe.rise_trans(jd - 0.5, swe.SUN, "", swe.CALC_RISE,
                                       lat, lon, 0, swe.CALC_DISC_UPPER_LIMB)
        ret2, sunset = swe.rise_trans(jd - 0.5, swe.SUN, "", swe.CALC_SET,
                                       lat, lon, 0, swe.CALC_DISC_UPPER_LIMB)
    except Exception:
        # Fallback: approximate 6am sunrise, 6pm sunset
        base = julian_day(date.year, date.month, date.day, 0)
        sunrise = [0, base + 6/24]
        sunset  = [0, base + 18/24]

    sunrise_jd = sunrise[1] if isinstance(sunrise, (list, tuple)) else sunrise
    sunset_jd  = sunset[1]  if isinstance(sunset,  (list, tuple)) else sunset

    # Next sunrise
    try:
        ret3, next_sunrise = swe.rise_trans(jd + 0.5, swe.SUN, "", swe.CALC_RISE,
                                             lat, lon, 0, swe.CALC_DISC_UPPER_LIMB)
        next_sunrise_jd = next_sunrise[1] if isinstance(next_sunrise, (list, tuple)) else next_sunrise
    except Exception:
        next_sunrise_jd = sunrise_jd + 1.0

    day_len  = (sunset_jd - sunrise_jd) / 12.0   # length of one day planetary hour
    night_len = (next_sunrise_jd - sunset_jd) / 12.0  # one night hour

    weekday = date.weekday()  # 0=Mon
    day_ruler = DAY_RULERS[weekday]
    ruler_idx = CHALDEAN.index(day_ruler)

    hours = []
    for i in range(12):
        hour_start = sunrise_jd + i * day_len
        planet = CHALDEAN[(ruler_idx + i) % 7]
        start_dt = swe.jdut1_to_utc(hour_start, 0)  # (y,m,d,h,mi,s)
        hours.append(("day", i + 1, planet, hour_start, day_len * 24 * 60))

    night_ruler_idx = (ruler_idx + 12) % 7
    for i in range(12):
        hour_start = sunset_jd + i * night_len
        planet = CHALDEAN[(night_ruler_idx + i) % 7]
        hours.append(("night", i + 1, planet, hour_start, night_len * 24 * 60))

    return hours, day_ruler, sunrise_jd, sunset_jd

def jd_to_dt(jd):
    """Convert Julian day to datetime string."""
    if SWE:
        try:
            y, m, d, h = swe.jdut1_to_utc(jd, 0)[:4]
            dt = datetime.datetime(int(y), int(m), int(d))
            hour = int(h)
            minute = int((h - hour) * 60)
            return dt.strftime(f"%Y-%m-%d") + f" {hour:02d}:{minute:02d} UTC"
        except Exception:
            pass
    return f"JD {jd:.4f}"

# ---------------------------------------------------------------------------
# COMPOSITE / SYNERGY / PREDICTION / GEOASTROLOGY ENGINE
# ---------------------------------------------------------------------------

def calc_composite(pos1, pos2):
    """Composite chart by midpoint method. Both charts must have same planet set."""
    composite = {}
    for planet in set(pos1.keys()) & set(pos2.keys()):
        lon1 = pos1[planet]["longitude"]
        lon2 = pos2[planet]["longitude"]
        # Shorter-arc midpoint
        diff = (lon2 - lon1) % 360
        mid = (lon1 + (diff / 2)) % 360 if diff <= 180 else (lon1 + (diff / 2) + 180) % 360
        sign, sidx, deg, mins = deg_to_sign(mid)
        composite[planet] = {
            "longitude": mid, "sign": sign, "sign_idx": sidx,
            "degree": deg, "minutes": mins,
            "latitude": 0.0, "speed": 0.0, "retrograde": False,
        }
    return composite

def calc_davison(jd1, jd2, lat1, lon1, lat2, lon2):
    """Davison relationship chart: average JD and average location."""
    jd_avg  = (jd1 + jd2) / 2.0
    lat_avg = (lat1 + lat2) / 2.0
    lon_avg = (lon1 + lon2) / 2.0
    return jd_avg, lat_avg, lon_avg

def calc_midpoints(positions):
    """Return all planet-pair midpoints sorted by longitude."""
    mps = []
    planet_list = sorted(positions.keys())
    for i, p1 in enumerate(planet_list):
        for p2 in planet_list[i+1:]:
            lon1 = positions[p1]["longitude"]
            lon2 = positions[p2]["longitude"]
            diff = (lon2 - lon1) % 360
            mid = (lon1 + diff / 2) % 360 if diff <= 180 else (lon1 + diff / 2 + 180) % 360
            sign, sidx, deg, mins = deg_to_sign(mid)
            mps.append((mid, p1, p2, sign, deg, mins))
    return sorted(mps)

def synergy_score(cross_aspects):
    """Score a list of (orb, p1, glyph, asp_name, p2, quality, applying) aspect rows."""
    WEIGHTS = {
        "Conjunction": 0,   # neutral — depends on planets
        "Trine":      +3,
        "Sextile":    +2,
        "Opposition": -1,   # awareness, not purely bad
        "Square":     -2,
        "Quincunx":   -1,
        "Semi-Square": -1,
        "Sesquisquare":-1,
    }
    PLANET_WEIGHTS = {
        "Sun":     3, "Moon":   3, "Venus": 2, "Mars": 2,
        "Mercury": 1, "Jupiter":2, "Saturn":1, "Chiron":1,
        "N.Node":  1, "Uranus": 1, "Neptune":1, "Pluto": 1,
    }
    categories = {"harmony": 0, "challenge": 0, "activation": 0, "neutral": 0}
    total = 0
    for row in cross_aspects:
        orb, p1, glyph, asp_name, p2, quality, applying = row
        w_asp = WEIGHTS.get(asp_name, 0)
        w_p   = (PLANET_WEIGHTS.get(p1, 1) + PLANET_WEIGHTS.get(p2, 1)) / 2
        tightness = max(0.1, 1 - orb / 10)  # closer = stronger
        score = w_asp * w_p * tightness

        # Conjunction: sign depends on planets involved
        if asp_name == "Conjunction":
            difficult_pair = {"Mars","Saturn","Pluto","Uranus","Neptune"}
            if p1 in difficult_pair or p2 in difficult_pair:
                score = -1 * w_p * tightness
            else:
                score = +2 * w_p * tightness

        if score > 0:
            categories["harmony"] += score
        elif score < 0:
            categories["challenge"] += abs(score)
        else:
            categories["neutral"] += 1
        total += score

    return total, categories

def find_exact_transit_dates(natal_pos, start_jd, end_jd, t_planets=None, n_planets=None, step=1.0):
    """Scan a date range for exact transit-to-natal major aspect dates.

    Returns list of (jd_exact, t_planet, asp_name, glyph, n_planet, quality).
    Uses bisection to find crossing to within 0.01° accuracy.
    """
    if not SWE:
        return []
    if t_planets is None:
        t_planets = ["Sun","Moon","Mercury","Venus","Mars",
                     "Jupiter","Saturn","Uranus","Neptune","Pluto","N.Node"]
    if n_planets is None:
        n_planets = ["Sun","Moon","Mercury","Venus","Mars","Asc","MC",
                     "Jupiter","Saturn","Chiron","N.Node"]

    MAJOR = {k: v for k, v in ASPECTS.items()
             if k in ("Conjunction","Opposition","Trine","Square","Sextile")}

    events = []

    for t_planet in t_planets:
        if t_planet not in PLANETS:
            continue
        pid = PLANETS[t_planet]

        for n_planet in n_planets:
            if n_planet not in natal_pos:
                continue
            n_lon = natal_pos[n_planet]["longitude"]

            for asp_name, (angle, orb_l, orb_o, glyph, quality) in MAJOR.items():
                # Two target longitudes (aspect from both sides)
                for target_lon in [(n_lon + angle) % 360, (n_lon - angle) % 360]:
                    jd = start_jd
                    try:
                        prev_lon = swe.calc_ut(jd, pid, swe.FLG_SPEED)[0][0]
                    except Exception:
                        continue

                    while jd < end_jd:
                        jd_next = min(jd + step, end_jd)
                        try:
                            curr_lon = swe.calc_ut(jd_next, pid, swe.FLG_SPEED)[0][0]
                        except Exception:
                            jd = jd_next
                            continue

                        # Check if transit planet crossed target_lon in this step
                        def dist_to_target(lon):
                            d = (lon - target_lon) % 360
                            return d if d <= 180 else d - 360

                        d_prev = dist_to_target(prev_lon)
                        d_curr = dist_to_target(curr_lon)

                        if d_prev * d_curr < 0 and abs(d_prev - d_curr) < 90:
                            # Sign change — bisect to find exact crossing
                            lo, hi = jd, jd_next
                            for _ in range(20):
                                mid_jd = (lo + hi) / 2
                                try:
                                    mid_lon = swe.calc_ut(mid_jd, pid, swe.FLG_SPEED)[0][0]
                                except Exception:
                                    break
                                if dist_to_target(mid_lon) * d_prev < 0:
                                    hi = mid_jd
                                else:
                                    lo = mid_jd
                            # Deduplicate: skip if same planet/aspect/natal combo within 5 days
                            duplicate = any(
                                abs(e[0] - (lo + hi) / 2) < 5
                                and e[1] == t_planet and e[2] == asp_name and e[3] == n_planet
                                for e in events
                            )
                            if not duplicate:
                                events.append(((lo + hi) / 2, t_planet, asp_name, glyph, n_planet, quality))

                        prev_lon = curr_lon
                        jd = jd_next

    return sorted(events)

def find_stations(start_jd, end_jd, step=1.0):
    """Find retrograde and direct station dates for all planets."""
    if not SWE:
        return []
    planets_to_check = ["Mercury","Venus","Mars","Jupiter","Saturn",
                        "Uranus","Neptune","Pluto","Chiron"]
    stations = []

    for planet in planets_to_check:
        pid = PLANETS[planet]
        jd = start_jd
        try:
            prev_speed = swe.calc_ut(jd, pid, swe.FLG_SPEED)[0][3]
        except Exception:
            continue

        while jd < end_jd:
            jd_next = min(jd + step, end_jd)
            try:
                curr = swe.calc_ut(jd_next, pid, swe.FLG_SPEED)[0]
                curr_speed = curr[3]
                curr_lon   = curr[0]
            except Exception:
                jd = jd_next
                continue

            if prev_speed * curr_speed < 0:
                # Speed sign change — bisect for exact station
                lo, hi = jd, jd_next
                for _ in range(20):
                    mid_jd = (lo + hi) / 2
                    try:
                        mid_spd = swe.calc_ut(mid_jd, pid, swe.FLG_SPEED)[0][3]
                    except Exception:
                        break
                    if mid_spd * prev_speed < 0:
                        hi = mid_jd
                    else:
                        lo = mid_jd
                exact_jd = (lo + hi) / 2
                try:
                    exact_lon = swe.calc_ut(exact_jd, pid, swe.FLG_SPEED)[0][0]
                except Exception:
                    exact_lon = curr_lon
                sign, sidx, deg, mins = deg_to_sign(exact_lon)
                kind = "Stations Retrograde ℞" if curr_speed < 0 else "Stations Direct  ℗"
                stations.append((exact_jd, planet, kind, sign, deg, mins))

            prev_speed = curr_speed
            jd = jd_next

    return sorted(stations)

def find_ingresses(start_jd, end_jd, planets=None, step=1.0):
    """Find sign ingresses for a list of planets."""
    if not SWE:
        return []
    if planets is None:
        planets = ["Sun","Mercury","Venus","Mars","Jupiter","Saturn",
                   "Uranus","Neptune","Pluto","N.Node"]
    ingresses = []

    for planet in planets:
        if planet not in PLANETS or PLANETS[planet] < 0:
            continue
        pid = PLANETS[planet]
        jd = start_jd
        try:
            prev_sign_idx = int(swe.calc_ut(jd, pid, swe.FLG_SPEED)[0][0] // 30) % 12
        except Exception:
            continue

        while jd < end_jd:
            jd_next = min(jd + step, end_jd)
            try:
                curr_lon = swe.calc_ut(jd_next, pid, swe.FLG_SPEED)[0][0]
                curr_sign_idx = int(curr_lon // 30) % 12
            except Exception:
                jd = jd_next
                continue

            if curr_sign_idx != prev_sign_idx:
                # Bisect to exact ingress
                lo, hi = jd, jd_next
                for _ in range(20):
                    mid_jd = (lo + hi) / 2
                    try:
                        mid_idx = int(swe.calc_ut(mid_jd, pid, swe.FLG_SPEED)[0][0] // 30) % 12
                    except Exception:
                        break
                    if mid_idx == prev_sign_idx:
                        lo = mid_jd
                    else:
                        hi = mid_jd
                ingresses.append(((lo + hi) / 2, planet,
                                   SIGNS[prev_sign_idx], SIGNS[curr_sign_idx]))
                prev_sign_idx = curr_sign_idx

            jd = jd_next

    return sorted(ingresses)

def find_eclipses(start_jd, end_jd):
    """Find solar and lunar eclipses using Swiss Ephemeris."""
    if not SWE:
        return []
    eclipses = []
    jd = start_jd

    while jd < end_jd:
        # Solar eclipse search
        try:
            ret, jd_sol = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0, False)
            if ret >= 0 and jd_sol[0] < end_jd:
                eclipse_type = {
                    swe.ECL_TOTAL:   "Total Solar Eclipse",
                    swe.ECL_ANNULAR: "Annular Solar Eclipse",
                    swe.ECL_PARTIAL: "Partial Solar Eclipse",
                    swe.ECL_ANNULAR_TOTAL: "Hybrid Solar Eclipse",
                }.get(ret & 0xFF, "Solar Eclipse")
                sun_lon = swe.calc_ut(jd_sol[0], swe.SUN, swe.FLG_SPEED)[0][0]
                sign, sidx, deg, mins = deg_to_sign(sun_lon)
                eclipses.append((jd_sol[0], eclipse_type, sign, deg, mins))
                jd = jd_sol[0] + 20  # skip past this eclipse
                continue
        except Exception:
            pass

        # Lunar eclipse search
        try:
            ret, jd_lun = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0, False)
            if ret >= 0 and jd_lun[0] < end_jd:
                eclipse_type = {
                    swe.ECL_TOTAL:    "Total Lunar Eclipse",
                    swe.ECL_PARTIAL:  "Partial Lunar Eclipse",
                    swe.ECL_PENUMBRAL:"Penumbral Lunar Eclipse",
                }.get(ret & 0xFF, "Lunar Eclipse")
                moon_lon = swe.calc_ut(jd_lun[0], swe.MOON, swe.FLG_SPEED)[0][0]
                sign, sidx, deg, mins = deg_to_sign(moon_lon)
                eclipses.append((jd_lun[0], eclipse_type, sign, deg, mins))
                jd = jd_lun[0] + 14
                continue
        except Exception:
            pass

        jd += 25  # jump roughly one lunation

    return sorted(eclipses)

def _obliquity(jd):
    """Return mean obliquity of ecliptic in degrees."""
    if SWE:
        try:
            return swe.calc_ut(jd, swe.ECL_NUT, 0)[0][0]
        except Exception:
            pass
    # IAU formula fallback
    T = (jd - 2451545.0) / 36525.0
    return 23.439291 - 0.013004 * T

def _ecl_to_eq(lon, lat, eps):
    """Convert ecliptic (lon, lat) to equatorial (RA, Dec) in degrees."""
    eps_r = math.radians(eps)
    lon_r = math.radians(lon)
    lat_r = math.radians(lat)
    dec = math.asin(math.sin(lat_r) * math.cos(eps_r) +
                    math.cos(lat_r) * math.sin(eps_r) * math.sin(lon_r))
    ra  = math.atan2(
        math.sin(lon_r) * math.cos(eps_r) - math.tan(lat_r) * math.sin(eps_r),
        math.cos(lon_r)
    )
    return math.degrees(ra) % 360, math.degrees(dec)

def _gmst(jd):
    """Greenwich Mean Sidereal Time in degrees."""
    if SWE:
        try:
            return swe.sidtime(jd) * 15.0  # hours -> degrees
        except Exception:
            pass
    T = (jd - 2451545.0) / 36525.0
    gmst_hours = 6.697374558 + 2400.0513369 * T + 0.0000258622 * T * T
    return (gmst_hours % 24) * 15.0

def calc_astrocartography(jd, positions):
    """Calculate astrocartography lines for all major planets.

    Returns dict of planet -> {
        "MC_lon": float,   # Earth longitude of MC line (planet on upper meridian)
        "IC_lon": float,   # Earth longitude of IC line
        "ASC_lons": [(lat, lon), ...],  # ASC line sampled every 10° of latitude
        "DSC_lons": [(lat, lon), ...],  # DSC line
        "ra": float, "dec": float,      # planet equatorial coords
    }
    """
    if not SWE:
        return {}

    eps = _obliquity(jd)
    gmst_deg = _gmst(jd)
    result = {}

    for planet, pid in PLANETS.items():
        if planet in ("S.Node",) or pid < 0:
            continue
        if planet not in positions:
            continue
        pdata = positions[planet]
        ecl_lon = pdata["longitude"]
        ecl_lat = pdata.get("latitude", 0.0)

        ra, dec = _ecl_to_eq(ecl_lon, ecl_lat, eps)

        # MC line: longitude on Earth where planet is on upper meridian
        # Local Sidereal Time = GMST + geographic_lon  →  geographic_lon = RA - GMST
        mc_earth_lon = (ra - gmst_deg) % 360
        if mc_earth_lon > 180:
            mc_earth_lon -= 360  # convert to -180..+180
        ic_earth_lon = mc_earth_lon + 180
        if ic_earth_lon > 180:
            ic_earth_lon -= 360

        # ASC/DSC lines: for each latitude, find the hour angle H where planet is on horizon
        # cos(H) = -tan(φ) * tan(δ)  → horizon condition
        asc_line = []
        dsc_line = []
        dec_r = math.radians(dec)

        for lat_deg in range(-60, 65, 5):
            phi_r = math.radians(lat_deg)
            cos_H = -math.tan(phi_r) * math.tan(dec_r)
            if abs(cos_H) > 1:
                continue  # circumpolar — no rising/setting
            H = math.degrees(math.acos(cos_H))  # 0..180°

            # Rising (ASC): RAMC = RA - H  →  geo_lon = RAMC - GMST
            ramc_asc = (ra - H) % 360
            geo_lon_asc = (ramc_asc - gmst_deg) % 360
            if geo_lon_asc > 180:
                geo_lon_asc -= 360
            asc_line.append((lat_deg, round(geo_lon_asc, 2)))

            # Setting (DSC): RAMC = RA + H
            ramc_dsc = (ra + H) % 360
            geo_lon_dsc = (ramc_dsc - gmst_deg) % 360
            if geo_lon_dsc > 180:
                geo_lon_dsc -= 360
            dsc_line.append((lat_deg, round(geo_lon_dsc, 2)))

        result[planet] = {
            "MC_lon": round(mc_earth_lon, 2),
            "IC_lon": round(ic_earth_lon, 2),
            "ASC_lons": asc_line,
            "DSC_lons": dsc_line,
            "ra": round(ra, 3),
            "dec": round(dec, 3),
        }

    return result

# Geographic region lookup (rough longitude bands for astrocartography)
_GEO_REGIONS = [
    (-180,-150,"Pacific Ocean / International Date Line"),
    (-150,-130,"Hawaii / Pacific Ocean"),
    (-130,-110,"Pacific Coast / British Columbia / Baja"),
    (-110, -90,"US Mountain West / Mexico"),
    ( -90, -70,"US Central / Mississippi / Caribbean"),
    ( -70, -50,"US East Coast / Eastern Canada"),
    ( -50, -30,"Atlantic Ocean / Eastern Brazil"),
    ( -30, -10,"Mid-Atlantic / West Africa"),
    ( -10,  10,"Western Europe / Central Africa"),
    (  10,  30,"Central Europe / East Africa"),
    (  30,  50,"Eastern Europe / Middle East"),
    (  50,  70,"Central Asia / Persian Gulf"),
    (  70,  90,"South Asia / India"),
    (  90, 110,"Southeast Asia / China"),
    ( 110, 130,"East Asia / Philippines / Japan"),
    ( 130, 150,"Japan / Oceania / Eastern Australia"),
    ( 150, 180,"Western Pacific / Eastern Australia"),
]

def geo_region(lon):
    for lo, hi, name in _GEO_REGIONS:
        if lo <= lon < hi:
            return name
    return "Unknown region"

# ---------------------------------------------------------------------------
# OUTPUT FORMATTERS
# ---------------------------------------------------------------------------

def fmt_position(p_data):
    sign = p_data["sign"]
    deg  = p_data["degree"]
    mins = p_data["minutes"]
    rx   = " ℞" if p_data.get("retrograde") else ""
    sym  = SIGN_SYMBOL[p_data["sign_idx"]]
    return f"{sign} {sym} {deg:2d}°{mins:02d}'{rx}"

def print_planet_table(positions, cusps=None, title="PLANETARY POSITIONS"):
    section(title)
    print(f"  │  {'Planet':<12} {'Symbol':<3} {'Position':<24} {'House':>5}  {'Lat':>7}  {'Speed':>8}")
    print(f"  │  {'─'*12} {'─'*3} {'─'*24} {'─'*5}  {'─'*7}  {'─'*8}")
    for name in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                 "Uranus","Neptune","Pluto","Chiron","N.Node","S.Node",
                 "Ceres","Pallas","Juno","Vesta"]:
        if name not in positions:
            continue
        d = positions[name]
        sym = PLANET_SYMBOL.get(name, "?")
        pos = fmt_position(d)
        house = ""
        if cusps:
            h = planet_house(d["longitude"], cusps)
            house = f"H{h:2d}"
        lat = f"{d.get('latitude', 0.0):+.2f}°"
        spd = f"{d.get('speed', 0.0):+.4f}°/d"
        print(f"  │  {name:<12} {sym:<3} {pos:<24} {house:>5}  {lat:>7}  {spd:>8}")
    print()

def print_aspects(aspects, max_show=40):
    section("ASPECTS")
    print(f"  │  {'Planet 1':<12} {'Asp':<14} {'Glyph':<5} {'Planet 2':<12} {'Orb':>6}  {'Quality':<12} {'App/Sep'}")
    print(f"  │  {'─'*12} {'─'*14} {'─'*5} {'─'*12} {'─'*6}  {'─'*12} {'─'*8}")
    for a in aspects[:max_show]:
        p1, p2, asp, orb, quality, glyph, applying = a
        app = "Appl." if applying else "Sep."
        print(f"  │  {p1:<12} {asp:<14} {glyph:<5} {p2:<12} {orb:>5.2f}°  {quality:<12} {app}")
    if len(aspects) > max_show:
        print(f"  │  ... and {len(aspects) - max_show} more aspects")
    print()

def print_dignity_table(positions):
    section("ESSENTIAL DIGNITIES")
    print(f"  │  {'Planet':<12} {'Sign':<14} {'Score':>5}  Dignities")
    print(f"  │  {'─'*12} {'─'*14} {'─'*5}  {'─'*40}")
    for name in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]:
        if name not in positions:
            continue
        d = positions[name]
        score, labels = essential_dignity(name, d["sign"], d["degree"])
        score_str = f"{score:+d}"
        print(f"  │  {name:<12} {d['sign']:<14} {score_str:>5}  {labels[0]}")
        for lbl in labels[1:]:
            print(f"  │  {'':<12} {'':<14} {'':>5}  {lbl}")
    print()

def print_norse_layer(positions):
    section("NORSE MYTHIC CORRESPONDENCES")
    for name in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                 "Uranus","Neptune","Pluto","Chiron","N.Node"]:
        if name not in positions:
            continue
        d = positions[name]
        norse = NORSE_CORRESPONDENCES.get(name, "")
        sign = d["sign"]
        rune_name, rune_sym, rune_meaning = SIGN_RUNES.get(sign, ("?", "?", "?"))
        print(f"  │  {PLANET_SYMBOL.get(name,'?')} {name} in {sign} {SIGN_SYMBOL[d['sign_idx']]}")
        print(f"  │    Norse: {norse}")
        print(f"  │    Rune:  {rune_sym} {rune_name} — {rune_meaning}")
        print(f"  │    Wyrd note: {name} carries the energy of {norse.split('—')[0].strip()} through the realm of {rune_name}.")
        print()

def print_lots(lots_dict, cusps=None):
    section("ARABIC LOTS / HERMETIC PARTS")
    print(f"  │  {'Lot':<24} {'Position':<28} {'House':>5}")
    print(f"  │  {'─'*24} {'─'*28} {'─'*5}")
    lot_meanings = {
        "Lot of Fortune":   "Material circumstances, the body, luck in external affairs",
        "Lot of Spirit":    "Soul's intention, agency, inner life, the mind-will",
        "Lot of Eros":      "Desire, erotic love, what the soul longs for",
        "Lot of Necessity": "What compels us, obligations, fate's grip",
        "Lot of Courage":   "Daring, risk, the hero's threshold",
        "Lot of Victory":   "Success, where Jupiter's grace manifests",
        "Lot of Nemesis":   "Retribution, hidden enemies, Saturn's reckoning",
    }
    for name, lon in lots_dict.items():
        sign, sidx, deg, mins = deg_to_sign(lon)
        sym = SIGN_SYMBOL[sidx]
        pos = f"{sign} {sym} {deg:2d}°{mins:02d}'"
        house = ""
        if cusps:
            h = planet_house(lon, cusps)
            house = f"H{h:2d}"
        print(f"  │  {name:<24} {pos:<28} {house:>5}")
        meaning = lot_meanings.get(name, "")
        wrap_print(meaning, indent=7)
    print()

def print_antiscia(antiscia_dict):
    section("ANTISCIA & CONTRA-ANTISCIA")
    print(f"  │  {'Planet':<12} {'Antiscia':<24} {'Contra-Antiscia':<24}")
    print(f"  │  {'─'*12} {'─'*24} {'─'*24}")
    for name in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                 "Uranus","Neptune","Pluto"]:
        if name not in antiscia_dict:
            continue
        a = antiscia_dict[name]
        print(f"  │  {name:<12} {a['antiscia']:<24} {a['contra']:<24}")
    print()

def print_hellenistic(positions, cusps, asc_lon):
    section("HELLENISTIC ANALYSIS")

    # Sect
    sun_lon = positions.get("Sun", {}).get("longitude", 0)
    day = is_day_chart(sun_lon, asc_lon)
    sect_name = "Day Chart (Diurnal)" if day else "Night Chart (Nocturnal)"
    sect_light = "Sun" if day else "Moon"
    print(f"  │  Sect: {sect_name}")
    print(f"  │  Sect Light: {sect_light}")
    print()

    # Planetary joys
    print(f"  │  Planetary Joys:")
    for planet, house_num in sorted(PLANETARY_JOY.items(), key=lambda x: x[1]):
        if planet in positions and cusps:
            actual_house = planet_house(positions[planet]["longitude"], cusps)
            joy = "✦ IN JOY" if actual_house == house_num else f"(joy H{house_num}, in H{actual_house})"
        else:
            joy = f"(joy H{house_num})"
        print(f"  │    {planet:<12} rejoices in H{house_num}  {joy}")
    print()

    # Triplicity rulers for sect light sign
    sl_sign = positions.get(sect_light, {}).get("sign", "")
    elem = ELEMENTS.get(sl_sign, "")
    if elem in TRIPLICITY:
        day_r, night_r, part_r = TRIPLICITY[elem]
        print(f"  │  Triplicity Rulers of {sect_light} ({sl_sign} / {elem}):")
        print(f"  │    Day ruler:          {day_r}")
        print(f"  │    Night ruler:        {night_r}")
        print(f"  │    Participating:      {part_r}")
        active = day_r if day else night_r
        print(f"  │    Active sect ruler:  {active}")
    print()

    # Mutual receptions
    receps = mutual_reception(positions)
    if receps:
        print(f"  │  Mutual Receptions:")
        for p1, p2, s1, s2 in receps:
            print(f"  │    {p1} in {s1} ⇔ {p2} in {s2}")
    else:
        print(f"  │  Mutual Receptions: none")
    print()

    # Stelliums
    sign_counts = {}
    house_counts = {}
    for pname, pd in positions.items():
        if pname in ("S.Node","Ceres","Pallas","Juno","Vesta"):
            continue
        sg = pd.get("sign")
        if sg:
            sign_counts[sg] = sign_counts.get(sg, []) + [pname]
        if cusps:
            h = planet_house(pd["longitude"], cusps)
            house_counts[h] = house_counts.get(h, []) + [pname]

    stelliums = [(sg, ps) for sg, ps in sign_counts.items() if len(ps) >= 3]
    house_stelliums = [(h, ps) for h, ps in house_counts.items() if len(ps) >= 3]
    if stelliums:
        print(f"  │  Stelliums by Sign:")
        for sg, ps in stelliums:
            print(f"  │    {sg}: {', '.join(ps)}")
    if house_stelliums:
        print(f"  │  Stelliums by House:")
        for h, ps in house_stelliums:
            print(f"  │    House {h}: {', '.join(ps)}")
    print()

# ---------------------------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------------------------

def cmd_natal(args):
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, city_default_used = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd = julian_day(y, mo, d, utc_hour)
    name = args.name or "Seeker"

    # Determine display label for location
    loc_label = f"{args.city}, {args.nation}"
    if getattr(args, "lat", None) is not None and getattr(args, "lon", None) is not None:
        # When explicit coords are given, use them in the label
        lat_dir_co = 'N' if lat >= 0 else 'S'
        lon_dir_co = 'E' if lon >= 0 else 'W'
        if city_default_used:
            loc_label = f"{abs(lat):.4f}°{lat_dir_co} {abs(lon):.4f}°{lon_dir_co}"
        else:
            loc_label = f"{args.city}, {args.nation}  ·  {abs(lat):.4f}°{lat_dir_co} {abs(lon):.4f}°{lon_dir_co}"

    header(
        f"NATAL CHART — {name.upper()}",
        f"{args.date}  ·  {loc_label}"
    )
    print(f"  Time: {tz_label}")
    print(f"  {'*time unknown — houses/ASC approximate*' if not time_known else ''}")
    print()

    positions = calc_planet_positions(jd)
    cusps, asc, mc = calc_houses(jd, lat, lon)

    asc_sign, asidx, asc_deg, asc_min = deg_to_sign(asc)
    mc_sign,  msidx, mc_deg,  mc_min  = deg_to_sign(mc)

    print(f"  ASC (Rising): {asc_sign} {SIGN_SYMBOL[asidx]} {asc_deg}°{asc_min:02d}'")
    print(f"  MC  (Midheaven): {mc_sign} {SIGN_SYMBOL[msidx]} {mc_deg}°{mc_min:02d}'")
    sun_sign = positions.get("Sun", {}).get("sign", "?")
    moon_sign = positions.get("Moon", {}).get("sign", "?")
    print(f"  Sun: {sun_sign}  ·  Moon: {moon_sign}  ·  Rising: {asc_sign}")
    print()

    # Day/night
    sun_lon = positions.get("Sun", {}).get("longitude", 0)
    day = is_day_chart(sun_lon, asc)
    print(f"  Chart Type: {'Day (Diurnal)' if day else 'Night (Nocturnal)'}")
    print()

    print_planet_table(positions, cusps)
    print_aspects(calc_aspects(positions))
    print_dignity_table(positions)

    # Lots
    lots = calc_lots(positions, asc, day)
    print_lots(lots, cusps)

    # Antiscia
    print_antiscia(calc_antiscia(positions))

    # Hellenistic
    print_hellenistic(positions, cusps, asc)

    # Norse layer
    print_norse_layer(positions)

    # House meanings
    section("HOUSE OVERVIEW")
    for h_num, h_key in HOUSE_KEYWORDS:
        cusp_lon = cusps[h_num - 1]
        c_sign, csidx, c_deg, c_min = deg_to_sign(cusp_lon)
        sym = SIGN_SYMBOL[csidx]
        # Planets in this house
        in_house = [p for p, pd in positions.items()
                    if planet_house(pd["longitude"], cusps) == h_num
                    and p not in ("S.Node",)]
        in_str = f"  [{', '.join(in_house)}]" if in_house else ""
        print(f"  │  H{h_num:2d} {c_sign} {sym} {c_deg:2d}°  {h_key}{in_str}")
    print()

    print(f"  {hr()}")
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    print(f"  Latitude: {abs(lat):.4f}°{lat_dir}  ·  Longitude: {abs(lon):.4f}°{lon_dir}  ·  JD: {jd:.4f}")


def cmd_transit(args):
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, _ = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd_natal = julian_day(y, mo, d, utc_hour)

    # Gap 2 fix: --transit-date overrides "now"
    transit_date_str = getattr(args, "transit_date", None)
    if transit_date_str:
        ty, tmo, td, thour = parse_date_time(transit_date_str,
                                              getattr(args, "transit_time", None))
        jd_sky = julian_day(ty, tmo, td, thour)
        ttime = getattr(args, "transit_time", None) or "12:00"
        sky_label = f"{transit_date_str} {ttime} UTC"
    else:
        now = datetime.datetime.utcnow()
        jd_sky = julian_day(now.year, now.month, now.day,
                             now.hour + now.minute / 60.0)
        sky_label = now.strftime("%Y-%m-%d %H:%M UTC")

    natal_pos   = calc_planet_positions(jd_natal)
    transit_pos = calc_planet_positions(jd_sky)
    cusps, asc, mc = calc_houses(jd_natal, lat, lon)

    header("TRANSIT CHART", f"Natal: {args.date}  ·  Sky: {sky_label}")

    print_planet_table(transit_pos, title=f"SKY POSITIONS  ({sky_label})")

    # Transiting planets in natal houses
    section("TRANSITING PLANETS IN NATAL HOUSES")
    print(f"  │  {'Planet':<12} {'Position':<24} {'Natal House':>12}  Natal house theme")
    print(f"  │  {'─'*12} {'─'*24} {'─'*12}  {'─'*30}")
    for t_name in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                   "Uranus","Neptune","Pluto","N.Node"]:
        if t_name not in transit_pos:
            continue
        t_data = transit_pos[t_name]
        h = planet_house(t_data["longitude"], cusps)
        _, kw = HOUSE_KEYWORDS[h - 1]
        print(f"  │  {t_name:<12} {fmt_position(t_data):<24} {'H'+str(h):>12}  {kw.split('·')[0].strip()}")
    print()

    # Transit-to-natal aspects
    section("TRANSIT-TO-NATAL ASPECTS")
    print(f"  │  {'Transit Planet':<14} {'Glyph+Aspect':<16} {'Natal Planet':<14} {'Orb':>6}  {'Quality':<12} App/Sep")
    print(f"  │  {'─'*14} {'─'*16} {'─'*14} {'─'*6}  {'─'*12} {'─'*6}")
    rows = []
    for t_name, t_data in transit_pos.items():
        if t_name in ("S.Node", "Ceres","Pallas","Juno","Vesta"):
            continue
        t_lon = t_data["longitude"]
        for n_name, n_data in natal_pos.items():
            if n_name in ("S.Node", "Ceres","Pallas","Juno","Vesta"):
                continue
            n_lon = n_data["longitude"]
            diff = angle_diff(t_lon, n_lon)
            for asp_name, (angle, orb_l, orb_o, glyph, quality) in ASPECTS.items():
                if asp_name in ("Quintile","Bi-Quintile","Septile","Semi-Sextile"):
                    continue
                orb = orb_l if t_name in ("Sun","Moon") or n_name in ("Sun","Moon") else orb_o
                actual_orb = abs(diff - angle)
                if actual_orb <= orb:
                    applying = (t_data["speed"] - n_data.get("speed", 0)) > 0
                    rows.append((actual_orb, t_name, glyph, asp_name, n_name, quality, applying))
    for actual_orb, t_name, glyph, asp_name, n_name, quality, applying in sorted(rows):
        app = "Appl." if applying else "Sep."
        print(f"  │  {t_name:<14} {glyph} {asp_name:<14} {n_name:<14} {actual_orb:>5.2f}°  {quality:<12} {app}")
    print()


def cmd_synastry(args):
    c1, n1a = getattr(args,"city1",None), getattr(args,"nation1",None)
    c2, n2a = getattr(args,"city2",None), getattr(args,"nation2",None)
    y1, mo1, d1, h1, lat1, lon1, tz1, tzl1, _, _ = resolve_birth(
        args.date1, getattr(args,"time1",None),
        c1 or "London", n1a or "GB",
        getattr(args,"lat1",None), getattr(args,"lon1",None)
    )
    y2, mo2, d2, h2, lat2, lon2, tz2, tzl2, _, _ = resolve_birth(
        args.date2, getattr(args,"time2",None),
        c2 or "London", n2a or "GB",
        getattr(args,"lat2",None), getattr(args,"lon2",None)
    )
    jd1 = julian_day(y1, mo1, d1, h1)
    jd2 = julian_day(y2, mo2, d2, h2)

    pos1 = calc_planet_positions(jd1)
    pos2 = calc_planet_positions(jd2)

    n1 = getattr(args, "name1", "Person A")
    n2 = getattr(args, "name2", "Person B")

    header("SYNASTRY CHART", f"{n1}  ×  {n2}")

    # Gap 6: house overlays — only available if birth location provided
    city1   = getattr(args, "city1",   None)
    nation1 = getattr(args, "nation1", None)
    city2   = getattr(args, "city2",   None)
    nation2 = getattr(args, "nation2", None)
    lat1 = getattr(args, "lat1", None)
    lon1 = getattr(args, "lon1", None)
    lat2 = getattr(args, "lat2", None)
    lon2 = getattr(args, "lon2", None)

    cusps1, asc1, mc1 = None, None, None
    cusps2, asc2, mc2 = None, None, None

    if city1 and nation1:
        _lat1, _lon1, _ = geocode_city(city1, nation1, lat1, lon1)
        cusps1, asc1, mc1 = calc_houses(jd1, _lat1, _lon1)
    elif lat1 and lon1:
        cusps1, asc1, mc1 = calc_houses(jd1, float(lat1), float(lon1))

    if city2 and nation2:
        _lat2, _lon2, _ = geocode_city(city2, nation2, lat2, lon2)
        cusps2, asc2, mc2 = calc_houses(jd2, _lat2, _lon2)
    elif lat2 and lon2:
        cusps2, asc2, mc2 = calc_houses(jd2, float(lat2), float(lon2))

    print_planet_table(pos1, cusps1, title=f"CHART 1 — {n1}")
    print_planet_table(pos2, cusps2, title=f"CHART 2 — {n2}")

    # House overlays
    if cusps1 and cusps2:
        section(f"HOUSE OVERLAYS — {n1}'s planets in {n2}'s houses")
        print(f"  │  {'Planet':<12} {'Position':<24} {n2+' House':>10}  Theme")
        print(f"  │  {'─'*12} {'─'*24} {'─'*10}  {'─'*30}")
        for pname in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                      "Uranus","Neptune","Pluto","Chiron","N.Node"]:
            if pname not in pos1:
                continue
            h = planet_house(pos1[pname]["longitude"], cusps2)
            _, kw = HOUSE_KEYWORDS[h - 1]
            print(f"  │  {pname:<12} {fmt_position(pos1[pname]):<24} {'H'+str(h):>10}  {kw.split('·')[0].strip()}")
        print()

        section(f"HOUSE OVERLAYS — {n2}'s planets in {n1}'s houses")
        print(f"  │  {'Planet':<12} {'Position':<24} {n1+' House':>10}  Theme")
        print(f"  │  {'─'*12} {'─'*24} {'─'*10}  {'─'*30}")
        for pname in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                      "Uranus","Neptune","Pluto","Chiron","N.Node"]:
            if pname not in pos2:
                continue
            h = planet_house(pos2[pname]["longitude"], cusps1)
            _, kw = HOUSE_KEYWORDS[h - 1]
            print(f"  │  {pname:<12} {fmt_position(pos2[pname]):<24} {'H'+str(h):>10}  {kw.split('·')[0].strip()}")
        print()
    else:
        print("  (Add --city1/--nation1 and --city2/--nation2 to enable house overlays)")
        print()

    # Cross-aspects
    section(f"CROSS-ASPECTS  {n1} → {n2}")
    print(f"  │  {n1+' Planet':<16} {'Asp':<16} {n2+' Planet':<16} {'Orb':>6}  {'Quality':<12} App/Sep")
    print(f"  │  {'─'*16} {'─'*16} {'─'*16} {'─'*6}  {'─'*12} {'─'*6}")

    rows = []
    for p1, d1_data in pos1.items():
        if p1 not in ("Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                       "Uranus","Neptune","Pluto","Chiron","N.Node"):
            continue
        for p2, d2_data in pos2.items():
            if p2 not in ("Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                           "Uranus","Neptune","Pluto","Chiron","N.Node"):
                continue
            diff = angle_diff(d1_data["longitude"], d2_data["longitude"])
            for asp_name, (angle, orb_l, orb_o, glyph, quality) in ASPECTS.items():
                if asp_name in ("Quintile","Bi-Quintile","Septile","Semi-Sextile"):
                    continue
                orb = orb_l if p1 in ("Sun","Moon") or p2 in ("Sun","Moon") else orb_o
                actual_orb = abs(diff - angle)
                if actual_orb <= orb:
                    applying = (d1_data["speed"] - d2_data.get("speed", 0)) > 0
                    rows.append((actual_orb, p1, glyph, asp_name, p2, quality, applying))
    for actual_orb, p1, glyph, asp_name, p2, quality, applying in sorted(rows):
        app = "Appl." if applying else "Sep."
        print(f"  │  {p1:<16} {glyph} {asp_name:<14} {p2:<16} {actual_orb:>5.2f}°  {quality:<12} {app}")
    print()


def cmd_solar_return(args):
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, _ = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd_natal = julian_day(y, mo, d, utc_hour)
    target_year = int(args.year) if hasattr(args, "year") and args.year else datetime.datetime.utcnow().year

    if not SWE:
        print("pyswisseph required for solar return calculation.")
        return

    # Find exact moment when Sun returns to natal Sun position
    natal_pos = calc_planet_positions(jd_natal)
    natal_sun_lon = natal_pos.get("Sun", {}).get("longitude", 0)

    # Start searching from ~March of target year
    jd_search = julian_day(target_year, mo - 1 if mo > 1 else 12, d, 0)
    # Refine with iterative approach
    for _ in range(50):
        pos = calc_planet_positions(jd_search)
        sun_lon = pos.get("Sun", {}).get("longitude", natal_sun_lon)
        diff = (natal_sun_lon - sun_lon) % 360
        if diff > 180:
            diff -= 360
        if abs(diff) < 0.001:
            break
        # Sun moves ~1 degree/day
        jd_search += diff / 360.0

    sr_pos = calc_planet_positions(jd_search)
    sr_cusps, sr_asc, sr_mc = calc_houses(jd_search, lat, lon)

    sr_dt = jd_to_dt(jd_search)
    header("SOLAR RETURN CHART", f"Year {target_year}  ·  {sr_dt}  ·  {args.city}, {args.nation}")
    print_planet_table(sr_pos, sr_cusps)
    print_aspects(calc_aspects(sr_pos))
    sr_asc_sign, saidx, sa_deg, sa_min = deg_to_sign(sr_asc)
    print(f"  SR ASC: {sr_asc_sign} {SIGN_SYMBOL[saidx]} {sa_deg}°{sa_min:02d}'")
    print()


def cmd_progressions(args):
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, _ = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd_natal = julian_day(y, mo, d, utc_hour)

    prog_date_str = args.prog_date if hasattr(args, "prog_date") and args.prog_date \
        else datetime.datetime.utcnow().strftime("%Y-%m-%d")
    py, pmo, pd = map(int, prog_date_str.split("-"))
    jd_prog_target = julian_day(py, pmo, pd, 12.0)

    # Secondary progressions: 1 day = 1 year
    years_elapsed = (jd_prog_target - jd_natal) / 365.25
    jd_prog = jd_natal + years_elapsed  # 1 day per year

    prog_pos = calc_planet_positions(jd_prog)
    prog_cusps, prog_asc, prog_mc = calc_houses(jd_prog, lat, lon)
    natal_pos = calc_planet_positions(jd_natal)

    header(
        "SECONDARY PROGRESSIONS",
        f"Natal: {args.date}  ·  Progressed to: {prog_date_str}  ({years_elapsed:.1f} years)"
    )
    print_planet_table(prog_pos, prog_cusps, title="PROGRESSED PLANETS")

    # Aspects: progressed to natal
    section("PROGRESSED-TO-NATAL ASPECTS")
    print(f"  │  {'Prog Planet':<14} {'Aspect':<14} {'Natal Planet':<14} {'Orb':>6}")
    print(f"  │  {'─'*14} {'─'*14} {'─'*14} {'─'*6}")
    for pp, pd_data in prog_pos.items():
        if pp in ("S.Node","Ceres","Pallas","Juno","Vesta","Uranus","Neptune","Pluto"):
            continue
        for np, nd_data in natal_pos.items():
            if np in ("S.Node","Ceres","Pallas","Juno","Vesta"):
                continue
            diff = angle_diff(pd_data["longitude"], nd_data["longitude"])
            for asp_name, (angle, orb_l, orb_o, glyph, quality) in ASPECTS.items():
                if asp_name in ("Quintile","Bi-Quintile","Septile","Semi-Sextile","Semi-Square","Sesquisquare"):
                    continue
                orb = 1.5  # tight orbs for progressions
                if abs(diff - angle) <= orb:
                    print(f"  │  {pp:<14} {glyph} {asp_name:<12} {np:<14} {abs(diff-angle):>5.2f}°")
    print()


def cmd_lunar(args):
    if not SWE:
        print("pyswisseph required.")
        return

    now = datetime.datetime.utcnow()
    jd_now = julian_day(now.year, now.month, now.day,
                         now.hour + now.minute / 60.0)
    pos = calc_planet_positions(jd_now)

    sun_lon  = pos.get("Sun",  {}).get("longitude", 0)
    moon_lon = pos.get("Moon", {}).get("longitude", 0)

    phase_name, phase_glyph, elongation, illumination = calc_lunar_phase(sun_lon, moon_lon)
    moon_sign, msidx, m_deg, m_min = deg_to_sign(moon_lon)
    sun_sign,  ssidx, s_deg, s_min = deg_to_sign(sun_lon)

    header("LUNAR INTELLIGENCE", now.strftime("%Y-%m-%d  %H:%M UTC"))

    print(f"  Current Phase:    {phase_glyph}  {phase_name}")
    print(f"  Moon Position:    {moon_sign} {SIGN_SYMBOL[msidx]} {m_deg}°{m_min:02d}'")
    print(f"  Sun Position:     {sun_sign}  {SIGN_SYMBOL[ssidx]} {s_deg}°{s_min:02d}'")
    print(f"  Elongation:       {elongation:.2f}°")
    print(f"  Illumination:     {illumination}%")
    print()

    # Void of course
    voc, hours_remaining = void_of_course(jd_now, moon_lon, pos)
    print(f"  Void of Course:   {'YES — Moon casts no more aspects in {moon_sign}' if voc else f'No  (ingress in ~{hours_remaining:.1f}h)'}")
    print()

    # Rune of current Moon sign
    rune_name, rune_sym, rune_meaning = SIGN_RUNES.get(moon_sign, ("?", "?", "?"))
    print(f"  Moon Rune:        {rune_sym} {rune_name} — {rune_meaning}")
    print()

    # Next lunations
    try:
        new_jd, full_jd = next_lunation(jd_now)
        if new_jd:
            print(f"  Next New Moon:    {jd_to_dt(new_jd)}")
        if full_jd:
            print(f"  Next Full Moon:   {jd_to_dt(full_jd)}")
    except Exception:
        pass
    print()

    # Moon aspects to current sky
    section("MOON ASPECTS (NOW)")
    moon_aspects = [(p1, p2, asp, orb, q, g, app)
                    for p1, p2, asp, orb, q, g, app in calc_aspects(pos)
                    if "Moon" in (p1, p2)]
    for p1, p2, asp, orb, q, g, app in moon_aspects:
        other = p2 if p1 == "Moon" else p1
        print(f"  │  Moon {g} {asp:<14} {other:<12}  orb {orb:.2f}°  {'Appl.' if app else 'Sep.'}")
    print()


def cmd_planet_hours(args):
    if args.date:
        y, mo, d = map(int, args.date.split("-"))
        date = datetime.date(y, mo, d)
    else:
        date = datetime.date.today()

    # Resolve location: explicit lat/lon > city/nation geocode > Indianapolis default
    if getattr(args, "lat", None) and getattr(args, "lon", None):
        lat, lon = float(args.lat), float(args.lon)
    elif getattr(args, "city", None) and getattr(args, "nation", None):
        lat, lon, _ = geocode_city(args.city, args.nation)
    else:
        lat, lon = 39.7684, -86.1581  # Indianapolis default

    try:
        hours_data, day_ruler, sunrise_jd, sunset_jd = planetary_hours(date, lat, lon)
    except Exception as e:
        print(f"Error calculating planetary hours: {e}")
        return

    header("PLANETARY HOURS", f"{date}  ·  Day Ruler: {day_ruler}  ·  Lat {lat:.2f}° Lon {lon:.2f}°")

    print(f"  Sunrise: {jd_to_dt(sunrise_jd)}")
    print(f"  Sunset:  {jd_to_dt(sunset_jd)}")
    print()

    section("DAY HOURS")
    print(f"  │  {'Hour':>4}  {'Planet':<12} {'Norse':<40}")
    print(f"  │  {'─'*4}  {'─'*12} {'─'*40}")
    for period, num, planet, jd_start, dur_min in hours_data:
        if period == "day":
            norse = NORSE_CORRESPONDENCES.get(planet, "").split("—")[0].strip()
            time_str = jd_to_dt(jd_start).split(" ")[1] if SWE else ""
            print(f"  │  D{num:>2}.  {planet:<12} {norse}")

    section("NIGHT HOURS")
    print(f"  │  {'Hour':>4}  {'Planet':<12} {'Norse'}")
    print(f"  │  {'─'*4}  {'─'*12} {'─'*40}")
    for period, num, planet, jd_start, dur_min in hours_data:
        if period == "night":
            norse = NORSE_CORRESPONDENCES.get(planet, "").split("—")[0].strip()
            print(f"  │  N{num:>2}.  {planet:<12} {norse}")
    print()


def cmd_lots(args):
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, _ = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd = julian_day(y, mo, d, utc_hour)
    positions = calc_planet_positions(jd)
    cusps, asc, mc = calc_houses(jd, lat, lon)
    sun_lon = positions.get("Sun", {}).get("longitude", 0)
    day = is_day_chart(sun_lon, asc)

    header("ARABIC LOTS / HERMETIC PARTS", f"{args.date}  ·  {'Day' if day else 'Night'} Chart")
    lots = calc_lots(positions, asc, day)
    print_lots(lots, cusps)


def cmd_hellenistic(args):
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, _ = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd = julian_day(y, mo, d, utc_hour)
    positions = calc_planet_positions(jd)
    cusps, asc, mc = calc_houses(jd, lat, lon)

    header("HELLENISTIC ASTROLOGY ANALYSIS", f"{args.date}  {args.time or ''}")
    print_hellenistic(positions, cusps, asc)
    print_dignity_table(positions)
    print_antiscia(calc_antiscia(positions))


def cmd_aspect_grid(args):
    y, mo, d, hour = parse_date_time(args.date, args.time)
    jd = julian_day(y, mo, d, hour)  # aspect-grid has no location so no TZ conversion
    positions = calc_planet_positions(jd)

    header("FULL ASPECT GRID", args.date)
    print_aspects(calc_aspects(positions), max_show=200)


def cmd_dignity(args):
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, _ = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd = julian_day(y, mo, d, utc_hour)
    positions = calc_planet_positions(jd)
    cusps, asc, mc = calc_houses(jd, lat, lon)

    header("ESSENTIAL DIGNITIES", f"{args.date}  {args.time or ''}")
    print_dignity_table(positions)

    # Mutual receptions
    receps = mutual_reception(positions)
    section("MUTUAL RECEPTIONS")
    if receps:
        for p1, p2, s1, s2 in receps:
            print(f"  │  {p1} in {s1}  ⇔  {p2} in {s2}")
            print(f"  │    Both planets swap homes — strong cooperative bond, dignity by mutual reception")
    else:
        print(f"  │  None detected")
    print()

    # Scoring summary
    section("DIGNITY SCORE SUMMARY")
    scores = []
    for name in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]:
        if name not in positions:
            continue
        d_data = positions[name]
        score, _ = essential_dignity(name, d_data["sign"], d_data["degree"])
        scores.append((score, name))
    scores.sort(reverse=True)
    print(f"  │  {'Rank':<5} {'Planet':<12} {'Score':>6}  {'Status'}")
    print(f"  │  {'─'*5} {'─'*12} {'─'*6}  {'─'*20}")
    for i, (score, name) in enumerate(scores, 1):
        if score >= 5:   status = "Highly dignified"
        elif score >= 3: status = "Dignified"
        elif score >= 1: status = "Moderate"
        elif score == 0: status = "Peregrine"
        elif score >= -3:status = "Weakened"
        else:            status = "Debilitated"
        print(f"  │  {i:<5} {name:<12} {score:>+6}  {status}")
    print()


def cmd_antiscia(args):
    """Gap 1 fix: standalone antiscia subcommand."""
    y, mo, d, hour = parse_date_time(args.date, args.time)
    jd = julian_day(y, mo, d, hour)
    positions = calc_planet_positions(jd)

    header("ANTISCIA & CONTRA-ANTISCIA", f"{args.date}  {args.time or ''}")

    print("  Antiscia mirror: solstice axis (0° Cancer / 0° Capricorn)")
    print("  Contra-antiscia: equinox axis (0° Aries / 0° Libra)")
    print()

    antiscia_data = calc_antiscia(positions)
    print_antiscia(antiscia_data)

    # Check for antiscia conjunctions between planets
    section("ANTISCIA CONNECTIONS (within 1°)")
    print(f"  │  {'Planet A':<12} {'Antiscia of A':<24} {'Planet B':<12} {'Position of B':<24} {'Orb':>6}")
    print(f"  │  {'─'*12} {'─'*24} {'─'*12} {'─'*24} {'─'*6}")
    planet_list = [p for p in antiscia_data]
    found_any = False
    for i, p1 in enumerate(planet_list):
        for p2 in planet_list[i+1:]:
            if p2 not in positions:
                continue
            a_lon  = antiscia_data[p1]["antiscia_lon"]
            p2_lon = positions[p2]["longitude"]
            orb = angle_diff(a_lon, p2_lon)
            if orb <= 1.0:
                found_any = True
                print(f"  │  {p1:<12} {antiscia_data[p1]['antiscia']:<24} {p2:<12} {fmt_position(positions[p2]):<24} {orb:>5.2f}°")
            # Also check contra-antiscia
            c_lon = antiscia_data[p1]["contra_lon"]
            c_orb = angle_diff(c_lon, p2_lon)
            if c_orb <= 1.0:
                found_any = True
                print(f"  │  {p1:<12} contra: {antiscia_data[p1]['contra']:<18} {p2:<12} {fmt_position(positions[p2]):<24} {c_orb:>5.2f}°  [contra]")
    if not found_any:
        print(f"  │  No antiscia connections within 1° orb")
    print()


def cmd_composite(args):
    """Composite chart (midpoint method) for two people. Optionally show Davison chart too."""
    c1, n1a = getattr(args,"city1",None), getattr(args,"nation1",None)
    c2, n2a = getattr(args,"city2",None), getattr(args,"nation2",None)
    y1, mo1, d1, h1, _lat1, _lon1, _, tzl1, _, _ = resolve_birth(
        args.date1, getattr(args,"time1",None),
        c1 or "London", n1a or "GB",
        getattr(args,"lat1",None), getattr(args,"lon1",None)
    )
    y2, mo2, d2, h2, _lat2, _lon2, _, tzl2, _, _ = resolve_birth(
        args.date2, getattr(args,"time2",None),
        c2 or "London", n2a or "GB",
        getattr(args,"lat2",None), getattr(args,"lon2",None)
    )
    jd1 = julian_day(y1, mo1, d1, h1)
    jd2 = julian_day(y2, mo2, d2, h2)
    n1 = getattr(args, "name1", "Person A")
    n2 = getattr(args, "name2", "Person B")

    pos1 = calc_planet_positions(jd1)
    pos2 = calc_planet_positions(jd2)
    comp = calc_composite(pos1, pos2)

    header("COMPOSITE CHART", f"{n1}  +  {n2}  (Midpoint Method)")
    print_planet_table(comp, title="COMPOSITE PLANETS")
    print_aspects(calc_aspects(comp))
    print_dignity_table(comp)

    # Davison chart
    c1   = getattr(args, "city1", None)
    nat1 = getattr(args, "nation1", None)
    c2   = getattr(args, "city2", None)
    nat2 = getattr(args, "nation2", None)
    l1   = getattr(args, "lat1", None)
    lo1  = getattr(args, "lon1", None)
    l2   = getattr(args, "lat2", None)
    lo2  = getattr(args, "lon2", None)

    if (c1 and nat1) or (l1 and lo1):
        lat1, lon1, _ = geocode_city(c1 or "", nat1 or "", l1, lo1)
    else:
        lat1, lon1 = 0.0, 0.0
    if (c2 and nat2) or (l2 and lo2):
        lat2, lon2, _ = geocode_city(c2 or "", nat2 or "", l2, lo2)
    else:
        lat2, lon2 = 0.0, 0.0

    if lat1 != 0.0 or lat2 != 0.0:
        jd_dav, lat_dav, lon_dav = calc_davison(jd1, jd2, lat1, lon1, lat2, lon2)
        dav_pos = calc_planet_positions(jd_dav)
        dav_cusps, dav_asc, dav_mc = calc_houses(jd_dav, lat_dav, lon_dav)
        dav_dt   = jd_to_dt(jd_dav)
        section(f"DAVISON RELATIONSHIP CHART  ({dav_dt}  ·  {lat_dav:.2f}°N {lon_dav:.2f}°E)")
        print_planet_table(dav_pos, dav_cusps, title="DAVISON PLANETS")
        asc_sign, asidx, asc_deg, asc_min = deg_to_sign(dav_asc)
        mc_sign,  msidx, mc_deg,  mc_min  = deg_to_sign(dav_mc)
        print(f"  Davison ASC: {asc_sign} {SIGN_SYMBOL[asidx]} {asc_deg}°{asc_min:02d}'")
        print(f"  Davison MC:  {mc_sign}  {SIGN_SYMBOL[msidx]} {mc_deg}°{mc_min:02d}'")
        print()
    else:
        print("  (Add --city1/--nation1 and --city2/--nation2 to enable the Davison chart)")
        print()


def cmd_synergy(args):
    """Full relationship analysis: synastry + composite + synergy score + midpoints."""
    y1, mo1, d1, h1, _la1, _lo1, _, tzl1, _, _ = resolve_birth(
        args.date1, getattr(args,"time1",None), "London", "GB"
    )
    y2, mo2, d2, h2, _la2, _lo2, _, tzl2, _, _ = resolve_birth(
        args.date2, getattr(args,"time2",None), "London", "GB"
    )
    jd1 = julian_day(y1, mo1, d1, h1)
    jd2 = julian_day(y2, mo2, d2, h2)
    n1 = getattr(args, "name1", "Person A")
    n2 = getattr(args, "name2", "Person B")

    pos1 = calc_planet_positions(jd1)
    pos2 = calc_planet_positions(jd2)
    comp = calc_composite(pos1, pos2)

    header("SYNERGY ANALYSIS", f"{n1}  ×  {n2}")

    # Cross-aspects and score
    core = ("Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Chiron","N.Node")
    cross_rows = []
    for p1, d1d in pos1.items():
        if p1 not in core:
            continue
        for p2, d2d in pos2.items():
            if p2 not in core:
                continue
            diff = angle_diff(d1d["longitude"], d2d["longitude"])
            for asp_name, (angle, orb_l, orb_o, glyph, quality) in ASPECTS.items():
                if asp_name in ("Quintile","Bi-Quintile","Septile","Semi-Sextile"):
                    continue
                orb = orb_l if p1 in ("Sun","Moon") or p2 in ("Sun","Moon") else orb_o
                actual_orb = abs(diff - angle)
                if actual_orb <= orb:
                    applying = (d1d["speed"] - d2d.get("speed", 0)) > 0
                    cross_rows.append((actual_orb, p1, glyph, asp_name, p2, quality, applying))
    cross_rows.sort()

    total_score, cats = synergy_score(cross_rows)
    pct_harmony = cats["harmony"] / max(0.1, cats["harmony"] + cats["challenge"]) * 100

    section("SYNERGY SCORE")
    bar_len = 40
    h_bars = int(pct_harmony / 100 * bar_len)
    c_bars = bar_len - h_bars
    bar = "█" * h_bars + "░" * c_bars
    print(f"  │  Harmony:   {cats['harmony']:.1f}  ·  Challenge: {cats['challenge']:.1f}")
    print(f"  │  Net score: {total_score:+.1f}")
    print(f"  │  [{bar}] {pct_harmony:.0f}% harmony")
    if pct_harmony >= 70:
        verdict = "Highly harmonious — strong natural flow and ease"
    elif pct_harmony >= 55:
        verdict = "Mostly harmonious — supportive with productive friction"
    elif pct_harmony >= 40:
        verdict = "Mixed — significant growth potential, requires conscious effort"
    else:
        verdict = "Challenging — high activation energy, powerful transformation possible"
    print(f"  │  {verdict}")
    print()

    # Top aspects by significance
    section(f"KEY CROSS-ASPECTS  {n1} → {n2}")
    print(f"  │  {n1+' Planet':<14} {'Asp':<16} {n2+' Planet':<14} {'Orb':>6}  {'Quality':<12} App/Sep")
    print(f"  │  {'─'*14} {'─'*16} {'─'*14} {'─'*6}  {'─'*12} {'─'*6}")
    for actual_orb, p1, glyph, asp_name, p2, quality, applying in cross_rows[:30]:
        app = "Appl." if applying else "Sep."
        print(f"  │  {p1:<14} {glyph} {asp_name:<14} {p2:<14} {actual_orb:>5.2f}°  {quality:<12} {app}")
    print()

    # Composite chart
    section(f"COMPOSITE CHART (Midpoints)")
    print_planet_table(comp, title=f"COMPOSITE PLANETS — {n1} + {n2}")
    comp_aspects = calc_aspects(comp)
    print_aspects(comp_aspects, max_show=20)

    # Composite dignity highlights
    section("COMPOSITE DIGNITY HIGHLIGHTS")
    for name in ["Sun","Moon","Venus","Mars","Jupiter","Saturn"]:
        if name not in comp:
            continue
        cd = comp[name]
        score, labels = essential_dignity(name, cd["sign"], cd["degree"])
        if score != 0:
            print(f"  │  {name} in {cd['sign']}: {labels[0]}  (score {score:+d})")
    print()

    # Shared midpoints between charts (within 2°)
    section("CROSS-MIDPOINTS  (planet of A at midpoint of B pair, within 2°)")
    mps2 = calc_midpoints(pos2)
    hits = []
    for p1, d1d in pos1.items():
        if p1 not in core:
            continue
        for mp_lon, pa, pb, mp_sign, mp_deg, mp_min in mps2:
            orb = angle_diff(d1d["longitude"], mp_lon)
            if orb <= 2.0:
                hits.append((orb, p1, pa, pb, mp_sign, mp_deg, mp_min))
    hits.sort()
    if hits:
        print(f"  │  {n1+' Planet':<14} {'Midpoint of '+n2:<32} {'Position':<20} {'Orb':>5}")
        print(f"  │  {'─'*14} {'─'*32} {'─'*20} {'─'*5}")
        for orb, p1, pa, pb, mp_sign, mp_deg, mp_min in hits[:20]:
            mp_str = f"{mp_sign} {mp_deg}°{mp_min:02d}'"
            pair = f"{pa}/{pb}"
            print(f"  │  {p1:<14} {pair:<32} {mp_str:<20} {orb:>4.2f}°")
    else:
        print(f"  │  No cross-midpoint hits within 2°")
    print()


def cmd_predict(args):
    """Event prediction: exact transit dates, stations, ingresses, eclipses."""
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, _ = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd_natal = julian_day(y, mo, d, utc_hour)
    natal_pos = calc_planet_positions(jd_natal)
    cusps, asc, mc = calc_houses(jd_natal, lat, lon)

    # Add Asc and MC to natal positions for aspect targets
    asc_sign, asidx, asc_deg, asc_min = deg_to_sign(asc)
    mc_sign,  msidx, mc_deg,  mc_min  = deg_to_sign(mc)
    natal_pos["Asc"] = {"longitude": asc, "sign": asc_sign, "sign_idx": asidx,
                        "degree": asc_deg, "minutes": asc_min,
                        "latitude": 0, "speed": 0, "retrograde": False}
    natal_pos["MC"]  = {"longitude": mc,  "sign": mc_sign,  "sign_idx": msidx,
                        "degree": mc_deg,  "minutes": mc_min,
                        "latitude": 0, "speed": 0, "retrograde": False}

    start_str = getattr(args, "start", None) or datetime.datetime.utcnow().strftime("%Y-%m-%d")
    end_str   = getattr(args, "end",   None) or (
        datetime.datetime(int(start_str[:4]) + 1, int(start_str[5:7]), int(start_str[8:10]))
        .strftime("%Y-%m-%d")
    )
    sy, smo, sd = map(int, start_str.split("-"))
    ey, emo, ed = map(int, end_str.split("-"))
    start_jd = julian_day(sy, smo, sd, 0.0)
    end_jd   = julian_day(ey, emo, ed, 23.9)

    t_planets = (getattr(args, "transit_planets", None) or
                 "Jupiter,Saturn,Uranus,Neptune,Pluto,Chiron,N.Node,Mars,Sun,Venus,Mercury").split(",")
    n_planets = (getattr(args, "natal_planets",   None) or
                 "Sun,Moon,Mercury,Venus,Mars,Jupiter,Saturn,Chiron,N.Node,Asc,MC").split(",")

    header("EVENT PREDICTION", f"Natal: {args.date}  ·  Window: {start_str} → {end_str}")

    # Step size: fine for inner planets, coarse for outer
    step = 0.5 if "Sun" in t_planets or "Moon" in t_planets or "Mercury" in t_planets else 1.0

    # Exact transit-to-natal aspects
    section("EXACT TRANSIT-TO-NATAL ASPECTS")
    print("  Computing... (this may take a few seconds)", flush=True)
    events = find_exact_transit_dates(natal_pos, start_jd, end_jd, t_planets, n_planets, step=step)
    print(f"\r  Found {len(events)} exact aspects in window.                    ")
    if events:
        print(f"  │  {'Date':<12} {'Transit':<12} {'Asp':<14} {'Natal':<12} {'Quality'}")
        print(f"  │  {'─'*12} {'─'*12} {'─'*14} {'─'*12} {'─'*14}")
        for jd_e, t_p, asp, glyph, n_p, quality in events:
            dt_str = jd_to_dt(jd_e).split(" ")[0]
            print(f"  │  {dt_str:<12} {t_p:<12} {glyph} {asp:<12} {n_p:<12} {quality}")
    print()

    # Stations
    section("PLANETARY STATIONS (Retrograde / Direct)")
    stations = find_stations(start_jd, end_jd)
    if stations:
        print(f"  │  {'Date':<12} {'Planet':<12} {'Event':<26} {'Position'}")
        print(f"  │  {'─'*12} {'─'*12} {'─'*26} {'─'*20}")
        for jd_s, planet, kind, sign, deg, mins in stations:
            dt_str = jd_to_dt(jd_s).split(" ")[0]
            pos_str = f"{sign} {deg}°{mins:02d}'"
            print(f"  │  {dt_str:<12} {planet:<12} {kind:<26} {pos_str}")
    else:
        print(f"  │  No stations found in window")
    print()

    # Ingresses
    section("SIGN INGRESSES")
    ingresses = find_ingresses(start_jd, end_jd)
    if ingresses:
        print(f"  │  {'Date':<12} {'Planet':<12} {'From':<14} → {'Into':<14}")
        print(f"  │  {'─'*12} {'─'*12} {'─'*14}   {'─'*14}")
        for jd_i, planet, from_sign, into_sign in ingresses:
            dt_str = jd_to_dt(jd_i).split(" ")[0]
            print(f"  │  {dt_str:<12} {planet:<12} {from_sign:<14} → {into_sign}")
    else:
        print(f"  │  No ingresses found in window")
    print()

    # Eclipses
    section("ECLIPSES")
    eclipses = find_eclipses(start_jd, end_jd)
    if eclipses:
        print(f"  │  {'Date':<12} {'Type':<32} {'Position'}")
        print(f"  │  {'─'*12} {'─'*32} {'─'*20}")
        for jd_ec, etype, sign, deg, mins in eclipses:
            dt_str = jd_to_dt(jd_ec).split(" ")[0]
            pos_str = f"{sign} {deg}°{mins:02d}'"
            print(f"  │  {dt_str:<12} {etype:<32} {pos_str}")
    else:
        print(f"  │  No eclipses found in window (or swe eclipse functions unavailable)")
    print()


def cmd_geoastrology(args):
    """Astrocartography: MC, IC, ASC, DSC lines for a natal chart."""
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, _ = resolve_birth(
        args.date, args.time,
        getattr(args, "city", None) or "London",
        getattr(args, "nation", None) or "GB",
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd = julian_day(y, mo, d, utc_hour)
    positions = calc_planet_positions(jd)
    name = args.name or "Seeker"

    header("GEOASTROLOGY — ASTROCARTOGRAPHY", f"{name}  ·  {args.date}  ·  {tz_label}")

    lines = calc_astrocartography(jd, positions)

    # MC / IC lines table
    section("MC AND IC LINES  (planet on upper/lower meridian)")
    print(f"  │  {'Planet':<12} {'RA':>7}  {'Dec':>7}  {'MC Lon':>8}  MC Region")
    print(f"  │  {'':24}{'IC Lon':>8}  IC Region")
    print(f"  │  {'─'*12} {'─'*7}  {'─'*7}  {'─'*8}  {'─'*30}")
    for planet in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
                   "Uranus","Neptune","Pluto","Chiron","N.Node"]:
        if planet not in lines:
            continue
        L = lines[planet]
        mc = L["MC_lon"]
        ic = L["IC_lon"]
        ra = L["ra"]
        dec = L["dec"]
        mc_dir = "E" if mc >= 0 else "W"
        ic_dir = "E" if ic >= 0 else "W"
        mc_region = geo_region(mc)
        ic_region = geo_region(ic)
        sym = PLANET_SYMBOL.get(planet, "?")
        print(f"  │  {sym} {planet:<10} {ra:>7.2f}°  {dec:>+7.2f}°  MC {abs(mc):>5.1f}°{mc_dir:<2}  {mc_region}")
        print(f"  │  {'':12}                        IC {abs(ic):>5.1f}°{ic_dir:<2}  {ic_region}")
    print()

    # ASC line table — show latitudes where ASC line passes through notable longitudes
    section("ASC LINES  (planet on eastern horizon — power locations)")
    print(f"  ASC line crossings by latitude (planet rises at these Earth longitudes):")
    print()
    for planet in ["Sun","Moon","Venus","Jupiter","Saturn","Mars","Mercury"]:
        if planet not in lines:
            continue
        L = lines[planet]
        sym = PLANET_SYMBOL.get(planet, "?")
        print(f"  │  {sym} {planet} ASC line:")
        print(f"  │    {'Lat':>5}  {'Lon':>8}  Region")
        print(f"  │    {'─'*5}  {'─'*8}  {'─'*34}")
        for lat_deg, geo_lon in L["ASC_lons"]:
            dir_c = "N" if lat_deg >= 0 else "S"
            dir_l = "E" if geo_lon >= 0 else "W"
            region = geo_region(geo_lon)
            print(f"  │    {abs(lat_deg):>4}°{dir_c}  {abs(geo_lon):>6.1f}°{dir_l}  {region}")
        print()

    # DSC line summary (briefer)
    section("DSC LINES  (planet on western horizon — relationship/other locations)")
    print(f"  │  {'Planet':<12} {'Lat 0°':<16} {'Lat 40°N':<16} {'Lat 40°S':<16}")
    print(f"  │  {'─'*12} {'─'*16} {'─'*16} {'─'*16}")
    for planet in ["Sun","Moon","Venus","Mars","Jupiter","Saturn"]:
        if planet not in lines:
            continue
        L = lines[planet]
        lons_by_lat = {lat: lon for lat, lon in L["DSC_lons"]}
        l0  = f"{abs(lons_by_lat.get(0,  999)):>5.1f}°{'E' if lons_by_lat.get(0,0)  >= 0 else 'W'}" if 0   in lons_by_lat else "n/a"
        l40n= f"{abs(lons_by_lat.get(40, 999)):>5.1f}°{'E' if lons_by_lat.get(40,0) >= 0 else 'W'}" if 40  in lons_by_lat else "n/a"
        l40s= f"{abs(lons_by_lat.get(-40,999)):>5.1f}°{'E' if lons_by_lat.get(-40,0)>= 0 else 'W'}" if -40 in lons_by_lat else "n/a"
        sym = PLANET_SYMBOL.get(planet, "?")
        print(f"  │  {sym} {planet:<10} {l0:<16} {l40n:<16} {l40s:<16}")
    print()

    # Power spot finder: where is a user-specified location relative to chart lines?
    query_lat = getattr(args, "query_lat", None)
    query_lon = getattr(args, "query_lon", None)
    if query_lat and query_lon:
        qlat = float(query_lat)
        qlon = float(query_lon)
        section(f"POWER SPOT ANALYSIS  ({qlat:.2f}°N, {qlon:.2f}°E)")
        print(f"  Nearest astrocartography lines to this location:")
        print()
        hits = []
        for planet, L in lines.items():
            if planet in ("S.Node","Ceres","Pallas","Juno","Vesta"):
                continue
            # MC line distance
            mc_dist = abs(angle_diff(qlon, L["MC_lon"]))
            if mc_dist <= 15:
                hits.append((mc_dist, planet, "MC line", L["MC_lon"]))
            ic_dist = abs(angle_diff(qlon, L["IC_lon"]))
            if ic_dist <= 15:
                hits.append((ic_dist, planet, "IC line", L["IC_lon"]))
            # ASC/DSC: find closest latitude
            for lat_a, lon_a in L["ASC_lons"]:
                combo_dist = math.sqrt((lat_a - qlat)**2 + angle_diff(lon_a, qlon)**2)
                if combo_dist <= 10:
                    hits.append((combo_dist, planet, "ASC line", lon_a))
                    break
            for lat_d, lon_d in L["DSC_lons"]:
                combo_dist = math.sqrt((lat_d - qlat)**2 + angle_diff(lon_d, qlon)**2)
                if combo_dist <= 10:
                    hits.append((combo_dist, planet, "DSC line", lon_d))
                    break
        hits.sort()
        if hits:
            for dist, planet, line_type, line_lon in hits[:10]:
                kw = PLANET_KEYWORDS.get(planet, "").split("·")[0].strip()
                norse = NORSE_CORRESPONDENCES.get(planet, "").split("—")[0].strip()
                print(f"  │  {PLANET_SYMBOL.get(planet,'?')} {planet} {line_type}  (dist {dist:.1f}°)")
                print(f"  │    Energy: {kw}")
                print(f"  │    Norse:  {norse}")
                print()
        else:
            print(f"  │  No major lines within 15° of this location")
        print()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        prog="astrology_engine",
        description="Advanced Astrology Engine — Volmarr's Longhall / Hermes Divination Skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = p.add_subparsers(dest="cmd")

    def add_geo(parser, city_default="London", nation_default="GB"):
        """Add --city/--nation/--lat/--lon to a subparser."""
        parser.add_argument("--city",   default=city_default)
        parser.add_argument("--nation", default=nation_default)
        parser.add_argument("--lat",    default=None, help="Override latitude (decimal)")
        parser.add_argument("--lon",    default=None, help="Override longitude (decimal)")

    # natal
    natal = sub.add_parser("natal", help="Full natal chart")
    natal.add_argument("--date", required=True, help="YYYY-MM-DD")
    natal.add_argument("--time", default=None,  help="HH:MM (24h)")
    natal.add_argument("--name", default=None)
    add_geo(natal)

    # transit  (gap 2: --transit-date / --transit-time)
    transit = sub.add_parser("transit", help="Transits to natal (default: now; use --transit-date to forecast)")
    transit.add_argument("--date",         required=True, help="Natal birth date YYYY-MM-DD")
    transit.add_argument("--time",         default=None,  help="Natal birth time HH:MM")
    transit.add_argument("--transit-date", default=None,  dest="transit_date",
                         help="Sky date to compare (default: now) YYYY-MM-DD")
    transit.add_argument("--transit-time", default=None,  dest="transit_time",
                         help="Sky time HH:MM (default: noon if transit-date given)")
    add_geo(transit)

    # synastry  (gap 6: --city1/2 --nation1/2 --lat1/2 --lon1/2)
    syn = sub.add_parser("synastry", help="Two-chart synastry with optional house overlays")
    syn.add_argument("--date1",    required=True)
    syn.add_argument("--date2",    required=True)
    syn.add_argument("--time1",    default=None)
    syn.add_argument("--time2",    default=None)
    syn.add_argument("--name1",    default="Person A")
    syn.add_argument("--name2",    default="Person B")
    syn.add_argument("--city1",    default=None, help="Person A birth city (enables house overlays)")
    syn.add_argument("--nation1",  default=None)
    syn.add_argument("--city2",    default=None, help="Person B birth city (enables house overlays)")
    syn.add_argument("--nation2",  default=None)
    syn.add_argument("--lat1",     default=None)
    syn.add_argument("--lon1",     default=None)
    syn.add_argument("--lat2",     default=None)
    syn.add_argument("--lon2",     default=None)

    # solar return
    sr = sub.add_parser("solar-return", help="Solar return chart")
    sr.add_argument("--date",  required=True)
    sr.add_argument("--time",  default=None)
    sr.add_argument("--year",  default=None)
    add_geo(sr)

    # progressions
    prog = sub.add_parser("progressions", help="Secondary progressions")
    prog.add_argument("--date",      required=True)
    prog.add_argument("--time",      default=None)
    prog.add_argument("--prog-date", default=None, dest="prog_date", help="Target date YYYY-MM-DD")
    add_geo(prog)

    # lunar
    sub.add_parser("lunar", help="Lunar intelligence — phase, VOC, next lunations")

    # planet-hours
    ph = sub.add_parser("planet-hours", help="Planetary hours for a date and location")
    ph.add_argument("--date", default=None, help="YYYY-MM-DD (default today)")
    ph.add_argument("--lat",  default=None, help="Latitude decimal")
    ph.add_argument("--lon",  default=None, help="Longitude decimal")
    ph.add_argument("--city",   default=None)
    ph.add_argument("--nation", default=None)

    # lots
    lots_p = sub.add_parser("lots", help="Arabic Lots / Hermetic Parts")
    lots_p.add_argument("--date", required=True)
    lots_p.add_argument("--time", default=None)
    add_geo(lots_p)

    # hellenistic
    hell = sub.add_parser("hellenistic", help="Hellenistic analysis — sect, bonification, joys")
    hell.add_argument("--date", required=True)
    hell.add_argument("--time", default=None)
    add_geo(hell)

    # dignity  (gap 1: new standalone command)
    dig = sub.add_parser("dignity", help="Essential dignities table with scoring and mutual receptions")
    dig.add_argument("--date", required=True)
    dig.add_argument("--time", default=None)
    add_geo(dig)

    # antiscia  (gap 1: new standalone command)
    ant = sub.add_parser("antiscia", help="Antiscia and contra-antiscia with connection detection")
    ant.add_argument("--date", required=True)
    ant.add_argument("--time", default=None)

    # composite
    comp_p = sub.add_parser("composite", help="Composite chart (midpoints) + optional Davison chart")
    comp_p.add_argument("--date1",   required=True)
    comp_p.add_argument("--date2",   required=True)
    comp_p.add_argument("--time1",   default=None)
    comp_p.add_argument("--time2",   default=None)
    comp_p.add_argument("--name1",   default="Person A")
    comp_p.add_argument("--name2",   default="Person B")
    comp_p.add_argument("--city1",   default=None)
    comp_p.add_argument("--nation1", default=None)
    comp_p.add_argument("--city2",   default=None)
    comp_p.add_argument("--nation2", default=None)
    comp_p.add_argument("--lat1",    default=None)
    comp_p.add_argument("--lon1",    default=None)
    comp_p.add_argument("--lat2",    default=None)
    comp_p.add_argument("--lon2",    default=None)

    # synergy
    syne = sub.add_parser("synergy", help="Full relationship analysis: aspects + composite + score + midpoints")
    syne.add_argument("--date1",   required=True)
    syne.add_argument("--date2",   required=True)
    syne.add_argument("--time1",   default=None)
    syne.add_argument("--time2",   default=None)
    syne.add_argument("--name1",   default="Person A")
    syne.add_argument("--name2",   default="Person B")

    # predict
    pred = sub.add_parser("predict",
        help="Exact transit dates, stations, ingresses, eclipses within a window")
    pred.add_argument("--date",   required=True, help="Natal birth date YYYY-MM-DD")
    pred.add_argument("--time",   default=None)
    pred.add_argument("--start",  default=None,  help="Window start YYYY-MM-DD (default: today)")
    pred.add_argument("--end",    default=None,  help="Window end   YYYY-MM-DD (default: 1 year)")
    pred.add_argument("--transit-planets", default=None, dest="transit_planets",
                      help="Comma-separated transit planets (default: all)")
    pred.add_argument("--natal-planets",   default=None, dest="natal_planets",
                      help="Comma-separated natal points (default: all)")
    add_geo(pred)

    # geoastrology
    geo_p = sub.add_parser("geoastrology",
        help="Astrocartography MC/IC/ASC/DSC lines; add --query-lat/--query-lon for power-spot analysis")
    geo_p.add_argument("--date",       required=True)
    geo_p.add_argument("--time",       default=None)
    geo_p.add_argument("--name",       default=None)
    add_geo(geo_p)
    geo_p.add_argument("--query-lat",  default=None, dest="query_lat",
                       help="Latitude to analyse proximity of lines")
    geo_p.add_argument("--query-lon",  default=None, dest="query_lon",
                       help="Longitude to analyse proximity of lines")

    # aspect-grid
    ag = sub.add_parser("aspect-grid", help="Full aspect matrix")
    ag.add_argument("--date", required=True)
    ag.add_argument("--time", default=None)

    args = p.parse_args()
    dispatch = {
        "natal":        cmd_natal,
        "transit":      cmd_transit,
        "synastry":     cmd_synastry,
        "solar-return": cmd_solar_return,
        "progressions": cmd_progressions,
        "lunar":        cmd_lunar,
        "planet-hours": cmd_planet_hours,
        "lots":         cmd_lots,
        "hellenistic":  cmd_hellenistic,
        "dignity":      cmd_dignity,
        "antiscia":     cmd_antiscia,
        "composite":    cmd_composite,
        "synergy":      cmd_synergy,
        "predict":      cmd_predict,
        "geoastrology": cmd_geoastrology,
        "aspect-grid":  cmd_aspect_grid,
    }
    fn = dispatch.get(args.cmd)
    if fn:
        fn(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
