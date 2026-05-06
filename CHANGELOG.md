# Changelog — Astrology Engine

All notable changes to `astrology_engine.py` and associated skill files.

Format: **Added** / **Changed** / **Fixed** / **Removed** for each version.

---

## [3.0.0] — 2026-05-03

### Added

- **Automatic worldwide geocoding** via `geopy` + Nominatim (OpenStreetMap). Any city on Earth can now be resolved without API keys. Previously limited to ~11 hardcoded cities.
- **Automatic timezone detection** via `timezonefinder`. IANA timezone is derived from coordinates; no manual timezone input required.
- **DST-aware UTC conversion** via `pytz`. `pytz.localize(is_dst=None)` raises on ambiguous DST boundaries (e.g. Indiana clocks-back) and falls back to standard time — handles all historical edge cases correctly.
- **`resolve_birth()` function** — single canonical entry point that combines geocoding + timezone + UTC conversion into one call. All command handlers updated to use this.
- **UTC label in all chart headers** — e.g. `14:30 LT → 19:30 UTC (UTC-05:00 America/Indiana/Indianapolis)`.
- **Lazy backend singletons** (`_geo()`, `_tzf()`) — Nominatim and TimezoneFinder only initialise on first use; no startup penalty when not needed.
- **`cmd_predict`** updated to use `resolve_birth` — birth location now correctly contributes UTC time for natal chart.
- **`cmd_geoastrology`** updated to use `resolve_birth` — `--city`/`--nation`/`--lat`/`--lon` args added to `geoastrology` subparser.
- **Geocoding fallback expanded** from ~11 cities to ~70 major world cities (Indiana, Nordic capitals, European capitals, US metros, Asia-Pacific).

### Changed

- All command handlers now use `resolve_birth()` instead of the old `parse_date_time() + geocode_city()` pattern. Affected handlers: `cmd_natal`, `cmd_transit`, `cmd_solar_return`, `cmd_progressions`, `cmd_lots`, `cmd_hellenistic`, `cmd_dignity`, `cmd_synastry`, `cmd_composite`, `cmd_synergy`, `cmd_predict`, `cmd_geoastrology`.
- Kerykeion geocoding demoted from primary to Tier 3 (behind Nominatim). Kerykeion's verbose GEONAMES warning is suppressed via `warnings.filterwarnings` and `logging.disable(logging.CRITICAL)` around the call.
- `geoastrology` header now includes full timezone label instead of raw time string.

### Fixed

- `IndexError: list index out of range` in `planet_house()` — `swe.houses()` returns exactly 12 elements (0-indexed); `cusps[1:]` was producing 11 elements. Fixed by returning `list(cusps)` not `list(cusps[1:])`.
- `ValueError: Invalid format specifier '>12+12'` in `cmd_geoastrology` header — f-string had invalid `{'>12+12'}` specifier. Fixed to use explicit padding.
- Transit header `sky_label` showing `"None UTC"` — `getattr(args, 'transit_time', '12:00')` returned `None`. Fixed: `ttime = getattr(args, "transit_time", None) or "12:00"`.
- Kerykeion WARNING spam on every geocoding call suppressed.

---

## [2.1.0] — 2026-05-03

### Added

- **`dignity` subcommand** — standalone essential dignities table with scoring and mutual receptions. Previously only accessible inside `natal` and `hellenistic` output.
- **`antiscia` subcommand** — standalone antiscia/contra-antiscia table with inter-planet connection detection. Previously only inside `natal`/`hellenistic`.
- **`--transit-date` / `--transit-time`** flags added to `transit` subcommand — enables forecasting against any past or future sky date, not just "now".
- **`--lat` / `--lon` override flags** added to all location-dependent subcommands (previously only `planet-hours` had them).
- **Exaltation degree scoring** — `EXALT_DEG` dict now used in `essential_dignity()` to flag when a planet is within 1° of its exact exaltation degree.
- **VOC detection rewrite** — changed from O(degrees × 10 × planets × aspects) step-scan to O(planets × 5 aspects × 2) exact aspect targeting. Significantly faster and more accurate.
- **Synastry house overlays** — when `--city1`/`--city2` are both provided, synastry mode shows "Person A's Sun in Person B's 5th house"-style overlays.
- **Geocoding fallback expanded** from 11 to ~60 cities including major Nordic, European, and US locations.

### Changed

- `add_geo()` helper function added to `main()` — DRY pattern for adding `--city`/`--nation`/`--lat`/`--lon` to any subparser.
- Aspect engine applying/separating detection improved.

---

## [2.0.0] — 2026-05-03

### Added

- **`synergy` subcommand** — full relationship analysis: harmony/challenge score bar, weighted cross-aspect breakdown, composite chart, composite dignities, cross-midpoints.
- **`predict` subcommand** — event prediction engine: exact transit-to-natal aspect dates (bisection to 0.01°), retrograde/direct stations, sign ingresses, eclipses — all within a user-specified window.
- **`geoastrology` subcommand** — astrocartography: MC/IC lines (exact Earth longitude where planet culminates), ASC/DSC lines sampled every 5° of latitude, power-spot analysis for any coordinates.
- **`composite` subcommand** — composite chart by midpoint method; optional Davison relationship chart when both birth cities are provided.
- **`synergy_score()` function** — weighted aspect scoring: trines/sextiles +harmony, squares/oppositions +challenge, conjunctions split by planet type. Outputs `%` bar.
- **`find_exact_transit_dates()` function** — bisection algorithm scans transit-to-natal aspect crossings and converges to 0.01° in 20 iterations.
- **`find_stations()` function** — detects retrograde/direct stations by speed sign change.
- **`find_ingresses()` function** — detects sign boundary crossings for all planets.
- **`find_eclipses()` function** — uses `swe.sol_eclipse_when_glob()` / `swe.lun_eclipse_when()` or geometric fallback.
- **`calc_astrocartography()` function** — first-principles MC/IC via RA-GMST, ASC/DSC via `cos(H) = -tan(φ)·tan(δ)`.
- **`calc_composite()` function** — shorter-arc midpoint composite.
- **`calc_davison()` function** — average Julian Day + average location Davison chart.
- **`calc_midpoints()` function** — all unique planet midpoints.

---

## [1.0.0] — 2026-05-03 (initial)

### Added

- Full natal chart: all planets + asteroids, Placidus houses, aspects (11 types), essential dignities (full Ptolemaic hierarchy including terms and faces), Arabic Lots (all 7), antiscia, Hellenistic analysis, Norse/Rune overlay, house overview.
- `transit` mode — transiting planets vs natal.
- `synastry` mode — cross-chart aspects with applying/separating.
- `solar-return` mode — iterative convergence to exact solar return moment.
- `progressions` mode — secondary progressions with tight-orb aspects.
- `lunar` mode — phase, illumination, void-of-course, next New/Full Moon.
- `planet-hours` mode — Chaldean hours with Norse deity layer.
- `lots` mode — standalone Arabic Lots output.
- `hellenistic` mode — sect, joys, triplicity rulers, mutual receptions, stelliums.
- `aspect-grid` mode — full N×N aspect matrix.
- Swiss Ephemeris (`pyswisseph`) for all positions — no lookup tables.
- Elder Futhark rune overlays on all 12 signs.
- Norse deity correspondences for all 11 planets.
- Essential dignities: domicile, exaltation, fall, detriment, triplicity (Ptolemaic), Egyptian terms, Chaldean decans.
- Void-of-course Moon detection.
- Day/night chart (sect) detection.
- `kerykeion` geocoding integration with SQLite cache.

---

*Each version a layer of wyrd laid down in the loom.*
