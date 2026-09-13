# Fixture library audit — four tools, 2026-09-09

Method: each tool's fixture array extracted verbatim from its published artifact, merged on
(brand, name), then compared attribute by attribute. Values transcribed, never normalized.

## Counts

| Tool | Entries | Carries |
|---|---|---|
| Distro Plot | 29 | `va`, plus `motor` / `mode` on the hoist |
| Patch Plot | 27 | `m` (mode/footprint pairs), `d` (data connector), `rdm` |
| Truss Plot | 27 | `lb`, `hw` (hardware allowance) |
| Pull Plot | 27 | `va`, `ch`, `lb`, `cs` (case family), `per`, plus `ln` / `haze` |
| **Canonical union** | **29** | — |

## Finding 1 — the 29/27 gap is not a gap

Distro Plot's two extra entries are the grandMA3 console and the CM Lodestar hoist. Both draw
power, so Distro needs them; neither is a DMX fixture, has a hanging weight, or ships in a fixture
case. Correct as-is. They belong in the library flagged as non-fixture loads, not deleted.

## Finding 2 — three fixtures are named differently in Truss Plot

| Truss Plot | Everywhere else |
|---|---|
| MDG theONE hazer (cradle, dry) | MDG theONE hazer |
| Look Viper NT fogger (full) | Look Viper NT fogger |
| Martin JEM ZR45 fogger (full) | Martin JEM ZR45 fogger |

The parenthetical states the weighing condition, which is real information — a hazer's weight
depends on whether the fluid is in it. But as names they don't match, so nothing joins these
records across tools. **This is the drift the shared library exists to prevent**, and it is why the
schema carries a stable `id` and an `aliases` array: the condition belongs in the weight's `note`,
not in the fixture's name.

## Finding 3 — no value conflicts

Every attribute asserted by more than one tool agrees, numerically, in every case. `va` matches
between Distro and Pull for all 27 shared fixtures; `lb` matches between Truss and Pull for all 27;
Patch's default mode footprint matches Pull's `ch` for all 27.

Eight apparent mismatches on first pass were `14.0` versus `14` — a JSON type difference between
two extractions, not a disagreement. Worth recording because the same false positive will recur in
any future audit that compares serialized text instead of numbers.

## Finding 4 — one derived value is masquerading as stated

Patch Plot's `rdm` is `true` on 24 of 27 fixtures, but only three carry an explicit value in the
source array (`rdm:false` on the Rogue R2 Wash, Source Four 750 W, and Viper NT). The rest get
`true` from a `.forEach` default at load time. So 24 RDM assertions are **the tool's default, not a
manufacturer claim** — and Patch Plot's own doc already flags Rogue R2 Wash RDM as undocumented.
These 24 must be researched or marked `interpreted`; they cannot be migrated as `verified`.

Fixture `id` is likewise assigned at load time (`"L" + index`) in every tool, which means an id is
positional and changes if the array is reordered. The canonical library needs stable ids.

## Status of the migration

`fixtures.observed.json` holds all 29 canonical records with every attribute and which tool asserts
it. **It is not `fixtures.json`.** Every one of its 257 attribute records has `provenance: null`.
These figures were verified once, during each tool's build, against manufacturer sources that were
not recorded per-attribute in the shipped file. Under rule zero they are unsourced until a
researcher backfills the URL and the source's own label for each one.

Next: researcher pass to attach provenance, starting with the 27 `va` figures — the attribute with
the known failure history.
