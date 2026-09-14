# KTM Hub — project rules

Inherits `~/.claude/CLAUDE.md`. This file adds what is specific to the suite.

## What this is

One published Claude artifact (KTM Hub, url in `~/.claude` memory) holding eleven single-file
HTML tools in same-origin frames, sharing one store through the `KTM` data layer:

Distro Plot · Patch Plot · Truss Plot · Pull Plot · Rack Plot · Loom Plot · Net Plot ·
Truss List · Truck Plot · Label Plot · Shop Order.

Distro, Patch and Pull are still ported frames (own fixture lists, rigs namespaced under
`tools/<tool>/`); every other tool is native and reads the shared `fixtures`, `gear`, `meta` and
`shows/{id}/*` collections. The schema and its three rules live in `data-model.md`; read it first.

## Where things live

- Canonical clone: `~/Developer/KTM-Hub`, GitHub `KillingTheMains/KTM-Hub`. Commit and push here.
- Drive mirror: `Cowork Playground/RigPlot/` — rsync from the clone (no `.git`), so Cowork
  sessions see current sources. Never run git inside the Drive folder.
- `python3 assemble.py` builds `ktm-hub.html` from `ktm-hub.template.html` + the tool files.
- Before republishing, read the artifact and diff it against the local bundle: a Cowork
  session once published without syncing back. Republish the existing URL, never a new one.
- `data/catalog/` is a read-only snapshot of the store's `gear/*` and `meta/*` for offline
  validation; `import/` holds show converters; `data/shows/` holds `ktm-show` bundles.

## The verification standard

The hard part of this project is not code. It is deciding whether a number on a spec sheet is the
thing you think it is. Nine of Distro Plot's first-pass wattages were wrong, and both recurring
traps were labelling traps: **LED-engine wattage read as fixture draw**, and **lamp wattage read
as fixture draw**.

So, on top of the global researcher rules:

- Gear figures (VA, weight, WLL, DMX footprint, case dims) need a manufacturer PDF or two
  independent primary sources. A retailer listing or rental-house page is never `verified`.
- Always record **what the source calls the number**, verbatim. That label is the actual finding.
- A researcher never reconciles a conflict between a spec sheet and a manual. It comes back
  `conflicting` and I decide.
- Standards figures (NEC tables, K factors) get cited to article and table number.

## Canonical data

The store's `fixtures/{id}` documents are the fixture library — every attribute carries a source
label, url, retrieval date and status (`verified` / `interpreted` / `conflicting` / `observed`).
`gear/*` holds product catalogs, `meta/tokens` the colour tokens. A native tool never carries a
figure the store does not have. Adding a fixture means: researcher → refuter → write the
document → the tools pick it up on next load.

## Build conventions

- Builders edit `<tool>.working.html`. I diff against the live file and promote after ACCEPT,
  then assemble, commit, push, rsync to Drive, republish.
- Each tool stays a single self-contained file. No external assets beyond the shared Google
  Fonts link, no build step, no jsPDF. Print is `window.print()` with `@page`.
- A native tool uses `window.KTM` only (`boot, P, list, get, set, del, activeShow, setActive,
  cacheGet, cacheSet`), writes only the collection it owns (`OWNERS`), stores colour tokens not
  hex, and never calls a full `render()` from an `oninput` handler.
- New tool = the file + one `TOOLS` entry in the template + one line in `assemble.py`.

## What the refuter checks here

Beyond re-deriving the math from `constants.json`:

- Print stylesheet renders
- CSV export opens and matches the on-screen values
- Saved-rig round trip through the artifact db
- The generated SVG (riser, truck pack) is geometrically right, not just present
- Default state still demonstrates the tool's lesson — for Distro Plot, the FOH position tripping
  the 5% flag at 9.4%

## Handoff

Every session ends with `data-model.md` and `roadmap.md` updated and committed. Known limits and
default state live there. A new session starts by reading them, not by re-deriving them.
`docs/prepro-port-map.md` records what was taken from the legacy Pre-Pro suite and what was
deliberately left behind.
