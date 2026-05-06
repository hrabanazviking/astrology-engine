# Contributing & Extending the Astrology Engine

> Guide for vibe coding new features, subcommands, and technique improvements.

This document assumes you've read [ARCHITECTURE.md](ARCHITECTURE.md) and understand the basic data flow. The engine is designed to be extended in layers — you can add a subcommand, extend a mapping, or drop in a new calculation without touching unrelated code.

---

## Contents

- [Before You Change Anything](#before-you-change-anything)
- [Adding a New Subcommand](#adding-a-new-subcommand)
- [Adding Cities to the Geocoding Fallback](#adding-cities-to-the-geocoding-fallback)
- [Extending Norse Correspondences](#extending-norse-correspondences)
- [Adding Rune-Sign Mappings](#adding-rune-sign-mappings)
- [Extending the Dignity System](#extending-the-dignity-system)
- [Adding New Aspect Types](#adding-new-aspect-types)
- [Improving VOC Detection](#improving-voc-detection)
- [Adding a New Lot (Arabic Part)](#adding-a-new-lot-arabic-part)
- [Working with Secondary Progressions](#working-with-secondary-progressions)
- [Debugging Tips](#debugging-tips)
- [Testing](#testing)
- [Style Rules](#style-rules)

---

## Before You Change Anything

1. **Read the section you're touching** with the `Read` tool before editing. The engine is ~2850 lines; changes in the wrong place can cascade.
2. **Run the smoke test** before and after your change:
   ```bash
   python3 astrology_engine.py natal --date 1975-11-22 --time 14:30 \
     --city Indianapolis --nation US --name Volmarr
   ```
   Verify: Sun in Scorpio, Moon in Cancer, Rising Pisces, `14:30 LT → 19:30 UTC`.
3. **Don't use pseudocode in the engine.** The rule is full working code only.
4. **Don't break the geocoding pipeline.** Every command handler must call `resolve_birth()`, not the old `parse_date_time()` + `geocode_city()` pattern.

---

## Adding a New Subcommand

The pattern is consistent across all 16 existing commands. Follow it exactly.

### Step 1 — Write the handler function

Place it in the command handler section (after `cmd_geoastrology`, before `def main()`):

```python
def cmd_mymode(args):
    """One-line description for the docstring."""
    # 1. Resolve birth
    y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known = resolve_birth(
        args.date, args.time, args.city, args.nation,
        getattr(args, "lat", None), getattr(args, "lon", None)
    )
    jd = julian_day(y, mo, d, utc_hour)

    # 2. Calculate base positions
    positions = calc_planet_positions(jd)
    cusps, asc, mc = calc_houses(jd, lat, lon)

    name = getattr(args, "name", None) or "Seeker"

    # 3. Header
    header("MY MODE TITLE", f"{name}  ·  {args.date}  ·  {tz_label}")

    # 4. Your calculations
    section("SECTION ONE")
    for planet, data in positions.items():
        sign = data["sign"]
        # ... print your rows
    print()

    # 5. Norse layer if applicable
    print_norse_layer(positions)
```

### Step 2 — Add the subparser in `main()`

Inside `def main()`, after the last `sub.add_parser(...)` block and before the dispatch dict:

```python
# mymode
my_p = sub.add_parser("mymode", help="Short description shown in --help")
my_p.add_argument("--date", required=True)
my_p.add_argument("--time", default=None)
my_p.add_argument("--name", default=None)
add_geo(my_p)   # adds --city, --nation, --lat, --lon
# any custom args:
my_p.add_argument("--myflag", default=None, help="Description")
```

### Step 3 — Register in dispatch dict

```python
dispatch = {
    ...
    "mymode": cmd_mymode,   # add here
}
```

### Step 4 — Update documentation

- Add mode to module docstring (lines 8–21)
- Add to `SKILL.md` Modes section
- Add full flag documentation to `COMMANDS.md`
- Add to `CHANGELOG.md` under the appropriate version

---

## Adding Cities to the Geocoding Fallback

Find `GEOCODING_FALLBACK` dict (~line 555 in `astrology_engine.py`). Add entries as:

```python
GEOCODING_FALLBACK = {
    # Format: "city,CC": (lat, lon)
    "reykjavik,is":   (64.1355, -21.8954),
    "anchorage,us":   (61.2181, -149.9003),
    # US cities can omit ",us" if unambiguous:
    "bend":           (44.0582, -121.3153),
}
```

Key rules:
- Keys are **lowercase** with no extra spaces
- Latitude: positive = North, negative = South
- Longitude: positive = East, negative = West
- Coordinates from [latlong.net](https://www.latlong.net) or `nominatim.openstreetmap.org`

**Note:** Nominatim resolves any world city automatically when the Pi has internet. The fallback only matters when offline or for cities that Nominatim struggles with (very small towns, historical names). Prioritise Nordic capitals, common US cities, and any cities Volmarr's users actually ask about.

---

## Extending Norse Correspondences

### Planet correspondences

`NORSE_CORRESPONDENCES` dict (~line 270):

```python
NORSE_CORRESPONDENCES = {
    "Sun": {
        "god":     "Sól",
        "world":   "Ásgard",
        "keyword": "the burning road",
        "rune":    "Sowilō ᛊ",
    },
    # ...
}
```

To add a new body (e.g. Eris, Sedna, Vesta):
1. Add the planet to the `PLANETS` dict with its `swe` ID
2. Add it to `NORSE_CORRESPONDENCES`
3. Add a `PLANET_SYMBOL` entry
4. The rest of the engine picks it up automatically

### World-Nine mapping

The `world` field should be one of: `"Ásgard"`, `"Vanaheim"`, `"Midgard"`, `"Jotunheim"`, `"Niflheim"`, `"Muspelheim"`, `"Alfheim"`, `"Svartalfheim"`, `"Helheim"`. These map to PAD dimensions in the Ørlög system.

---

## Adding Rune-Sign Mappings

`SIGN_RUNES` dict (~line 290):

```python
SIGN_RUNES = {
    "Aries": {
        "rune":    "Tiwaz",
        "symbol":  "ᛏ",
        "meaning": "victory, justice, sacrifice",
        "galdr":   "tiwaz tiwaz tiwaz",
    },
    # ...
}
```

All 24 runes of the Elder Futhark are in the full grimoire at `references/`. Signs map to runes on a syncretic seasonal/elemental basis — see the grimoire for the full rationale.

---

## Extending the Dignity System

### Adding exact exaltation degree detection

`EXALT_DEG` is already defined but the `essential_dignity()` function checks `exact_exalt` via:

```python
if planet == EXALTATION.get(sign):
    exalt = True
    if EXALT_DEG.get(planet) is not None:
        exact_exalt = abs(degree - EXALT_DEG[planet]) <= 1.0
```

This flag is returned in the dignity dict. To surface it in output, modify `print_dignity_table()` to show a `★` marker when `exact_exalt` is True.

### Adding Dorothean triplicity

The current `TRIPLICITY` uses Ptolemaic rulers. Dorothean triplicity has different night/day assignments for some elements. To add it, define `TRIPLICITY_DOROTHEAN` and add a `--triplicity-system` flag to `dignity` and `hellenistic` subcommands.

### Adding Bonification and Maltreatment

Bonification: a planet is "bonified" when a benefic (Venus, Jupiter) applies a trine or sextile to it within orb. Maltreatment: a malefic (Mars, Saturn) applies a hard aspect. Add a `bonification_check(planet, aspects)` function that scans the aspects list for these conditions and returns a string tag.

---

## Adding New Aspect Types

The full aspect list is in `ASPECTS` dict. To add a new type:

```python
ASPECTS["Novile"] = {"angle": 40, "orb": 1.0, "quality": "spiritual gift"}
```

And add its glyph to `ASPECT_GLYPH` dict. The aspect engine will detect it automatically on the next run.

**Note on orbs:** Tighter orbs = fewer hits = cleaner output. For minor harmonics (novile, septile, etc.), keep orbs at 1.0° or less. The existing sesquisquare and quincunx use 2–3° orbs; anything tighter than that produces a lot of noise.

---

## Improving VOC Detection

Current implementation (`void_of_course()`, ~line 934):

```python
# For each major aspect type and each planet (not Moon):
# Compute exact JD when Moon forms that aspect
# Find minimum JD > now that is still within current sign
# The last such aspect before sign change = last aspect
```

The function currently targets exact crossing times using a bisection-like approach but doesn't scan all remaining degrees in the sign. For a more rigorous implementation:

1. Find the Moon's next sign ingress JD (scan forward until `sign_idx` changes)
2. For each other planet and each aspect type, find all crossing JDs between now and ingress
3. If zero crossings found → VOC
4. If crossings exist, return the latest one as "last aspect before ingress"

This would be ephemeris-grade but requires more compute. Acceptable for a background task; too slow for `lunar` mode (which is expected to return in <2 seconds).

---

## Adding a New Lot (Arabic Part)

`LOTS_FORMULAS` dict defines the formulas:

```python
LOTS_FORMULAS = {
    "Fortune": {
        "day":   ("Asc", "+", "Moon", "-", "Sun"),
        "night": ("Asc", "+", "Sun",  "-", "Moon"),
    },
    # Add new lot here:
    "Basis": {
        "day":   ("Asc", "+", "Saturn", "-", "Moon"),
        "night": ("Asc", "+", "Moon",   "-", "Saturn"),
    },
}
```

`calc_lots()` reads this dict and computes all entries automatically. The new lot appears in `lots` output without any other changes.

For lots without a day/night reversal, use the same formula for both keys:

```python
"Daemon": {
    "day":   ("Asc", "+", "Sun", "-", "Mercury"),
    "night": ("Asc", "+", "Sun", "-", "Mercury"),
},
```

---

## Working with Secondary Progressions

Current progression uses mean tropical year (365.25 days/year):

```python
years_elapsed = (target_jd - natal_jd) / 365.25
prog_jd = natal_jd + years_elapsed
```

**To switch to Naibod arc** (more traditional, slightly more accurate):

1 degree of solar arc per year = 59'08" = 0.9856°/year

```python
# Solar arc method: Sun progresses exactly its mean daily motion (0.9856°/day)
# Each day after birth = 1 year of progressed time
# Difference in days = years_elapsed (same formula, different constant)
NAIBOD_ARC = 0.985647   # degrees per year of progression
```

The current implementation is conventional and accurate to within a few arc-minutes per decade. Only worth changing if clients are comparing progressed charts to other software at high precision.

---

## Debugging Tips

### Print a specific Julian Day

```python
python3 -c "
import swisseph as swe
jd = swe.julday(1975, 11, 22, 19.5)
print(jd)
print(swe.calc_ut(jd, swe.SUN)[0])   # Sun longitude
"
```

### Test geocoding in isolation

```python
python3 -c "
from geopy.geocoders import Nominatim
g = Nominatim(user_agent='test')
r = g.geocode('Reykjavik, Iceland')
print(r.latitude, r.longitude)
"
```

### Test timezone resolution

```python
python3 -c "
from timezonefinder import TimezoneFinder
tf = TimezoneFinder()
print(tf.timezone_at(lat=39.7683, lng=-86.1584))
# → America/Indiana/Indianapolis
"
```

### Verify a specific output

All chart output goes to stdout. Redirect to a file and diff against a known-good reference:

```bash
python3 astrology_engine.py natal \
  --date 1975-11-22 --time 14:30 --city Indianapolis --nation US \
  > /tmp/natal_test.txt

# Verify manually:
grep "Sun.*Scorpio 29" /tmp/natal_test.txt
grep "Moon.*Cancer 15" /tmp/natal_test.txt
grep "Rising.*Pisces" /tmp/natal_test.txt
grep "19:30 UTC" /tmp/natal_test.txt
```

---

## Testing

There is no automated test suite. Canonical verification chart:

**Volmarr Wyrd:** 1975-11-22, 14:30 local, Indianapolis IN US

| Point | Expected |
|-------|---------|
| Sun | Scorpio 29°52' |
| Moon | Cancer 15°51' |
| ASC | Pisces 25°44' |
| MC | Sagittarius 27°42' |
| Chart type | Night (nocturnal) |
| UTC conversion | 14:30 LT → 19:30 UTC (UTC-05:00) |
| Timezone | America/Indiana/Indianapolis |

After any change to `calc_planet_positions`, `calc_houses`, `julian_day`, `resolve_birth`, or `local_to_utc`, run the natal command and verify this table.

---

## Style Rules

- **No pseudocode.** If you're not sure how to implement something, leave a `# TODO: implement X` comment and come back to it.
- **Full working code only.** No stubs, no `pass` bodies, no placeholder returns.
- **Additive fixes only.** Don't delete existing working logic to replace it. Add alongside, validate, then remove the old path.
- **No docstrings on functions you didn't write.** Don't add docstrings or type annotations to existing functions just because you touched nearby code.
- **Constants at the top.** New data tables belong in the constants section, not inside functions.
- **`resolve_birth()` is mandatory.** Never call `parse_date_time()` + `geocode_city()` directly in a command handler. Use `resolve_birth()` for all birth data resolution.
- **Output width is W=76.** Don't exceed this in header/section labels. Use `wrap_print()` for long prose.
- **Preserve the Norse frame.** Every significant output section should have or be compatible with a Norse layer call.

---

*Forge well. The wyrd you weave here runs forward.*
