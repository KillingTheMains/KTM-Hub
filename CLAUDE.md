# Rig Plot Suite — project rules

Inherits `~/.claude/CLAUDE.md`. This file adds what is specific to the suite.

## What this is

Four single-file, self-contained HTML rig-planning tools, published as Claude artifacts:

- **Distro Plot** — three-phase power: leg balance, circuit packing, Soca cuts, branch voltage drop
- **Patch Plot** — DMX universe packing and node planning
- **Truss Plot** — rigging loads
- **Pull Plot** — pull sheet, cases, truck pack

They share a fixture library and a body of reference constants. That sharing is the project's
main risk: the same fixture appears in all four with different attributes attached.

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

`data/fixtures.json` is the single source of truth for the fixture library — every attribute, with
a source URL per attribute. `data/constants.json` holds the shared reference constants.

A tool never carries a figure the data files don't have. Adding a fixture means: researcher →
refuter → update `fixtures.json` → auditor confirms all four tools pick it up → builder patches
each tool, sequentially.

## Build conventions

- Builders edit `<tool>.working.html`. I diff against the live file and promote after ACCEPT.
- Each tool stays a single self-contained file. No external assets, no build step.
- Publishing means republishing the tool's existing artifact — same URL, never a new one.

## What the refuter checks here

Beyond re-deriving the math from `constants.json`:

- Print stylesheet renders
- CSV export opens and matches the on-screen values
- Saved-rig round trip through the artifact db
- The generated SVG (riser, truck pack) is geometrically right, not just present
- Default state still demonstrates the tool's lesson — for Distro Plot, the FOH position tripping
  the 5% flag at 9.4%

## Handoff

Every session ends with the tool's doc updated in the Cowork project (`claude/<tool>.md`) and
mirrored to `docs/`. Reference constants, known limits, and default state all live there. A new
session starts by reading it, not by re-deriving it.
