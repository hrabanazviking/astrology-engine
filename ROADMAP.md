# Roadmap — Astrology Engine

> Planned improvements, known gaps, and integration goals. Ordered roughly by value/effort ratio.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| `[done]` | Completed |
| `[next]` | High priority, low effort — pick up first |
| `[soon]` | Worth doing, moderate effort |
| `[later]` | Good idea, higher effort or lower urgency |
| `[wontfix]` | Acknowledged limitation, not worth fixing |

---

## Core Engine

### Calculation Quality

- `[next]` **Exact exaltation degree marker in `dignity` output** — `EXALT_DEG` is defined and the flag is computed; just needs a `★` glyph in `print_dignity_table()` when `exact_exalt=True`.

- `[next]` **Moon in `predict` mode** — default step size (1.0 day) misses Moon transits. Add auto-detection: if "Moon" is in `--transit-planets`, set `step=0.1` automatically.

- `[soon]` **Naibod arc progressions** — optional `--method naibod` flag for `progressions` subcommand. Current mean-tropical-year approximation (365.25) is close but not what specialist software uses. Naibod arc = 0.985647°/year.

- `[soon]` **Robust VOC Moon** — current detection checks aspects within the current sign but doesn't exhaustively scan all remaining degrees. Rewrite as: find next ingress JD, then scan for all aspect crossings between now and ingress JD. Return `True` if zero found. Accurate to minute.

- `[soon]` **Solar arc directions** — separate from progressions. Solar arc direction moves all planets at the Sun's progressed speed. Useful for event timing alongside secondaries.

- `[later]` **Primary directions** — classical Ptolemaic directions. Significant compute; requires `swe.time_equ()` for accurate poles. Highest value for traditional/Hellenistic clients.

- `[later]` **Tertiary progressions** — 1 day = 1 lunar month. Less commonly used but completing the progression suite.

- `[later]` **Firdaria periods** — Hellenistic time-lord technique. Day chart: Sun → Venus → Mercury → Moon → Saturn → Jupiter → Mars. Each planet rules a set number of years. Low effort to add as a `cmd_firdaria` subcommand.

- `[wontfix]` **Solar return convergence edge case near year boundary** — 50-iteration convergence can be slightly slow within 2 days of year boundary. Not meaningfully imprecise for practical use; fixing requires root-finding redesign.

---

## Geocoding & Timezone

- `[next]` **Nominatim caching** — currently every new city requires a live Nominatim call. A simple `dict`-based in-process cache (city string → lat/lon) would make repeated calls instantaneous and reduce OSM load. Optional SQLite persistence to survive restarts.

- `[next]` **Expand hardcoded fallback** — add: Anchorage, Honolulu, São Paulo, Buenos Aires, Cairo, Lagos, Nairobi, Mumbai, Beijing, Shanghai, Seoul, Mexico City, Bogotá, Lima. These cover the most common geocoding misses when offline.

- `[soon]` **Historical timezone data** — `pytz` handles most cases correctly via Olson database, but some pre-1970 timezone data is incomplete for certain regions. Document known edge cases (e.g. China used UTC+8 uniformly only after 1949; India uses UTC+5:30 year-round with no DST).

- `[later]` **Offline-first geocoding** — bundle a small SQLite of 10,000 major world cities (lat/lon/tz) so the engine works fully offline without kerykeion. File size ~2–3 MB. Would replace Tiers 2+3 in the cascade.

---

## New Subcommands / Modes

- `[next]` **`firdaria` subcommand** — time-lord periods. Requires only the sect light detection already implemented. Add `FIRDARIA_SEQUENCE_DAY` and `FIRDARIA_SEQUENCE_NIGHT` dicts with year counts, then compute current period from years elapsed since birth.

- `[next]` **`midpoints` subcommand** — `calc_midpoints()` already exists. Just needs a `cmd_midpoints` handler and subparser. Shows all planet midpoints, their signs/degrees, and which natal planets are within 1° of a midpoint (sensitive midpoints).

- `[soon]` **`eclipse-map` subcommand** — given an eclipse date, show which natal planets fall within 3° of the eclipse degree. Flag as activating if transit or progression also hits within 6 months. Uses existing `find_eclipses()`.

- `[soon]` **`return-chart` subcommand** — generalise `solar-return` to any planet return (lunar return, Mars return, Jupiter return). Lunar returns happen monthly and are excellent for monthly forecasting. Core logic is the same as solar return: iterate to find the moment a planet's longitude matches its natal degree.

- `[later]` **`bonification` subcommand** — show which planets are bonified (benefic trine/sextile from Venus or Jupiter) or afflicted (malefic conjunction/square/opposition from Mars or Saturn). Classic Hellenistic assessment beyond just dignity.

- `[later]` **`profections` subcommand** — annual profections time-lord system. Year 1 = House 1 is activated; year 13 = House 1 again. Each house = 30° = 1 sign progression per year from ASC. The activated house's ruling planet becomes the Lord of the Year. Requires only birth year and ASC sign.

- `[later]` **`sect-chart` subcommand** — full sect analysis showing which planets are in-sect (aligned with chart type) vs out-of-sect, with traditional bonification scoring. Extends current `hellenistic` sect detection.

---

## Output & Formatting

- `[next]` **Color output flag** — `--color` / `--no-color` toggle using ANSI codes. Benefics (Venus, Jupiter) in green; malefics (Mars, Saturn) in red; luminaries in yellow; angular planets in bold. Terminal-only; pipe detection should auto-disable.

- `[next]` **JSON output flag** — `--json` outputs the full data structure as JSON instead of formatted text. Enables Hermes to parse positions programmatically for WYRD Protocol feeds without screen-scraping.

- `[soon]` **SVG/ASCII chart wheel** — simple circular chart wheel output for `natal` mode. Full ASCII art in terminal; optional SVG file output via `--svg path/to/output.svg`. Chart wheels are high value for visual presentations but moderate build effort.

- `[later]` **Markdown report output** — `--markdown` flag outputs a clean Markdown document suitable for saving to Obsidian, Hugo, or any notes system. Each section becomes a Markdown heading.

---

## WYRD Protocol Integration

- `[next]` **Natal data as JSON for Ørlög** — `natal --json` output should map directly to WYRD Protocol PAD dimensions. Sun longitude → Arousal axis weight; Moon longitude → Valence axis weight; ASC → Dominance axis. Document the mapping in this repo.

- `[soon]` **Transit trigger events** — `predict` output as JSON with a `triggers` array that the Ørlög ChronoEngine can consume. Format: `[{"date": "2026-06-15", "type": "transit", "planet": "Saturn", "aspect": "Square", "natal": "Sun", "quality": "tension"}]`.

- `[soon]` **Sigrid astrological profile** — generate a character astrological profile (natal chart + Lot of Fortune + Lot of Spirit + sect light) in JSON format for Sigrid's persistent context. Sigrid can use this to modulate her responses during specific transits.

- `[later]` **RuneForge integration** — map the current `SIGN_RUNES` and `NORSE_CORRESPONDENCES` dicts to RuneForgeAI's rune grammar. A birth chart becomes a starting rune configuration; transits modify active rune weights.

---

## Infrastructure

- `[next]` **SKILL.md version bump** — update version from 3.0.0 to match engine after each release.

- `[soon]` **Basic smoke test script** — `test_smoke.sh` that runs 4–5 quick subcommands and greps for known-good values. Catches regressions without a full test framework.

- `[later]` **Type annotations** — add `-> ReturnType` annotations to `resolve_birth`, `calc_planet_positions`, `calc_houses`, `calc_aspects` for IDE support. Pyright flags are currently suppressed; proper annotations would clean them up properly.

- `[later]` **Ephemeris data files** — optionally install Swiss Ephemeris data files (`.se1` files) for extended date range and higher precision. Default `pyswisseph` built-in covers 1800–2400 CE adequately. Files extend to 5400 BCE / 9999 CE and improve accuracy outside the default range.

---

## Known Limitations (Accepted)

These are documented limitations that are not planned to be fixed because the impact is low or the fix isn't worth the complexity:

- **Pyright "possibly unbound" warnings on `swe` and `AstrologicalSubject`** — false positives from conditional imports guarded by `SWE`/`KK` runtime checks. Not real errors. Suppressing with `# type: ignore` would clutter every call site.
- **Sidereal zodiac not exposed via CLI** — `tropical=False` exists internally but no `--sidereal` flag. Vedic astrology requires Lahiri ayanamsa selection and different dignity tables; a full sidereal mode is its own sub-project.
- **Composite Davison uses average location** — the Davison relationship chart averages birth coordinates, which is a simplification. The full Davison calculation uses the average Julian Day only; location is technically irrelevant to the chart. This is a common software convention.
- **Secondary progressions use 365.25 day year** — off by ~0.06 days per century from the tropical year (365.2422 days). Negligible for most practical use.

---

*The Norns weave forward. So do we.*
