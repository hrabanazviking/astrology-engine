# Astrology Engine — Review & Known Gaps

_Session: 2026-05-03 deep review via sub-agent_

## Confirmed Working

- All 9 CLI modes function correctly: natal, transit, synastry, solar-return, progressions, lunar, planet-hours, lots, hellenistic, aspect-grid
- Swiss Ephemeris (`pyswisseph`) produces accurate planetary positions
- kerykeion geocoding works for major cities (with SQLite cache at `cache/kerykeion_geonames_cache.sqlite`)
- Norse/Rune overlay deeply integrated across all modes, not bolted on
- Essential dignity calculations (domicile, detriment, exaltation, fall, triplicity, terms, face) verified
- Arabic Lots computed correctly (all 7 traditional Lots)
- Antiscia computed within natal/hellenistic output

## Gaps & Missing CLI Commands

### `dignity` mode — no CLI subcommand
- `print_dignity_table()` function exists in the engine
- Module docstring lists `dignity` as a mode
- **No `sub.add_parser("dignity")`** and no `cmd_dignity` dispatch entry
- Currently only accessible as part of `natal` and `hellenistic` output
- **Fix:** Add argparse subcommand + dispatch entry mirroring other modes

### `antiscia` mode — no CLI subcommand
- `calc_antiscia()` and `print_antiscia()` exist in the engine
- **No CLI subcommand** for standalone use
- Only appears within `natal`/`hellenistic` output
- **Fix:** Add argparse subcommand + dispatch entry

### No custom transit date
- `transit` mode always compares natal chart vs "now" (UTC)
- Cannot check transits for a specific past/future date
- **Fix:** Add `--transit-date YYYY-MM-DD` option to transit subcommand

### Limited geocoding fallback
- Only 11 hardcoded cities in the fallback dictionary
- If kerykeion fails and city isn't in the dict, lat/lon defaults to (0.0, 0.0) — produces nonsensical house cusps for equatorial/prime meridian
- **Fix:** Expand fallback dict or add `--lat`/`--lon` override to all location-dependent modes (currently only `planet-hours` has it)

## Minor Observations

- `EXALTATION_DEG` dict defined but never used in dignity calculation (could add "exact exaltation degree" flag)
- VOC detection is approximate (0.1° step scanning, 0.5° orb) — acceptable for ritual timing but not ephemeris-grade
- Solar return uses iterative convergence (max 50 steps, `diff/360.0` delta) — works but could be fragile near year boundaries
- Secondary progressions use mean tropical year (365.25 days) — conventional approximation, not Naibod arc
- Synastry shows cross-aspects only, no house overlays ("Person A's Sun in Person B's 5th house")
- Transits use `datetime.datetime.utcnow()` — no timezone awareness
- Norse planet→god and sign→rune correspondences are modern syncretic, not historically documented — present as living tradition overlay, not historical reconstruction

## Priority Fixes

1. **Add `dignity` and `antiscia` CLI subcommands** (low effort, high value — functions already exist)
2. **Add `--transit-date` option** to transit mode (enables forecasting)
3. **Add `--lat`/`--lon` to all location-dependent modes** as kerykeion fallback override
4. **Expand geocoding fallback** to 20-30 major world cities