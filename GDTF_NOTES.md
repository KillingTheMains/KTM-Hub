# Reading GDTF files

## What the format is

A `.gdtf` is a **ZIP archive**. Everything structured is in `description.xml` at the root; the
rest is 3D models, gobo images, SVGs and a thumbnail. Those dominate the file size and are
irrelevant to us — a 6.6 MB Robe Esprite file is 6.6 MB of geometry wrapped around ~400 KB of XML.

Parser: `gdtf_read.py`. No dependencies beyond the standard library (`zipfile` + `ElementTree`).

## What GDTF is authoritative for

**DMX modes and their footprints.** This is the format's entire purpose and it is what a console
actually loads, which makes it better than any spec sheet — spec sheets summarise modes in prose,
name them inconsistently, and omit them.

Proven on the one fixture that overlapped the library:

| | library | spec-sheet research | GDTF |
|---|---|---|---|
| MAC Ultra modes | Basic 48, Extended 58 | Standard 48 (one mode) | **Compact 42, Basic 48, Extended 58** |

GDTF found a third mode neither other source had. The spec-sheet pass found only one.

**Weight** was populated in all six files and agreed with the researched figure to the decimal.

## What GDTF does NOT give

**Power draw and power connectors.** The spec has elements for both. Across all six files tested —
Martin, Robe ×2, Ayrton, ACME — **zero** populated either one.

So GDTF and spec sheets are complementary, not competing:

| Field | Best source |
|---|---|
| DMX modes and footprints | **GDTF** |
| Weight, dimensions | GDTF (spec sheet confirms) |
| Power draw | **Spec sheet / manual only** |
| Power connector, pass-thru | **Spec sheet / manual only** |

Never read an absent GDTF element as zero.

## The footprint trap

A mode's footprint is **the highest DMX offset any channel occupies**, not the number of
`<DMXChannel>` nodes. A 16-bit channel occupies two offsets (`Offset="12,13"`). MAC Ultra's Basic
mode has **37 channel nodes and a 48-channel footprint**. Counting nodes undercounts by 23%, and
undercounting a footprint is how a universe silently overflows in Patch Plot.

## Provenance

Two signals decide whether a GDTF counts as a manufacturer source:

- `FixtureType@Description` often says so outright — the Martin file reads
  `"Official Martin Professional File"`.
- `<Revisions>` records who uploaded it, when, and why.

The parser sets `provenanceStatus` to `verified` only when the description claims official
authorship, and `interpreted` otherwise. Of the six tested, only the Martin file was official —
the two Robe files, both Ayrtons and the ACME are community builds, and their modes are still
useful but are recorded as `interpreted`.

## Where this matters most

The takeoff. A plot's key gives manufacturer and model; the mode has to come from the production
electrician. With GDTF in the library that stops being a typed field and becomes **a dropdown of
the fixture's real modes with real footprints** — far less to get wrong, and the footprint that
Patch Plot packs against is then the same number the console will use.

## Local sources

Seven GDTF files were already on the Mac under `~/MALightingTechnology/gma3_library/fixturetypes/`,
copied to `RigPlot/gdtf/`. The grandMA3 library folder is the obvious place to keep harvesting;
GDTF Share is the upstream for anything not already there.

---

## Reaching GDTF Share directly — 2026-09-10

`gdtf-share.com` is **blocked by the network allowlist**. The gateway answers 403 to CONNECT, from
both the cloud workspace and the Cowork VM on the Mac — they share one egress policy. Nothing
routes around it: no proxy, no mirror, no archive. Jason is the admin on that allowlist, so adding
the domain is the unlock.

Two scripts, deliberately separate:

- **`gdtf_share.py`** — search the catalogue and pull a file. No browser at any point.
  `probe` · `search "<text>"` · `get <rid…>` · `get --name "<text>"`
- **`gdtf_ingest.py`** — merge whatever landed in `gdtf/` into fixture records.

They are separate because the merge is the part that can quietly corrupt the library, and it has to
be runnable and re-runnable without touching the network.

### The endpoint shapes are unverified

Nothing in `gdtf_share.py` has run against the live site. Every URL and field name is a hypothesis,
which is why they are collected in one `ENDPOINTS` dict and why `probe` exists: it reports what each
endpoint returns, whether anything works anonymously, and what fields the list rows actually carry.
**Run `probe` first** the day the domain opens, and fix `ENDPOINTS` in one place if it is wrong.

### Credentials

`gdtf-share.json` beside the script (or `~/.gdtf-share.json`), `{"user":…, "password":…}`. Never
printed, never logged, never in an error message, never written to the Hub database, the project
docs or an artifact. `gdtf-share.example.json` is the template. If this folder ever becomes a git
repo, the real file goes in `.gitignore` first.

### What the ingest merge does, and why it is the careful half

Testing on the seven files already on disk found two real failures on the first run:

1. **The ACME file did not join and created a duplicate.** GDTF calls it
   `ACME SANA PROFILE (XA 300 BSWF IP)` — brand repeated in the name, model code appended — while
   the library calls it `SANA Profile`. A slug-only importer splits one fixture into two, which is
   worse than not importing. Matching is now **fixtureTypeID first** (real identity, stable across
   renames and revisions), then the record's own aliases, then slug, then slug with a repeated
   brand prefix stripped.
2. **The ACME weight would have been overwritten.** GDTF says 5.58 kg; the library holds ACME's own
   published 26 kg. The merge now records the disagreement in `weight.conflicting` and keeps the
   manufacturer figure — and recognised that this exact claim was already on file, so it did not
   double-log it.

The rule the merge is built on: **GDTF is authoritative for DMX modes and nothing else.** Modes are
written. Weight and dimensions are compared and, on disagreement, recorded as conflicts rather than
replaced. Power is never taken from GDTF at all — across all seven files, zero populated power draw
and zero populated connectors. An empty element is not zero.

A fixture GDTF brings in that the library does not hold lands with power fields marked `missing`,
so the hole is visible and a researcher pass can fill it.
