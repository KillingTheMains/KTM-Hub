# KTM Hub — data model

Settled 2026-09-10. This is the contract every tool builds against. Change it here first.

## The architecture correction

The plan of 2026-09-10 assumed nine artifacts could share one database. They cannot. The
artifact store is **per artifact** — "a persistent, realtime document store for this artifact...
One store per artifact" — and each artifact is served from its own origin, so localStorage
cannot bridge them either.

So the suite is **one artifact containing nine tools**, not nine artifacts. Sharing is solved by
construction. The four already-published tools (Distro, Patch, Truss, Pull) stay live at their own
URLs until each is ported in, one at a time; each port retires its standalone artifact.

## Two caps that shape the schema

- **5,000 documents** per artifact database, total.
- **256 KiB** per document, 32 levels deep.

Hence the aggregation rule: **one document per thing a person names** — a show, a position, a
rack, a loom, a truck, a fixture type — **and arrays inside for everything that belongs to it.**
A position carries its units in an array; it does not spend one document per hung fixture. A
truck carries its placements the same way. A 40-position show with 60 trucks costs about 100
documents, not 2,000.

## Collections

Path parity matters: a document path has an **even** number of segments, a collection an **odd**
number. Getting it wrong throws a `TypeError` at the call site, which is why the path builders
live in one place (`KTM.P`).

```
meta/{docId}                       tokens, constants                       owner: hub
fixtures/{fixtureId}               canonical fixture library               owner: hub
gear/{gearId}                      racks, cases, truss products, trailers  owner: hub

shows/{showId}                     identity                                owner: hub
shows/{showId}/positions/{posId}   position + units[]  ← takeoff lands here owner: hub
shows/{showId}/power/{docId}                                               owner: distro
shows/{showId}/patch/{docId}                                               owner: patch
shows/{showId}/racks/{rackId}                                              owner: rack
shows/{showId}/looms/{loomId}                                              owner: loom
shows/{showId}/network/{docId}                                             owner: net
shows/{showId}/truss/{trussId}     truss inventory by run                  owner: trusslist
shows/{showId}/cases/{caseId}                                              owner: pull
shows/{showId}/trucks/{truckId}                                            owner: truck
shows/{showId}/derived/{docId}     roll-ups                                owner: hub
```

## Three rules, each one a bug the audits found

1. **Stable ids, never positional.** The four shipped tools all use `"L" + index` as fixture id,
   which changes the moment an array is reordered — the migration AUDIT already flagged this.
   Ids here are slugs (`martin-mac-ultra-performance`) with an `aliases` array for old names.
2. **Colors are tokens, resolved to hex at render.** Pre-Pro stores cable color as a name and
   location color as raw hex from an older palette generation, so re-imported data silently
   repaints. Store `RED`; never a hex. The token table lives at `meta/tokens` and is versioned.
3. **One writer per collection.** Not enforced by the store — writes are last-writer-wins with no
   transactions — so it is enforced by convention, declared in `KTM.OWNERS`, and a tool writes only
   its own collections. This is the rule Pre-Pro broke; it paid with four repair passes
   (`purgeStaleSnakes`, `deduplicateSnakes`, `syncFromLoom`, `repairConnections`) on every init.

## The fixture record

Follows `fixtures.schema.json`, with one deliberate extension.

```json
{
  "name": "MAC Ultra Performance",
  "manufacturer": "Martin",
  "aliases": [],
  "category": "Moving light",
  "power":  { "value": 1450, "unit": "VA", "sourceLabel": null, "sourceUrl": null,
              "retrieved": null, "status": "observed", "assertedBy": ["distro","pull"] },
  "weight": { "value": 97,   "unit": "lb", "...": "same shape" },
  "dmx":    { "footprints": [["Basic",48],["Extended",58]], "default": 48,
              "connector": "5+net", "rdm": true, "rdmStatus": "interpreted" },
  "case":   { "family": "tall", "perCase": 2 },
  "hang":   "omega",
  "flags":  {}
}
```

**The extension is `status: "observed"`** — a fourth state beside `verified`, `interpreted` and
`conflicting`. It means: the shipped tools assert this figure and agree with each other, but no
source is attached. It is the honest state of all 29 seeded records, and it is not a synonym for
"probably fine." Nine of Distro Plot's first-pass wattages were wrong and both traps were
labelling traps — LED-engine wattage read as fixture draw, lamp wattage read as fixture draw — so
`observed` is exactly as trustworthy as the thing that produced it.

The Hub enforces one rule at save time: **a figure cannot be marked `verified` without a
`sourceLabel`.** The label is the finding.

`rdmStatus` seeds as `interpreted` on every record carrying an rdm value, because the audit found
`rdm: true` on 24 fixtures came from a Patch Plot load-time default, not a manufacturer claim.

## Catalogs are one document, not one per item

The aggregation rule has a second half worth stating plainly: a reference catalog is always read
whole, so it is **one document holding an array**, never one document per entry. The 114 Christie
Lites case types are one 15 KB document, not 114 documents burning 2.3% of the cap on rows nobody
ever reads individually.

| Document | Items | Size | Source |
|---|---|---|---|
| `gear/cases` | 114 | 15.0 KB | `Case Weights and Dims (2).xlsx`, Truck Packer repo |
| `gear/truss` | 5 | 2.2 KB | `TRUSS_LIBRARY`, Pre-Pro Truss Builder |
| `gear/rack-equipment` | 8 | 6.8 KB | `BUILTIN_TYPES`, Pre-Pro Rack Builder |
| `gear/pack-items` | 41 | 3.1 KB | `DEFAULT_LIBRARY`, Truck Packer |
| `gear/label-formats` | 4 | 2.6 KB | `LABEL_FORMATS` + `LW/LH/LP`, Pre-Pro Label Builder |
| `gear/network` | 9 | 3.0 KB | Pre-Pro Rack Builder `BUILTIN_TYPES`, plus switches in use |

Two of these were dead data in their source projects and are now live:

- **Case weights and dimensions.** Truck Packer tracks neither weight nor cube, while this
  spreadsheet sat unread in its own repo root. Truck Plot is built on it — it is the whole reason
  Truck Plot can answer "how many trucks and what do they weigh" when Truck Packer cannot.
- **Truss `weightPerFt`.** Real per-manufacturer figures (Tyler GT 3.1, 12" box 2.8, 20.5" box
  5.2, 16" box 3.8, Christie F-Type 3.0 lb/ft) that Pre-Pro defined once and never read anywhere.
  Truss Plot needs exactly this.

Extraction is reproducible: `extract_gear.js` brace-balances each named array literal out of the
legacy sources and evaluates only that literal — the 245 KB Rack Builder file is never otherwise
parsed or run — and `build_gear.py` shapes the four catalog documents.

## Seeded state, 2026-09-10

29 fixture documents written from `data/_migration/fixtures.observed.json`. Every `power` and
`weight` figure is `observed`; nothing is `verified`. Plus the four gear catalogs above.
**33 of 5,000 documents used.**

**The blocking task is unchanged:** attach provenance, starting with the 27 `va` figures — the
attribute with the known failure history. Until that is done the library is a faithful record of
what the tools believe, not a record of what is true.

## The data layer

`KTM` in the Hub source. Every tool goes through it.

- **Reads hit the localStorage cache first.** The UI paints immediately and still opens when the
  store is unreachable. The cache is a cache, never a second source of truth.
- **Writes go to the store, then update the cache.** With no store, a write throws and the UI says
  so rather than pretending it saved.
- **`KTM.P`** builds every path, so segment parity is correct in one place.
- **`KTM.activeShow()`** is the one piece of context every tool needs.

## Known consequence worth remembering

Declaring the `db` capability makes the artifact **organization-internal — it cannot be shared
publicly.** For a solo planning suite whose output leaves as exports, that is the right trade.
But it means the Hub itself is not a link you can send to a vendor. Exports are the delivery path,
by design, which is what Label Plot and the per-tool PDF exports are for.

## Naming

The suite is **KTM Hub**, not Rig Plot. "Rig" is short for rigging, which is a department —
the people who hang truss and motors — so naming the whole suite after it reads as though the
suite belongs to them. The individual tools keep their `… Plot` names. Renamed 2026-09-10, while
the store was still nearly empty: the localStorage prefix is `ktm:`, the data layer object is
`KTM`, and the export format identifier is `ktm-show`.

## How the four ported tools run

Not merged into the Hub's scope — **each runs in its own same-origin `srcdoc` frame.**

That is forced, not stylistic. The four were written independently as standalone artifacts and
share **22 top-level function names** between them: `render`, `compute`, `save`, `esc`, `uid`,
`exportCSV`, `snapshot`, `applySnapshot`, `fillPositions`, `cutLabel` and more. Merged into one
global scope they would silently clobber each other. A frame each means they port byte-for-byte
and keep behaving exactly as they were verified — which matters most for Distro Plot, whose
default state is supposed to demonstrate the FOH position tripping the 5% flag at 9.4%.

The only change to any tool is a shim injected right after `<body>`, ahead of its own code:

- Frames have no capabilities of their own, so the shim hands each tool the Hub's, by direct
  same-origin call into the parent realm. No postMessage, no serialization.
- All four save rigs at `rigs/{key}`. In four separate stores that was fine; in one shared store
  they overwrite each other. So every path a tool builds is namespaced under `tools/<tool>/`.
  **The prefix is two segments on purpose** — document paths must stay even-length, so a
  one-segment prefix would flip every path's parity and throw.
- Theme is owned by the Hub and pushed into each frame on toggle.

Frames are built once and kept alive; switching tools hides and shows them rather than reloading,
so half-entered work survives a tab switch.

`tools/<tool>/rigs/*` is deliberately outside the show tree for now — these are each tool's own
saved rigs, carried over as-is. Folding them into `shows/{showId}/…` is a per-tool migration to do
when that tool is natively integrated, not something to force during the port.

### Assembly

`assemble.py` builds the artifact: it reads the four sources, injects the shim, and embeds them
as JS string literals that the Hub assigns to `iframe.srcdoc`. Assigning from JS rather than
writing a `srcdoc=` attribute means no HTML attribute escaping is involved and the tool markup
survives intact. Bundle is 346 KB against a 16 MB cap.

**Confirmed 2026-09-10:** the artifact host's CSP permits `srcdoc` frames, and all four tools
open inside the Hub. The frame strategy is therefore the suite's architecture, not a trial — the
five remaining tools are built to sit in frames alongside these four, and any tool can later be
natively integrated one at a time without disturbing the others.

## Vendors, and the products-vs-inventory line

Added 2026-09-10 when shop orders became a tool. A shop order is addressed **to** a vendor and
filled **from** that vendor's stock, so vendor is a first-class collection, not a tag on a gear item.

```
vendors/{vendorId}                  identity, contacts, locations
vendors/{vendorId}/catalog/{docId}  that vendor's own stock, rates and case conventions
shows/{showId}/orders/{orderId}     owner: order
```

Seeded: `4wall`, `prg`, `ct`, `christie-lites`, `osa`, `felix`.

The line to hold, and it is the same one that made `gear/cases-christie-lites` a shop-scoped id:

- **`gear/*` is manufacturer product truth.** A Tyler GT truss is 3.1 lb/ft wherever you rent it.
  A MAC Ultra draws 1450 W at every vendor on earth.
- **`vendors/{id}/catalog/*` is one vendor's reality** — what they actually stock, what they call
  it, what case it ships in, what it rents for per week.

The fixture library is never duplicated per vendor. A vendor catalog entry points at a
`fixtures/{id}` and adds only what is vendor-specific.

### Three catalogs a shop order needs that the library did not have

| Document | Items | Why it is separate |
|---|---|---|
| `gear/cable` | 11 types × 6 standard lengths | A shop order is mostly cable by line count |
| `gear/adapters` | 11 | Not fixtures, not cable, and what ruins a load-in when missing |
| `gear/hardware` | 8 | What a show hangs a fixture *with*, vs the fixture's own `hang` field |
| `meta/orderLayout` | 7 sections | Default section order, titles and visibility |

**Cable is a length matrix.** Type down the side, length across the top (5′/10′/15′/25′/50′/100′),
counts in the cells. That is how a shop order reads and how a truck packs — not a flat list.

### The derived number that justifies the powerOut work

Shop Order computes the **two-fer count** from the library rather than asking for it. A fixture
with `powerOut.present === false` cannot be daisy-chained, so every pair of them needs a two-fer;
one with a pass-thru needs none, and `maxLinked` refines it further where the manufacturer
publishes a per-circuit figure. Twenty-one of thirty-five fixtures have no pass-thru. That number
was invisible before this week and it is a real line on a real order.

A fixture whose pass-thru is unknown is **excluded and named**, never assumed either way.

## Rack Plot — shipped 2026-09-10

The largest thing the legacy Pre-Pro suite did that this one had no answer for, and the natural
downstream of Patch Plot: Patch assigns universes, Rack decides which physical port each one
leaves from.

Reads `gear/rack-equipment` (8 devices, each with a real `ports[]` map). Writes
`shows/{showId}/racks/{rackId}`. Native, not legacy — it goes through `window.KTM` and is not
path-namespaced.

Three things worth keeping:

- **RU 1 is the bottom.** An item at `ru:3` with `ruHeight:2` occupies 3 and 4. Elevations draw
  bottom-up with cage-nut rails, because that is how a rack is read in front of a road case.
- **Duplicate universes are the finding, not an error.** `universeIndex()` builds the map across
  *all* racks and flags any universe appearing on two ports. It does not refuse the second one —
  a deliberate duplicate happens, and the tool's job is to make it visible.
- **Port inputs never repaint.** `oninput` writes the model and toggles a CSS class, nothing
  more. A full `render()` on input destroys the DOM and kills tab order, which is the specific
  bug that made Pre-Pro's rack patching unusable for entering forty ports in a row.

Bundle after the port: 454 KB of a 16 MB cap. **51 of 5,000 documents used.**

## Truss List and the Pre-Pro port — 2026-09-13

Truss Plot is rigging-load math and never carried a truss *inventory*; Pre-Pro's Truss Builder
did (named runs, type, length, piece breakdown, colours, end labelling). That concept now lives
in **Truss List**, a native tool writing `shows/{showId}/truss/{trussId}`, one document per run:

```
{ name:"B1", typeName:"TYLER GT TRUSS", lengthFt:40, pieces:{"10":4},
  colors:["RED"], endType:"uds"|"srsl"|"custom", customEnds:["",""], notes, sort }
```

`typeName` points at an item in `gear/truss`; weight is derived (`lengthFt × weightPerFt`),
never stored. Label Plot reads this collection to print joint and end labels; Truss Plot may
later read it to seed positions. `pieces` is keyed by section length so a type with 20 ft
sections and one with 3 m sections both fit.

**Rack port links.** A rack port entry may carry `link`:
`{kind:'rack', rackId, itemKey, portId}` (reciprocal, both ends written by Rack Plot) or
`{kind:'loom', sheetId, cableId, line}` (one-way; Rack Plot reads looms, never writes them).
This replaces Pre-Pro's `connRackId/connItemId/connPortId` and `snakeId/snakeLineId` pairs and
is the source Label Plot uses to print a universe on a snake-line label.

**Loom cable `breakout`** (`CPC4 | CPC8 | SOCA | OTHER | ''`) decides how many lines a cable has
(4 / 8 / 6) and therefore how many snake-line labels it gets.

**Label media added:** `ol285` (1.25×0.75 in, 6×12) and `ol875` (2.625×1 in, 3×10) in
`gear/label-formats`, both with `colGapMm`/`rowGapMm`; older entries keep the single `gapMm`.

**Import.** The shell can now import a `ktm-show` bundle (identity doc plus every row in
`collections`), replacing or copying an existing show. `fixtures` and `gear` inside a bundle are
skipped on import: the library belongs to the Hub, not the show.

**Snake lines on a loom cable.** A CPC cable may carry `lines: [{n, position, universe,
firstFixture}]`, one entry per conductor pair, imported from Pre-Pro's snake data. It is
optional and Loom Plot does not edit it yet; Label Plot uses `lines[n-1].universe` for a snake
line label when no rack port links to that line. `partPositions` stays the six-slot display
array; a CPC8's lines 7 and 8 exist only in `lines`.

**Catalog snapshot.** `data/catalog/` holds read-only copies of `gear/*` and `meta/*` so the
import scripts can validate offline. The live store wins; refresh the snapshot from it.

**Truss Plot native — 2026-09-13.** No longer a legacy frame. Fixtures come from the shared
`fixtures` collection (legacy `L<n>` ids map by name through `LEGACY_LIB`), rigs save at
`shows/{showId}/rigging/{rigId}` (owner: truss), positions can be seeded from Truss List. The
statics tables stay in the tool: `gear/truss` carries no allowable-load rows, and a catalog
`weightPerFt` only replaces a table weight when the two agree within 0.05 lb/ft — the Tyler GT
catalog figure (3.1) does not match the Tomcat LD 12″ table (6.2), so the table wins and the
note says so. Every ported tool is now native; the `LEGACY` shim path applies to none.
