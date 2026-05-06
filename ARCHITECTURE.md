# Architecture — Astrology Engine

> Technical reference for vibe coding, extensions, and deep modifications to `astrology_engine.py`.

---

## Contents

- [High-Level Design](#high-level-design)
- [Data Flow](#data-flow)
- [Module Layout](#module-layout)
- [Key Constants](#key-constants)
- [Core Engine Functions](#core-engine-functions)
- [Geocoding Pipeline](#geocoding-pipeline)
- [Timezone Resolution](#timezone-resolution)
- [The `resolve_birth` Function](#the-resolve_birth-function)
- [Subcommand Handler Pattern](#subcommand-handler-pattern)
- [Aspect Engine](#aspect-engine)
- [Dignity Engine](#dignity-engine)
- [Event Prediction Engine](#event-prediction-engine)
- [Astrocartography Engine](#astrocartography-engine)
- [Output Formatting Conventions](#output-formatting-conventions)
- [Lazy Backend Singletons](#lazy-backend-singletons)
- [Known Architecture Limitations](#known-architecture-limitations)

---

## High-Level Design

```
CLI input (argparse)
        │
        ▼
  resolve_birth()          ← geo + timezone in one call
  ┌──────────────────────────────────────────────────────┐
  │  geocode_city()         4-tier cascade               │
  │  resolve_timezone()     timezonefinder → IANA tz     │
  │  local_to_utc()         pytz DST-aware conversion    │
  └──────────────────────────────────────────────────────┘
        │
        ▼
  julian_day(y, mo, d, utc_hour)   ← Swiss Ephemeris input
        │
        ▼
  calc_planet_positions(jd)        ← swe.calc_ut() for each planet
  calc_houses(jd, lat, lon)        ← swe.houses() Placidus
        │
        ▼
  Derived calculations
  ├── calc_aspects()
  ├── essential_dignity()
  ├── calc_lots()
  ├── calc_antiscia()
  ├── void_of_course()
  ├── calc_astrocartography()
  └── find_exact_transit_dates()
        │
        ▼
  Formatted output (Unicode box-drawing, Norse layer)
```

---

## Data Flow

### Input → Julian Day

All Swiss Ephemeris calls require **Julian Day in Universal Time (JD UT)**. The pipeline is:

```
"Indianapolis" + "1975-11-22" + "14:30"
        │
        ▼ geocode_city()
lat=39.7683, lon=-86.1584
        │
        ▼ resolve_timezone(lat, lon)
"America/Indiana/Indianapolis"
        │
        ▼ local_to_utc(1975, 11, 22, 14.5, tz_name)
utc_hour=19.5  (UTC-05:00 EST)
        │
        ▼ julian_day(1975, 11, 22, 19.5)
jd = 2442745.3125
        │
        ▼ swe.calc_ut(jd, planet_id)
[longitude, latitude, distance, speed_lon, speed_lat, speed_dist]
```

### Planet Position Dict Structure

`calc_planet_positions()` returns a dict keyed by planet name:

```python
{
    "Sun": {
        "longitude": 237.87,      # ecliptic longitude 0–360°
        "latitude":  -0.002,       # ecliptic latitude
        "distance":   0.987,       # AU
        "speed":     +1.010,       # degrees/day (negative = retrograde)
        "retrograde": False,
        "sign":      "Scorpio",
        "sign_idx":  7,            # 0=Aries ... 11=Pisces
        "degree":    27,           # degrees within sign
        "minutes":   52,           # arc minutes within degree
    },
    ...
}
```

### House Cusps Structure

`calc_houses()` returns `(cusps, asc, mc)`:

```python
cusps = [30.5, 62.1, 93.4, 124.7, 156.0, 187.3,
         210.5, 242.1, 273.4, 304.7, 336.0,   7.3]
# cusps[0]  = House 1 cusp longitude
# cusps[11] = House 12 cusp longitude
asc = 30.5   # Ascendant longitude (= cusps[0])
mc  = 330.2  # Midheaven longitude
```

---

## Module Layout

The file is organised into sections separated by `# ---` comment banners:

| Line Range (approx) | Section |
|---------------------|---------|
| 1–31 | Module docstring, shebang |
| 32–95 | Imports, lazy backend singletons |
| 96–390 | Constants (SIGNS, PLANETS, ASPECTS, dignities, Norse, runes) |
| 391–624 | Utility functions (julian_day, geocode, resolve_birth, etc.) |
| 625–994 | Core engine functions (positions, houses, aspects, dignity) |
| 995–1143 | Specialty calculations (planetary hours, composites, synergy) |
| 1144–1506 | Prediction engine (transit search, stations, ingresses, eclipses) |
| 1507–1701 | Astrocartography + output helpers |
| 1702–2664 | Command handlers (cmd_natal through cmd_geoastrology) |
| 2665–2847 | `main()` — argparse setup + dispatch |

---

## Key Constants

All constants are module-level dicts/lists defined before any functions.

### `PLANETS`

```python
PLANETS = {
    "Sun":     swe.SUN,         # 0
    "Moon":    swe.MOON,        # 1
    "Mercury": swe.MERCURY,     # 2
    "Venus":   swe.VENUS,       # 3
    "Mars":    swe.MARS,        # 4
    "Jupiter": swe.JUPITER,     # 5
    "Saturn":  swe.SATURN,      # 6
    "Uranus":  swe.URANUS,      # 7
    "Neptune": swe.NEPTUNE,     # 8
    "Pluto":   swe.PLUTO,       # 9
    "Chiron":  swe.CHIRON,      # 15
    "N.Node":  swe.TRUE_NODE,   # 11
    "S.Node":  swe.TRUE_NODE,   # 11 (longitude + 180°)
}
```

### `ASPECTS`

```python
ASPECTS = {
    "Conjunction":    {"angle": 0,   "orb": 8,  "quality": "fusion"},
    "Opposition":     {"angle": 180, "orb": 8,  "quality": "polarity"},
    "Trine":          {"angle": 120, "orb": 7,  "quality": "harmony"},
    "Square":         {"angle": 90,  "orb": 7,  "quality": "tension"},
    "Sextile":        {"angle": 60,  "orb": 5,  "quality": "opportunity"},
    "Quincunx":       {"angle": 150, "orb": 3,  "quality": "adjustment"},
    "Semi-sextile":   {"angle": 30,  "orb": 2,  "quality": "minor growth"},
    "Semi-square":    {"angle": 45,  "orb": 2,  "quality": "friction"},
    "Sesquisquare":   {"angle": 135, "orb": 2,  "quality": "agitation"},
    "Quintile":       {"angle": 72,  "orb": 1.5,"quality": "creative"},
    "Bi-Quintile":    {"angle": 144, "orb": 1.5,"quality": "creative"},
}
```

### Dignity Hierarchy Constants

```python
DOMICILE    = {"Aries": "Mars", "Taurus": "Venus", ...}        # sign → ruling planet
EXALTATION  = {"Aries": "Sun",  "Taurus": "Moon",  ...}        # sign → exalted planet
EXALT_DEG   = {"Sun": 19, "Moon": 3, "Mercury": 15, ...}       # exact exaltation degree
FALL        = {...}   # opposite of exaltation
DETRIMENT   = {...}   # opposite of domicile
TERMS       = {...}   # Egyptian terms (5 rulers per sign, by degree range)
DECANS      = {...}   # Chaldean decans (3 per sign, 10° each)
TRIPLICITY  = {...}   # fire/earth/air/water with day/night/participating rulers
```

### Norse Correspondence Constants

```python
NORSE_CORRESPONDENCES = {
    "Sun":     {"god": "Sól",   "world": "Ásgard",   "keyword": "the burning road"},
    "Moon":    {"god": "Máni",  "world": "Ásgard",   "keyword": "the measurer"},
    ...
}

SIGN_RUNES = {
    "Aries":       {"rune": "Tiwaz",  "symbol": "ᛏ", "meaning": "victory, sacrifice"},
    "Taurus":      {"rune": "Fehu",   "symbol": "ᚠ", "meaning": "wealth, cattle, luck"},
    ...
}
```

---

## Core Engine Functions

### `calc_planet_positions(jd, tropical=True)`

Loops through `PLANETS` dict calling `swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)`. Returns the planet position dict described above.

S.Node is computed as `N.Node longitude + 180° mod 360`.

### `calc_houses(jd, lat, lon, system=b"P")`

Calls `swe.houses(jd, lat, lon, system)`. Returns `(cusps_list_12, asc, mc)`.

**Important:** `swe.houses()` returns a tuple `(cusps_tuple_12, angles_tuple_10)`. The cusps tuple is 0-indexed, 12 elements (houses 1–12). The engine returns `list(cusps)` — 0-indexed, so `cusps[0]` = House 1.

House system codes: `b"P"` = Placidus (default), `b"W"` = Whole Sign, `b"K"` = Koch, `b"E"` = Equal.

### `planet_house(planet_lon, cusps)`

Returns 1–12 by checking which cusp bracket the longitude falls in, with wrap-around logic for the 12th→1st house boundary.

### `calc_aspects(positions, luminaries=("Sun","Moon"))`

Iterates all unique planet pairs. For each pair and each aspect, checks if `abs(angle_diff(lon_a, lon_b) - aspect_angle) <= orb`. Applying/separating detection: a planet is *applying* to an aspect if its speed is moving it toward the exact angle.

---

## Geocoding Pipeline

### Function: `geocode_city(city, nation, lat_override, lon_override)`

```
Tier 1: lat_override AND lon_override both provided?
        → return (float(lat_override), float(lon_override))

Tier 2: geopy available?
        → Nominatim query: "city, nation" (or just "city")
        → 6-second timeout, single attempt
        → returns (lat, lon) if found

Tier 3: kerykeion available?
        → AstrologicalSubject("_", "probe", city, nation)
        → extracts .lat/.lng from result
        → logging disabled around this call (kerykeion is verbose)

Tier 4: GEOCODING_FALLBACK dict
        → ~70 hardcoded entries: major world cities + Indiana cities + Nordic capitals
        → key format: "city,nation" lowercase or just "city"

Fallback failure:
        → print warning to stderr
        → return (0.0, 0.0)
```

### Adding Cities to Fallback

Find `GEOCODING_FALLBACK` dict in `astrology_engine.py` (~line 555). Add entries as:

```python
"city name,CC": (lat, lon),   # CC = ISO country code
# or for US cities without ambiguity:
"city name": (lat, lon),
```

---

## Timezone Resolution

### `resolve_timezone(lat, lon) -> str | None`

```python
tf = _tzf()   # lazy TimezoneFinder singleton
if tf is None:
    return None
return tf.timezone_at(lng=float(lon), lat=float(lat))
```

Returns IANA timezone string like `"America/Indiana/Indianapolis"` or `None`.

### `local_to_utc(year, month, day, local_hour, tz_name) -> (float, str)`

```python
tz = pytz.timezone(tz_name)
local_dt = datetime(year, month, day, int(h), int(m))

# First try: DST-ambiguity safe
try:
    aware = tz.localize(local_dt, is_dst=None)
except AmbiguousTimeError:
    aware = tz.localize(local_dt, is_dst=False)   # standard time wins

utc_dt = aware.astimezone(pytz.utc)
offset_str = "UTC" + format_offset(aware.utcoffset())
return utc_dt.hour + utc_dt.minute/60 + utc_dt.second/3600, offset_str
```

`is_dst=None` is intentional — it raises rather than silently guessing on clocks-back ambiguity. The fallback `is_dst=False` always picks standard time, which is correct for birth records (hospitals document clock time, not DST intent).

---

## The `resolve_birth` Function

**This is the canonical entry point for all location+time resolution.** Every command handler should call this.

```python
def resolve_birth(date_str, time_str, city, nation="",
                  lat_override=None, lon_override=None):
    """
    Returns:
        year, month, day   : int
        utc_hour           : float  (for julian_day())
        lat, lon           : float  (geocoded coordinates)
        tz_name            : str | None  (IANA tz, e.g. "America/New_York")
        tz_label           : str  (human display, e.g. "14:30 LT → 19:30 UTC (UTC-05:00 ...)")
        time_known         : bool  (False if time_str was None → noon was used)
    """
```

### Command Handler Template

```python
def cmd_mycommand(args):
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd = julian_day(y, mo, d, utc_hour)
    # ... use jd, lat, lon for all calculations
```

---

## Subcommand Handler Pattern

All 16 handlers follow the same structure:

```python
def cmd_name(args):
    # 1. Resolve birth data
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known = resolve_birth(...)
    jd = julian_day(y, mo, d, utc_hour)

    # 2. Calculate positions
    positions = calc_planet_positions(jd)
    cusps, asc, mc = calc_houses(jd, lat, lon)

    # 3. Print header
    header("SUBCOMMAND TITLE", f"{args.name}  ·  {args.date}  ·  {tz_label}")

    # 4. Derived calculations + print sections
    section("SECTION TITLE")
    # ... print rows

    # 5. Norse layer (if applicable)
    print_norse_layer(positions)
```

### Adding a New Subcommand (Checklist)

1. Write `def cmd_mycommand(args):` following the template above
2. Add the subparser in `main()`:
   ```python
   my_p = sub.add_parser("mycommand", help="Short description")
   my_p.add_argument("--date", required=True)
   my_p.add_argument("--time", default=None)
   add_geo(my_p)   # adds --city, --nation, --lat, --lon
   # add any custom args
   ```
3. Add to the dispatch dict in `main()`:
   ```python
   "mycommand": cmd_mycommand,
   ```
4. Update the module docstring at the top of the file
5. Update `SKILL.md` with the new mode
6. Update `COMMANDS.md` with full flag documentation
7. Update `CHANGELOG.md`

---

## Aspect Engine

### `calc_aspects(positions, luminaries)`

Returns a list of dicts:

```python
[
    {
        "planet1": "Sun",
        "planet2": "Moon",
        "aspect":  "Trine",
        "glyph":   "△",
        "orb":     2.34,
        "quality": "harmony",
        "applying": True,
    },
    ...
]
```

Aspects are sorted by orb (tightest first). The `luminaries` parameter widens orbs for Sun and Moon (traditional rule: luminaries get extra orb).

### Orb widening for luminaries

When either planet is a luminary, orbs are widened by 2°. This is baked into the `ASPECTS` dict values — if you want to change orb policy, adjust `ASPECTS` or modify the orb check logic in `calc_aspects()`.

---

## Dignity Engine

### `essential_dignity(planet, sign, degree) -> dict`

Returns:

```python
{
    "domicile":    True/False,
    "detriment":   True/False,
    "exaltation":  True/False,
    "exact_exalt": True/False,  # within 1° of exact exaltation degree
    "fall":        True/False,
    "triplicity":  "primary"/"secondary"/"participating"/None,
    "term":        True/False,
    "face":        True/False,
    "peregrine":   True/False,
    "score":       int,         # net dignity score
    "ruler":       "Venus",     # planet that rules this position
}
```

Score thresholds: `+5` (domicile) down to `−5` (detriment). Peregrine = 0 (no dignity or debility).

---

## Event Prediction Engine

### `find_exact_transit_dates(natal_pos, start_jd, end_jd, t_planets, n_planets, step)`

**Algorithm:**

1. Scan `start_jd` to `end_jd` in `step`-day increments (0.5 for inner planets, 1.0 for outer)
2. At each step, compute transit planet longitude
3. Compute angular distance to each natal point for each aspect
4. If `angle_diff` crosses zero between two steps (sign changes), a crossing exists
5. Bisect the interval 20 times (converges to ~0.01° precision) to find exact JD
6. Record `(jd_exact, transit_planet, aspect_name, glyph, natal_planet, quality)`

Step size matters: Moon transits require `step=0.1` or you can miss fast-moving crossings. The default is fine for outer planet work.

### `find_stations(start_jd, end_jd, step=1.0)`

Scans for speed sign changes (positive → negative = retrograde station, negative → positive = direct station). Uses a 0.1-day refinement window around the station point.

### `find_ingresses(start_jd, end_jd, planets, step=1.0)`

Detects `sign_idx` integer crossing between two adjacent JD steps. Records `(jd, planet, from_sign, into_sign)`.

### `find_eclipses(start_jd, end_jd)`

Uses `swe.sol_eclipse_when_glob()` and `swe.lun_eclipse_when()` if available. Falls back to a geometric Sun/Moon/Earth alignment scan if not.

---

## Astrocartography Engine

### `calc_astrocartography(jd, positions) -> dict`

For each planet:

**MC line** — Earth longitude where planet's Right Ascension equals the Greenwich Sidereal Time:

```
GMST(jd) = Greenwich Mean Sidereal Time (degrees)
RA(planet) = Right Ascension converted from ecliptic lon/lat
MC_lon = RA - GMST   (normalised to ±180°)
IC_lon = MC_lon + 180° (or − 180°)
```

**ASC lines** — latitudes sampled every 5°, longitude solved from the horizon condition:

```
cos(H) = -tan(φ) · tan(δ)   where φ=latitude, δ=declination
if |cos(H)| > 1: planet circumpolar or never rises at this latitude → skip
H = arccos(cos(H))
ASC_lon = RA - H - GMST
DSC_lon = RA + H - GMST
```

Helper functions:
- `_obliquity(jd)` → ecliptic obliquity
- `_ecl_to_eq(lon, lat, eps)` → (RA, Dec) from ecliptic coordinates
- `_gmst(jd)` → Greenwich Mean Sidereal Time in degrees
- `geo_region(lon)` → approximate region name string from longitude

---

## Output Formatting Conventions

All output uses Unicode box-drawing characters. Helper functions:

```python
W = 76  # global output width constant

def hr(char="─"):
    """Print a full-width horizontal rule."""

def header(title, subtitle=None):
    """╔══ TITLE ══╗ / ║ subtitle ║ / ╚══════════╝"""

def section(title):
    """┌─ SECTION TITLE ─────────────────────────────┐"""

def wrap_print(text, indent=4):
    """Word-wrap text to W columns with indent."""
```

Planet symbols are in `PLANET_SYMBOL` dict. Sign symbols in `SIGN_SYMBOL` list indexed by sign index (0=Aries).

---

## Lazy Backend Singletons

The geocoding and timezone backends are expensive to initialise. They use the lazy singleton pattern:

```python
_nominatim = None;  _GEO_AVAIL = None
_tf        = None;  _TZ_AVAIL  = None

def _geo():
    """Returns Nominatim instance or None."""
    global _nominatim, _GEO_AVAIL
    if _GEO_AVAIL is None:
        try:
            from geopy.geocoders import Nominatim
            _nominatim = Nominatim(user_agent="volmarr_astrology_engine/3.0", timeout=6)
            _GEO_AVAIL = True
        except Exception:
            _GEO_AVAIL = False
    return _nominatim if _GEO_AVAIL else None
```

`_GEO_AVAIL = None` means "not yet checked". After the first call it is `True` or `False` and the import never runs again. This means: importing the module is fast; the geo/tz libraries only load on first geocoding call.

---

## Known Architecture Limitations

| Area | Limitation | Notes |
|------|-----------|-------|
| Sidereal zodiac | Not exposed via CLI | `tropical=False` can be passed to `calc_planet_positions` internally; no `--sidereal` flag yet |
| Moon VOC | Checks aspects within current sign only | Does not scan all remaining degrees to next ingress exhaustively; accurate enough for timing but not ephemeris-grade |
| Solar return convergence | 50 iterations max, `diff/360` delta | Can be slow or slightly imprecise within 2 days of year boundary edge case |
| Progressions | Uses mean tropical year (365.25 days) | Conventional approximation; Naibod arc would require `swe.sol_eclipse_when_glob` for solar arc |
| `predict` step size | 1.0 day default for outer planets | Can miss short-window events for fast-moving transiting inner planets; set `step=0.25` for Mercury |
| Nominatim rate limit | 1 request/second OSM policy | Single-call, 6-second timeout. No retry loop. City caching not implemented (kerykeion's cache only) |
| Pyright warnings | `swe` and `AstrologicalSubject` flagged as "possibly unbound" | False positives — both are guarded by `SWE`/`KK` runtime checks. Not real errors. |

---

*Read the code; read the wyrd.*
