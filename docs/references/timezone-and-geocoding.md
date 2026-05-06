# Timezone Conversion & Geocoding Reference

## Timezone Handling (as of May 2025)

The engine now **auto-converts local time → UTC** using `timezonefinder` + `pytz`:

1. `geocode_city()` resolves the city to `(lat, lon, city_resolved)`
2. `resolve_timezone(lat, lon)` uses `timezonefinder` to get IANA timezone (e.g., `America/Indiana/Indianapolis`)
3. `local_to_utc()` applies the timezone offset and DST rules for the date
4. The natal chart header displays the conversion: `14:30 LT → 19:30 UTC (UTC-05:00 EST)`

**When auto-conversion works:** Any city in the fallback table or resolved by Nominatim/GeoNames.

**When it fails / falls back to UTC:**
- Unknown city → 0°N 0°E → timezonefinder returns None → input treated as UTC with warning
- No internet → Nominatim and GeoNames fail → fallback table only → timezone from fallback coords
- Historical dates before timezonefinder's database (pre-1900) → may be inaccurate

**Manual UTC conversion table** (fallback for when auto-conversion is unavailable):

| Timezone | Offset | Example Local | UTC Time |
|----------|--------|---------------|----------|
| EST      | +5     | 8:18 AM EST   | 13:18    |
| EDT      | +4     | 8:18 AM EDT   | 12:18    |
| CST      | +6     | 8:18 AM CST   | 14:18    |
| CDT      | +5     | 8:18 AM CDT   | 13:18    |
| MST      | +7     | 8:18 AM MST   | 15:18    |
| MDT      | +6     | 8:18 AM MDT   | 14:18    |
| PST      | +8     | 8:18 AM PST   | 16:18    |
| PDT      | +7     | 8:18 AM PDT   | 15:18    |

**DST dates for 1972:** DST started April 30, ended October 29.
**Rule of thumb:** Verify with https://timeanddate.com for historical timezone data.

## Geocoding — Priority Chain

| Priority | Source | Works Offline? | Accuracy |
|----------|--------|---------------|----------|
| 1 | Explicit `--lat`/`--lon` | ✅ | Perfect |
| 2 | Nominatim (OSM) | ❌ Needs internet | High |
| 3 | kerykeion GeoNames | ❌ Needs internet | High (rate-limited) |
| 4 | Hardcoded fallback (~120+ cities) | ✅ | Exact for known cities |
| 5 | Default 0°N 0°E | ✅ | Useless — warns on stderr |

**`geocode_city()` returns `(lat, lon, city_resolved)`:**
- `city_resolved=True` → city was actually matched (Nominatim, GeoNames, or fallback table)
- `city_resolved=False` → coords were explicitly provided OR fell back to 0°N 0°E

**`resolve_birth()` returns 10 values:**
```python
y, mo, d, utc_hour, lat, lon, tz_name, tz_label, time_known, city_default_used = resolve_birth(...)
```
- `city_default_used=True` → city was NOT resolved, using default coords (bad!)
- `time_known=False` → birth time was not provided, noon was used

## Key Coordinates (Verified)

| City | Latitude | Longitude |
|------|----------|-----------|
| Schenectady, NY | 42.7603 | -73.9334 |
| Indianapolis, IN | 39.7684 | -86.1581 |
| Angola, IN | 41.6337 | -84.9994 |
| Fort Wayne, IN | 41.0793 | -85.1394 |
| London, UK | 51.5074 | -0.1278 |
| Oslo, Norway | 59.9139 | 10.7522 |
| Stockholm, Sweden | 59.3293 | 18.0686 |
| Copenhagen, Denmark | 55.6761 | 12.5683 |

## Safe Invocation Pattern

```bash
# Recommended: let auto-conversion handle timezone
python3 /home/pi/.hermes/skills/divination/astrology/astrology_engine.py \
  natal --date 1972-09-01 --time 08:18 \
  --city "Schenectady" --nation US --name Volmarr

# Fallback: explicit coords + manual UTC for reliability
python3 /home/pi/.hermes/skills/divination/astrology/astrology_engine.py \
  natal --date 1972-09-01 --time 12:18 \
  --lat 42.7603 --lon -73.9334 --name Volmarr
```

## GeoNames Rate Limiting

kerykeion uses GeoNames API with shared free credentials. When rate-limited:
- Throws: `KerykeionException: Missing data from geonames`
- Solution: Use `--lat/--lon` to bypass geocoding entirely
- Free personal account: https://www.geonames.org/login

## Bug Fix History

### May 2025 — Geocoding & Return Signature Overhaul
- **`geocode_city()`**: Changed return from 2-tuple `(lat, lon)` to 3-tuple `(lat, lon, city_resolved)` for tracking whether city was actually matched
- **`resolve_birth()`**: Added 10th return value `city_default_used` (True = city unresolved, using default)
- **All 14 callers of `resolve_birth()`** updated to unpack 10 values
- **All 6 direct callers of `geocode_city()`** updated to unpack 3 values
- **`cmd_natal`**: Fixed broken `lat_override` reference → `getattr(args, "lat", None)`
- **CITIES dict**: Fixed IndentationError caused by misplaced `result = CITIES.get(...)` line before dict literal (patch tool inserted code at wrong position)
- **Coordinate display**: Changed from negative-degree notation to N/S/E/W suffix notation

### Pitfall: Patching Large Python Files
The `astrology_engine.py` file is ~2900 lines. The Hermes patch tool operates on string matching. **Critical gotchas:**
- Always `read_file` the target area before patching — the tool warns if you last used offset/limit pagination
- Never insert code before a dict literal (Python will see it as a statement before `{`, breaking indentation)
- After any patch, always verify with: `python3 -c "import py_compile; py_compile.compile('astrology_engine.py', doraise=True)"`
- When changing a function's return type, search for ALL callers with `search_files` before updating
- Use `replace_all=true` for mechanical same-pattern changes across multiple lines

## Volmarr's Verified Chart (Sept 1, 1972, 8:18 AM EDT, Schenectady NY)

- **ASC: Libra 1°01'** ✓ (confirmed by Volmarr)
- **MC: Cancer 1°12'**
- **Sect: Nocturnal** (Sun below horizon at 12:18 UTC for this latitude)
- Key: Auto-conversion handles EDT → UTC. Manual fallback: UTC time is 12:18