# Astrology Engine — Gaps & Integration Notes

## Known Gaps (as of 2026-05-03)

### 1. Missing CLI Subcommands
Two engine modes exist as functions but have **no argparse CLI subcommand**:

- **`dignity`** — `print_dignity_table()` exists but no `sub.add_parser("dignity")`. Only accessible inside `natal` and `hellenistic` output.
- **`antiscia`** — `calc_antiscia()` and `print_antiscia()` exist but no CLI subcommand. Only shown inside `natal`/`hellenistic`.

**Fix pattern** (follows `lots` subcommand):
```python
sub = subparsers.add_parser("dignity", help="Essential dignities table")
sub.add_argument("--date", required=True)
sub.add_argument("--time", default="12:00")
sub.add_argument("--city", default="London")
sub.add_argument("--nation", default="GB")
# ... add to dispatch dict
```

### 2. No Custom Transit Date
The `transit` mode always compares natal chart vs `datetime.utcnow()`. There is no `--transit-date` or `--transit-time` option to check transits for a specific past/future date.

**Fix**: Add `--transit-date` (YYYY-MM-DD) and `--transit-time` (HH:MM) optional args. Default to `None` → use `utcnow()`.

### 3. Limited Geocoding Fallback
Only 11 hardcoded cities in `GEOCODING_FALLBACK`. If kerykeion fails and the city isn't in the dict, lat/lon defaults to (0.0, 0.0) → nonsensical house cusps.

**Expanded city list** (recommended additions): Angola IN, Fort Wayne IN, Oslo NO, Stockholm SE, Copenhagen DK, Reykjavik IS, Helsinki FI, Dublin IE, Edinburgh UK, Berlin DE, Paris FR, Tokyo JP, Sydney AU, Los Angeles CA, Chicago IL, San Francisco CA, Seattle WA, Denver CO, Austin TX, Portland OR, Amsterdam NL.

### 4. Exaltation Degrees Unused
`EXALTATION_DEG` dict is defined (exact degrees of exaltation for each planet) but never referenced in dignity calculations. Adding it would show when a planet is at its exact exaltation degree (within ~1° orb) — a meaningful traditional detail.

### 5. VOC Detection is Approximate
Void-of-Course detection scans future Moon positions in 0.1° increments with 0.5° orb. This is a reasonable heuristic but not ephemeris-precise. Acknowledged as acceptable for general use.

### 6. Synastry Missing House Overlays
Synastry mode only shows cross-aspects. It doesn't show house overlays (e.g., "Person A's Sun falls in Person B's 5th house") — a standard synastry feature.

## Norse Correspondence Notes

The planet→god and sign→rune mappings are **modern syncretic associations**, not historically attested in Old Norse sources. This is fine for a personal occult system but should be presented as a "living tradition overlay" rather than historical reconstruction. Volmarr values authentic Norse sources — be clear about what's attested vs. what's modern interpretation.

## Integration Hooks

The SKILL.md describes Ørlög/WYRD Protocol integration points:
- Lot of Fortune → material wyrd
- Lot of Spirit → seiðr capacity  
- Sect light → solar/lunar channel

These are conceptual hooks only — no code-level integration with the WYRD Protocol ECS yet.

## Dependencies Status

| Dependency | Version | Status |
|-----------|---------|--------|
| `pyswipseph` | — | Installed, core engine |
| `kerykeion` | 5.12.7 | Installed, geocoding only |
| `argparse` | stdlib | — |
| `rich` | — | Console output |