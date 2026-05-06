---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/etre34gdfgd3.png](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/etre34gdfgd3.png)

---

# AI Agent Astrology Engine — Volmarr's Longhall

> *Full-spectrum astrological computation. Swiss Ephemeris on bare metal. Norse sky, Hellenistic roots.*

A complete astrological engine running on a Raspberry Pi 5 (or any other device) as part of the **Hermes Agent** skill system. No cloud, no API keys, no lookup tables. Real ephemeris positions via `pyswisseph` with 16 CLI subcommands covering every major technique from classical Arabic Lots to astrocartography.

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/1a64a630-c13b-499b-a1c9-4e6f5fc3fee0.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/1a64a630-c13b-499b-a1c9-4e6f5fc3fee0.jpg)

---

## Contents

- [What It Does](#what-it-does)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [All 16 Subcommands](#all-16-subcommands)
- [Geocoding & Timezone Pipeline](#geocoding--timezone-pipeline)
- [Norse & Hellenistic Layer](#norse--hellenistic-layer)
- [Hermes Agent Integration](#hermes-agent-integration)
- [WYRD Protocol Hooks](#wyrd-protocol-hooks)
- [File Structure](#file-structure)
- [Dependencies](#dependencies)
- [Further Reading](#further-reading)

---

## What It Does

This is not a keyword reader or chart-wheel generator. The engine:

- Calculates real **Julian Day** ephemeris positions using Swiss Ephemeris
- Derives **Placidus house cusps** via `swe.houses()`
- Computes **11 aspect types** (conjunction through bi-quintile) with applying/separating detection
- Scores **essential dignities** through the full Ptolemaic hierarchy: domicile → detriment → exaltation → fall → triplicity → terms → face
- Calculates all **7 classical Arabic Lots** with day/night chart formulas
- Detects **void-of-course Moon** via exact aspect targeting
- Computes **synastry** cross-aspects with house overlays when birth cities are provided
- Finds **exact transit dates** to 0.01° precision via bisection algorithm
- Generates **astrocartography** MC/IC/ASC/DSC lines from first principles (not lookup tables)
- Overlays **Elder Futhark runes** and **Norse deity correspondences** on every chart

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/1e181307-c1c2-4ecb-912e-f88d3980e3e5.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/1e181307-c1c2-4ecb-912e-f88d3980e3e5.jpg)

---

## Quick Start

```bash
# Full natal chart
python3 astrology_engine.py natal \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US \
  --name Volmarr

# Current transits to natal
python3 astrology_engine.py transit \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US

# Lunar intelligence right now
python3 astrology_engine.py lunar

# Planetary hours today
python3 astrology_engine.py planet-hours \
  --city Indianapolis --nation US

# Event prediction — what exact transits hit in the next year?
python3 astrology_engine.py predict \
  --date 1975-11-22 --time 14:30 \
  --city Indianapolis --nation US \
  --start 2026-01-01 --end 2027-01-01
```

---

## Installation

### System Requirements

- Python 3.9+
- Raspberry Pi 5 (16 GB RAM) — or any Linux/macOS machine
- Internet access for first-use Nominatim geocoding (optional; falls back gracefully offline)

### Dependencies

```bash
pip install pyswisseph kerykeion geopy timezonefinder pytz
```

| Package | Purpose | Required |
|---------|---------|----------|
| `pyswisseph` | Swiss Ephemeris — all celestial positions | **Yes** |
| `kerykeion` | Supplementary geocoding cache | Recommended |
| `geopy` | Nominatim geocoder — any world city | Recommended |
| `timezonefinder` | IANA timezone from lat/lon | Recommended |
| `pytz` | DST-aware local→UTC conversion | Recommended |

The engine degrades gracefully: if `geopy` is absent it falls back to kerykeion then a hardcoded city list. If `timezonefinder` is absent it treats input time as UTC and says so.

### Verify Installation

```bash
python3 astrology_engine.py lunar
```

You should see current Moon phase, illumination %, and next lunation dates. If `pyswisseph` is missing you will get a clear error.

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/544f9808-270f-4ba7-9d6a-af48d47a624e.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/544f9808-270f-4ba7-9d6a-af48d47a624e.jpg)

---

## All 16 Subcommands

### `natal` — Full Natal Chart

```bash
python3 astrology_engine.py natal \
  --date YYYY-MM-DD [--time HH:MM] \
  --city CITY --nation CC [--name NAME] \
  [--lat LAT --lon LON]
```

Output sections:
- Planetary positions (longitude, house, speed, retrograde flag)
- Aspects table with orb, quality, applying/separating
- Essential dignities (scored hierarchy)
- Arabic Lots (Fortune, Spirit, Eros, Necessity, Courage, Victory, Nemesis)
- Antiscia and contra-antiscia
- Hellenistic analysis (sect, sect light, joys, triplicity)
- Norse/Rune overlay
- House overview

---

### `transit` — Transits to Natal

```bash
python3 astrology_engine.py transit \
  --date YYYY-MM-DD [--time HH:MM] \
  --city CITY --nation CC \
  [--transit-date YYYY-MM-DD] [--transit-time HH:MM]
```

Default sky date is now (UTC). Use `--transit-date` to forecast against any past or future sky.

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/8ac34e68-f15a-4c8c-bbcb-690a689d37c5.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/8ac34e68-f15a-4c8c-bbcb-690a689d37c5.jpg)

---

### `synastry` — Two-Chart Comparison

```bash
python3 astrology_engine.py synastry \
  --date1 YYYY-MM-DD [--time1 HH:MM] --name1 NAME \
  --date2 YYYY-MM-DD [--time2 HH:MM] --name2 NAME \
  [--city1 CITY --nation1 CC] [--city2 CITY --nation2 CC]
```

Providing both cities enables house overlay analysis (Person A's planets in Person B's houses and vice versa).

---

### `composite` — Composite / Davison Chart

```bash
python3 astrology_engine.py composite \
  --date1 YYYY-MM-DD [--time1 HH:MM] \
  --date2 YYYY-MM-DD [--time2 HH:MM] \
  [--city1 CITY --nation1 CC] [--city2 CITY --nation2 CC] \
  [--name1 NAME] [--name2 NAME]
```

Midpoint composite by default. Providing both cities also generates the Davison relationship chart (average Julian Day + average location).

---

### `synergy` — Full Relationship Analysis

```bash
python3 astrology_engine.py synergy \
  --date1 YYYY-MM-DD [--time1 HH:MM] \
  --date2 YYYY-MM-DD [--time2 HH:MM] \
  [--name1 NAME] [--name2 NAME]
```

Combined report: harmony/challenge synergy score bar, key cross-aspects, composite chart positions, composite dignities, cross-midpoints.

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/c5c058a2-a770-49b1-a58d-637db801313e.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/c5c058a2-a770-49b1-a58d-637db801313e.jpg)

---

### `solar-return` — Solar Return Chart

```bash
python3 astrology_engine.py solar-return \
  --date YYYY-MM-DD --time HH:MM \
  --city CITY --nation CC \
  [--year YYYY]
```

Finds the exact moment the Sun returns to its natal degree for the target year (default: current year). Uses iterative convergence accurate to arc-seconds.

---

### `progressions` — Secondary Progressions

```bash
python3 astrology_engine.py progressions \
  --date YYYY-MM-DD --time HH:MM \
  --city CITY --nation CC \
  [--prog-date YYYY-MM-DD]
```

One day after birth = one progressed year. Default target is today. Shows all progressed positions plus tight-orb aspects to natal planets.

---

### `lunar` — Lunar Intelligence

```bash
python3 astrology_engine.py lunar
```

No parameters needed. Returns: current phase name, illumination %, void-of-course status, next New Moon date, next Full Moon date, Moon's aspects to other planets.

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/ccb952ab-e824-4c94-aea9-29651672549d.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/ccb952ab-e824-4c94-aea9-29651672549d.jpg)

---

### `planet-hours` — Chaldean Planetary Hours

```bash
python3 astrology_engine.py planet-hours \
  [--date YYYY-MM-DD] \
  [--city CITY --nation CC] \
  [--lat LAT --lon LON]
```

Chaldean hour ruler sequence for the day, sunrise to sunset to sunrise. Each hour shows the planet ruler and its Norse god correspondence.

---

### `lots` — Arabic Lots

```bash
python3 astrology_engine.py lots \
  --date YYYY-MM-DD [--time HH:MM] \
  --city CITY --nation CC
```

All seven Hermetic Parts with day/night chart switching: Fortune, Spirit, Eros, Necessity, Courage, Victory, Nemesis.

---

### `hellenistic` — Hellenistic Analysis

```bash
python3 astrology_engine.py hellenistic \
  --date YYYY-MM-DD [--time HH:MM] \
  --city CITY --nation CC
```

Sect (day/night chart), sect light (Sun or Moon as chart ruler), planetary joys by house, triplicity rulers for each element, stelliums, mutual receptions.

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/ecc1715c-605a-4575-bee5-0d91ade23108.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/ecc1715c-605a-4575-bee5-0d91ade23108.jpg)

---

### `dignity` — Essential Dignities Table

```bash
python3 astrology_engine.py dignity \
  --date YYYY-MM-DD [--time HH:MM] \
  --city CITY --nation CC
```

Standalone dignity table: all planets with their domicile/detriment/exaltation/fall/triplicity/terms/face status, scored and ranked. Shows mutual receptions.

---

### `antiscia` — Antiscia Table

```bash
python3 astrology_engine.py antiscia \
  --date YYYY-MM-DD [--time HH:MM]
```

Antiscia (solstice points) and contra-antiscia for all planets, with inter-planet connection detection when two antiscia are conjunct.

---

### `predict` — Event Prediction

```bash
python3 astrology_engine.py predict \
  --date YYYY-MM-DD [--time HH:MM] \
  --city CITY --nation CC \
  [--start YYYY-MM-DD] [--end YYYY-MM-DD] \
  [--transit-planets LIST] [--natal-planets LIST]
```

Four prediction layers in one report:
1. **Exact transit-to-natal aspects** — bisection search finds crossing dates to 0.01°
2. **Planetary stations** — all retrograde and direct stations in window
3. **Sign ingresses** — all planets crossing sign boundaries
4. **Eclipses** — New/Full Moon eclipses in window

Default window: today → one year ahead. Planet lists are comma-separated (e.g. `--transit-planets Jupiter,Saturn,Uranus`).

---

### `geoastrology` — Astrocartography

```bash
python3 astrology_engine.py geoastrology \
  --date YYYY-MM-DD [--time HH:MM] \
  --city CITY --nation CC \
  [--name NAME] \
  [--query-lat LAT --query-lon LON]
```

MC/IC lines: exact Earth longitude where each planet culminates/anti-culminates. ASC/DSC lines: latitude-sampled table of where each planet rises/sets. Add `--query-lat`/`--query-lon` for a **power spot analysis** — finds which chart lines are within 3° of any location on Earth.

---

### `aspect-grid` — Full Aspect Matrix

```bash
python3 astrology_engine.py aspect-grid \
  --date YYYY-MM-DD [--time HH:MM]
```

Complete N×N aspect matrix for all 11 major and minor aspects between all planets.

---

## Geocoding & Timezone Pipeline

All location-dependent commands use a four-tier cascade:

```
1. --lat / --lon explicit override (always wins)
        ↓ (if not provided)
2. Nominatim (OpenStreetMap) — any world city, free, no API key
        ↓ (if Nominatim fails or is offline)
3. kerykeion geonames database (SQLite cache, ~60 cities)
        ↓ (if kerykeion fails)
4. Hardcoded fallback dict (~70 major world cities)
        ↓ (if city unknown)
   Warns and uses (0.0°N, 0.0°E) — Greenwich/Equator
```

Once coordinates are resolved, the **timezone pipeline**:

```
lat/lon → timezonefinder → IANA tz name (e.g. "America/Indiana/Indianapolis")
                 ↓
tz name + local birth time → pytz.localize(is_dst=None)
                 ↓
UTC hour for Swiss Ephemeris Julian Day calculation
```

The `is_dst=None` setting raises `AmbiguousTimeError` on genuinely ambiguous DST boundaries; the engine catches this and falls back to `is_dst=False` (standard time). This handles Indiana's complex DST history and all other edge cases correctly.

Every chart header shows the resolved timezone label, for example:

```
Time: 14:30 LT  →  19:30 UTC  (UTC-05:00  America/Indiana/Indianapolis)
```

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/ff1930e8-65c4-4214-b3ca-936e7c6d0e67.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/ff1930e8-65c4-4214-b3ca-936e7c6d0e67.jpg)

---

## Norse & Hellenistic Layer

### Planet → Norse Deity

| Planet | Norse Correspondence |
|--------|---------------------|
| Sun | Sól — Ásgard's light, the burning road |
| Moon | Máni — the measurer, Hrimfaxi's rider |
| Mercury | Oðinn — seeker, rune-master, the wanderer |
| Venus | Freyja — Vanaheim's queen, seiðr and war |
| Mars | Týr — the one-handed, the oath-keeper |
| Jupiter | Þórr — Miðgarðr's protector, the law |
| Saturn | Allfather in his aspect of fate and age |
| Uranus | Loki — the shape-changer, the unbound |
| Neptune | Njörðr — sea-mist, dissolution, the deep |
| Pluto | Hel — Niflheim's queen, death-door |
| Chiron | Mímir — severed wisdom, the eternal wound |

### Sign → Elder Futhark Rune

Each sign maps to an Elder Futhark rune — see `SIGN_RUNES` constant in `astrology_engine.py` for the full table, and `references/` for the full rune grimoire with galdr chants and magical applications.

### Hellenistic Techniques

The engine implements:
- **Sect** — day vs night chart (Sun above/below horizon)
- **Sect light** — whether the chart runs on solar or lunar power
- **Planetary joys** — traditional house joy assignments (Mercury/1st, Moon/3rd, etc.)
- **Triplicity rulers** — fire/earth/air/water primary + secondary + participating rulers
- **Mutual receptions** — planets in each other's domicile
- **Stelliums** — three or more planets within 15° of longitude

### Essential Dignity Scoring

Points assigned by Ptolemaic hierarchy:

| Dignity | Score |
|---------|-------|
| Domicile | +5 |
| Exaltation | +4 |
| Triplicity ruler | +3 |
| Term (Egyptian) | +2 |
| Face (Chaldean decan) | +1 |
| Peregrine (none) | 0 |
| Fall | −4 |
| Detriment | −5 |

---

## Hermes Agent Integration

The engine is registered as a Hermes skill at:

```
/home/pi/.hermes/skills/divination/astrology/
├── SKILL.md           ← Hermes skill manifest
└── astrology_engine.py
```

`SKILL.md` contains the YAML frontmatter the Hermes dispatcher reads, plus full usage documentation for the AI agent layer. When Hermes receives an astrology request, it reads `SKILL.md`, determines the correct subcommand, runs the engine, and interprets the output through the Norse mythic framing.

### Key agent rules from SKILL.md

- Never fabricate planetary positions — always run the engine for current data
- Birth time unknown → default to noon (12:00) and flag houses/ASC as approximate
- City unknown → pass `--lat`/`--lon` directly if coordinates are available
- Present Norse correspondences as living tradition overlay, not historical reconstruction

---

## WYRD Protocol Hooks

When called from the Norse Saga Engine or Ørlög system:

| Astrological Output | WYRD Protocol Mapping |
|--------------------|----------------------|
| Lot of Fortune | Material wyrd — resource pool and luck |
| Lot of Spirit | Seiðr capacity — inner alignment |
| Sect light (Sun) | Solar channel — will, action, outer fate |
| Sect light (Moon) | Lunar channel — intuition, inner fate |
| Current transits | Potential Wyrd event triggers in active campaign |
| Natal chart angles | ASC → PAD Valence axis; MC → Arousal axis |

These are conceptual hooks. Code-level integration with the WYRD Protocol ECS lives in the Norse Saga Engine codebase, not here.

---

## File Structure

```
astrology/
├── README.md                    ← You are here
├── SKILL.md                     ← Hermes Agent skill manifest
├── ARCHITECTURE.md              ← Technical deep-dive for vibe coding
├── COMMANDS.md                  ← Full CLI reference (every flag)
├── CHANGELOG.md                 ← Version history
├── ROADMAP.md                   ← Planned features and known gaps
├── CONTRIBUTING.md              ← How to extend the engine
├── astrology_engine.py          ← The engine (~2850 lines)
├── cache/
│   └── kerykeion_geonames_cache.sqlite
└── references/
    ├── engine-review-gaps.md    ← Original gap analysis (archived)
    └── gaps-and-integration-notes.md
```

---

## Dependencies

```
pyswisseph>=2.10        Swiss Ephemeris bindings
kerykeion>=5.0          Geocoding cache + chart helpers
geopy>=2.4              Nominatim geocoder
timezonefinder>=8.0     IANA timezone from coordinates
pytz>=2024              DST-aware timezone conversion
```

All installed on the target Raspberry Pi 5. For a fresh environment:

```bash
pip install pyswisseph kerykeion geopy timezonefinder pytz
```

---

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) — How the engine is built, data flow, constants, function map
- [COMMANDS.md](COMMANDS.md) — Exhaustive flag reference for every subcommand
- [ROADMAP.md](ROADMAP.md) — What's planned, what's known to be imperfect
- [CONTRIBUTING.md](CONTRIBUTING.md) — How to add subcommands, extend mappings, improve the engine
- [CHANGELOG.md](CHANGELOG.md) — What changed in each version

---

*Forged in the Longhall of Volmarr Wyrd. Read the sky; read the wyrd.*

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/Viking_Apache_V2_1.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/Viking_Apache_V2_1.jpg)

---

## License

Copyright (c) 2026 Volmarr Wyrd

AI Agent Astrology Engine is licensed under the **Apache License, Version 2.0**. See the [LICENSE](LICENSE) file for the full license text and [NOTICE](NOTICE) for the project attribution.

Unless required by applicable law or agreed to in writing, this project is distributed on an "AS IS" BASIS, without warranties or conditions of any kind, either express or implied.

---

## Distribution and Privacy Position

AI Agent Astrology Engine is published here as source code and project material.

The author does not require users to provide age, identity, government ID, biometric data, or similar personal information in order to access or use the source code in this repository.

The author may decline to provide official binaries, installers, hosted services, app-store releases, or other official distribution channels where doing so would require age verification, identity verification, or similar personal-data collection.

Any third party who forks, packages, redistributes, deploys, hosts, or otherwise makes this software available does so independently and is solely responsible for compliance with applicable law, platform policy, and distribution requirements in their own jurisdiction and context.

See [LEGAL-NOTICE.md](LEGAL-NOTICE.md) for details.

---
---

## RuneForgeAI

**RuneForgeAI** is my AI research, development, and creative systems forge: a Norse Pagan cyber-Viking workshop for building mythic AI architectures, memory systems, world engines, companion intelligence, and structured vibe coding tools.

RuneForgeAI exists at the crossroads of:

- **Mythic Engineering**
- **AI memory and continuity systems**
- **Viking-themed simulation and worldbuilding**
- **AI companions with stable identity**
- **small-model enhancement through architecture**
- **retrieval, grounding, and truth-verification systems**
- **cyber-Heathen software design**
- **human + AI co-creation**

The core idea is simple:

> AI should not be treated as a disposable text generator.  
> It should be shaped into structured, memory-bearing, meaning-aware systems that can preserve continuity, deepen creativity, and help humans build living worlds.

RuneForgeAI is where I explore architectures that make AI more coherent, more persistent, and more useful: not through hype, but through structure. Memory, retrieval, world state, personality, routing, verification, symbolic logic, and mythic design language all become part of the same forge.

This work connects directly to my larger ecosystem of projects, including the **Norse Saga Engine**, **Mythic Engineering**, **WYRD Protocol**, **Mímir-Vörðr**, cyber-Viking philosophy, AI companion design, and the broader vision of spiritually meaningful technology.

### What RuneForgeAI Builds

- AI-native memory frameworks
- persistent personality and companion systems
- Viking and mythic world simulation tools
- roleplay and RPG intelligence architectures
- structured prompt and documentation protocols
- retrieval-augmented truth systems
- small-model orchestration patterns
- cyber-Viking AI aesthetics and interfaces
- open frameworks for human-AI creative collaboration

### Guiding Principle

> Build AI like a living system, not a pile of prompts.

RuneForgeAI is my digital forge for turning myth, memory, code, and consciousness into working architecture.

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/image-23-RuneForgeAI.jpg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/image-23-RuneForgeAI.jpg)

---

![https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/IMG_0407.jpeg](https://raw.githubusercontent.com/hrabanazviking/astrology-engine/refs/heads/main/IMG_0407.jpeg)

---
