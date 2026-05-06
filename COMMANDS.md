# CLI Reference — Astrology Engine

Complete flag reference for all 16 subcommands.

```
python3 astrology_engine.py <subcommand> [options]
```

---

## Global Notes

- `--date` always expects `YYYY-MM-DD` format
- `--time` always expects `HH:MM` 24-hour format; if omitted, noon (12:00) is used and houses/ASC are marked approximate
- `--city` / `--nation` feed the geocoding pipeline (Nominatim → kerykeion → hardcoded fallback)
- `--lat` / `--lon` always override geocoding when both are provided
- `--nation` should be an ISO 2-letter country code (`US`, `GB`, `DE`, `NO`, etc.)
- All local times are automatically converted to UTC via `timezonefinder` + `pytz`; the resolved timezone is displayed in the output header

---

## `natal`

Full natal chart.

```
python3 astrology_engine.py natal
    --date   YYYY-MM-DD        birth date (required)
    --time   HH:MM             birth time local (optional; default noon)
    --city   CITY              birth city (optional)
    --nation CC                ISO country code (optional)
    --name   NAME              name to display in output (optional)
    --lat    DECIMAL           latitude override (optional)
    --lon    DECIMAL           longitude override (optional)
```

**Output sections:** timezone label, ASC/MC, Sun/Moon/Rising summary, chart type (day/night), planetary positions table, aspects, essential dignities, Arabic Lots, antiscia, Hellenistic analysis, Norse/Rune overlay, house overview.

**Example:**
```bash
python3 astrology_engine.py natal \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US --name Volmarr
```

---

## `transit`

Transiting planets vs a natal chart.

```
python3 astrology_engine.py transit
    --date          YYYY-MM-DD   natal birth date (required)
    --time          HH:MM        natal birth time local (optional)
    --city          CITY         natal birth city (optional)
    --nation        CC           natal birth nation (optional)
    --transit-date  YYYY-MM-DD   sky date to compare (default: now)
    --transit-time  HH:MM        sky time (default: noon if transit-date given)
    --lat           DECIMAL      lat override (optional)
    --lon           DECIMAL      lon override (optional)
```

**Example — current transits:**
```bash
python3 astrology_engine.py transit \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US
```

**Example — forecast to specific date:**
```bash
python3 astrology_engine.py transit \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US \
  --transit-date 2027-06-21 --transit-time 12:00
```

---

## `synastry`

Two-chart cross-aspect analysis with optional house overlays.

```
python3 astrology_engine.py synastry
    --date1    YYYY-MM-DD   Person A birth date (required)
    --date2    YYYY-MM-DD   Person B birth date (required)
    --time1    HH:MM        Person A birth time (optional)
    --time2    HH:MM        Person B birth time (optional)
    --name1    NAME         Person A display name (default: "Person A")
    --name2    NAME         Person B display name (default: "Person B")
    --city1    CITY         Person A birth city (optional; enables house overlays)
    --city2    CITY         Person B birth city (optional; enables house overlays)
    --nation1  CC           Person A birth nation (optional)
    --nation2  CC           Person B birth nation (optional)
    --lat1     DECIMAL      Person A lat override (optional)
    --lon1     DECIMAL      Person A lon override (optional)
    --lat2     DECIMAL      Person B lat override (optional)
    --lon2     DECIMAL      Person B lon override (optional)
```

House overlay analysis (Person A's planets in Person B's houses, vice versa) is only available when **both** `--city1` and `--city2` are provided, or both `--lat`/`--lon` pairs are provided.

**Example:**
```bash
python3 astrology_engine.py synastry \
  --date1 1975-11-22 --time1 14:30 --name1 Volmarr \
  --city1 Indianapolis --nation1 US \
  --date2 1985-06-14 --time2 09:00 --name2 Seeker \
  --city2 London --nation2 GB
```

---

## `composite`

Composite chart (midpoint method) with optional Davison relationship chart.

```
python3 astrology_engine.py composite
    --date1    YYYY-MM-DD   Person A birth date (required)
    --date2    YYYY-MM-DD   Person B birth date (required)
    --time1    HH:MM        Person A birth time (optional)
    --time2    HH:MM        Person B birth time (optional)
    --name1    NAME         (optional; default "Person A")
    --name2    NAME         (optional; default "Person B")
    --city1    CITY         Person A city (optional; enables Davison chart)
    --city2    CITY         Person B city (optional; enables Davison chart)
    --nation1  CC           (optional)
    --nation2  CC           (optional)
    --lat1 / --lon1 / --lat2 / --lon2   coordinate overrides (optional)
```

Davison chart requires both city/location pairs to derive the average location. Without cities, only the midpoint composite is shown.

---

## `synergy`

Full relationship analysis: score + aspects + composite.

```
python3 astrology_engine.py synergy
    --date1    YYYY-MM-DD   Person A birth date (required)
    --date2    YYYY-MM-DD   Person B birth date (required)
    --time1    HH:MM        (optional)
    --time2    HH:MM        (optional)
    --name1    NAME         (optional; default "Person A")
    --name2    NAME         (optional; default "Person B")
```

Outputs: harmony/challenge synergy score bar (%), weighted cross-aspect breakdown, composite chart positions with dignities, cross-midpoints table.

**Example:**
```bash
python3 astrology_engine.py synergy \
  --date1 1975-11-22 --time1 14:30 --name1 Volmarr \
  --date2 1985-06-14 --time2 09:00 --name2 Seeker
```

---

## `solar-return`

Solar return chart: exact moment Sun returns to natal degree.

```
python3 astrology_engine.py solar-return
    --date    YYYY-MM-DD   birth date (required)
    --time    HH:MM        birth time local (required for accurate results)
    --city    CITY         birth city (optional)
    --nation  CC           (optional)
    --year    YYYY         target year (default: current calendar year)
    --lat     DECIMAL      (optional)
    --lon     DECIMAL      (optional)
```

The engine iterates to convergence to find the exact solar return moment accurate to arc-seconds.

**Example:**
```bash
python3 astrology_engine.py solar-return \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US \
  --year 2026
```

---

## `progressions`

Secondary progressions (1 day after birth = 1 progressed year).

```
python3 astrology_engine.py progressions
    --date       YYYY-MM-DD   birth date (required)
    --time       HH:MM        birth time local (optional)
    --city       CITY         birth city (optional)
    --nation     CC           (optional)
    --prog-date  YYYY-MM-DD   target date for progressed chart (default: today)
    --lat        DECIMAL      (optional)
    --lon        DECIMAL      (optional)
```

Shows all progressed positions plus tight-orb (≤2°) aspects between progressed and natal planets.

---

## `lunar`

Current lunar intelligence. No arguments required.

```
python3 astrology_engine.py lunar
```

Outputs: Moon's current sign and degree, phase name (New/Waxing/Full/Waning), illumination %, void-of-course status (with time until next ingress), next New Moon date, next Full Moon date, Moon aspects to current transiting planets, Norse overlay (Máni's phase).

---

## `planet-hours`

Chaldean planetary hours for a date and location.

```
python3 astrology_engine.py planet-hours
    --date    YYYY-MM-DD   date to calculate (default: today)
    --city    CITY         location city (optional)
    --nation  CC           (optional)
    --lat     DECIMAL      latitude decimal (optional)
    --lon     DECIMAL      longitude decimal (optional)
```

If no location is given, defaults to Indianapolis (39.7684°N, 86.1581°W). Each hour shows: start time, end time, planet ruler, Norse deity, and quality keywords.

**Example:**
```bash
python3 astrology_engine.py planet-hours \
  --city Oslo --nation NO
```

---

## `lots`

Arabic Lots / Hermetic Parts.

```
python3 astrology_engine.py lots
    --date    YYYY-MM-DD   birth date (required)
    --time    HH:MM        birth time local (optional)
    --city    CITY         (optional)
    --nation  CC           (optional)
    --lat     DECIMAL      (optional)
    --lon     DECIMAL      (optional)
```

All seven classical Lots: Fortune, Spirit, Eros, Necessity, Courage, Victory, Nemesis. Day/night chart formula switching applied automatically. Output shows longitude, sign, house placement, and brief interpretation.

---

## `hellenistic`

Hellenistic analysis layer.

```
python3 astrology_engine.py hellenistic
    --date    YYYY-MM-DD   birth date (required)
    --time    HH:MM        birth time (optional)
    --city    CITY         (optional)
    --nation  CC           (optional)
    --lat     DECIMAL      (optional)
    --lon     DECIMAL      (optional)
```

Outputs: sect (day/night), sect light (Sun or Moon as chart ruler), planetary joys by house, triplicity rulers for fire/earth/air/water, stellium detection, mutual receptions.

---

## `dignity`

Standalone essential dignities table.

```
python3 astrology_engine.py dignity
    --date    YYYY-MM-DD   birth date (required)
    --time    HH:MM        birth time (optional)
    --city    CITY         (optional)
    --nation  CC           (optional)
    --lat     DECIMAL      (optional)
    --lon     DECIMAL      (optional)
```

Full Ptolemaic dignity hierarchy for all planets: domicile, exaltation (with exact-degree flag), fall, detriment, triplicity, Egyptian terms, Chaldean face. Scored and ranked. Mutual receptions listed.

---

## `antiscia`

Standalone antiscia table.

```
python3 astrology_engine.py antiscia
    --date    YYYY-MM-DD   birth date (required)
    --time    HH:MM        birth time (optional)
```

No location needed. Shows antiscia (solstice reflection across 0°Cancer/Capricorn axis) and contra-antiscia (reflection across 0°Aries/Libra axis) for all planets. Inter-planet connections highlighted when two antiscia are within orb.

---

## `predict`

Event prediction within a time window.

```
python3 astrology_engine.py predict
    --date              YYYY-MM-DD   natal birth date (required)
    --time              HH:MM        natal birth time (optional)
    --city              CITY         natal birth city (optional)
    --nation            CC           (optional)
    --start             YYYY-MM-DD   window start (default: today)
    --end               YYYY-MM-DD   window end (default: today + 1 year)
    --transit-planets   LIST         comma-separated transit planet list
    --natal-planets     LIST         comma-separated natal target list
    --lat               DECIMAL      (optional)
    --lon               DECIMAL      (optional)
```

Default transit planets: `Jupiter,Saturn,Uranus,Neptune,Pluto,Chiron,N.Node,Mars,Sun,Venus,Mercury`
Default natal targets: `Sun,Moon,Mercury,Venus,Mars,Jupiter,Saturn,Chiron,N.Node,Asc,MC`

Four prediction layers:
1. **Exact transit-to-natal aspects** (bisection to 0.01°)
2. **Planetary stations** (retrograde / direct)
3. **Sign ingresses** (planet crosses sign boundary)
4. **Eclipses** (New Moon / Full Moon eclipses)

**Example — outer planets only, one year:**
```bash
python3 astrology_engine.py predict \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US \
  --start 2026-01-01 --end 2027-01-01 \
  --transit-planets "Jupiter,Saturn,Uranus,Neptune,Pluto"
```

**Performance note:** A full one-year window with all planets takes 5–15 seconds on the Raspberry Pi 5. Narrow the window or use `--transit-planets` to reduce compute time.

---

## `geoastrology`

Astrocartography — MC/IC/ASC/DSC lines.

```
python3 astrology_engine.py geoastrology
    --date       YYYY-MM-DD   birth date (required)
    --time       HH:MM        birth time local (optional)
    --city       CITY         birth city (optional)
    --nation     CC           (optional)
    --name       NAME         display name (optional)
    --lat        DECIMAL      birth location lat override (optional)
    --lon        DECIMAL      birth location lon override (optional)
    --query-lat  DECIMAL      analyse proximity to this location (optional)
    --query-lon  DECIMAL      analyse proximity to this location (optional)
```

**Output sections:**
- MC/IC lines table: planet RA, Dec, and Earth longitude where it culminates/anti-culminates
- ASC lines: latitude-sampled table of where each planet rises
- DSC lines: brief summary for Sun, Moon, Venus, Mars, Jupiter, Saturn
- Power spot analysis: when `--query-lat`/`--query-lon` provided, shows which chart lines pass within 3° of that location

**Example:**
```bash
python3 astrology_engine.py geoastrology \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US \
  --name Volmarr \
  --query-lat 59.91 --query-lon 10.75
```

---

## `aspect-grid`

Full aspect matrix for all planets.

```
python3 astrology_engine.py aspect-grid
    --date    YYYY-MM-DD   birth date (required)
    --time    HH:MM        birth time (optional)
```

N×N grid showing all 11 aspect types between all 12 planet points. Glyph-based display. No location needed.

---

## Coordinate Reference

When using `--lat` / `--lon`:

- North latitudes are positive: `--lat 39.7684` (Indianapolis)
- South latitudes are negative: `--lat -33.8688` (Sydney)
- East longitudes are positive: `--lon 10.7522` (Oslo)
- West longitudes are negative: `--lon -86.1581` (Indianapolis)

---

## Nation Code Examples

| Code | Country |
|------|---------|
| `US` | United States |
| `GB` | United Kingdom |
| `DE` | Germany |
| `NO` | Norway |
| `SE` | Sweden |
| `DK` | Denmark |
| `IS` | Iceland |
| `FI` | Finland |
| `IE` | Ireland |
| `FR` | France |
| `AU` | Australia |
| `JP` | Japan |
| `CA` | Canada |
| `MX` | Mexico |

---

*The stars wait for no one's permission.*
