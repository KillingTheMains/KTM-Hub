# KTM Hub — roadmap

Running list. Added to as things come up; nothing here is committed to a date.

## Built

- **The Hub** — shows, fixture library, gear library, store browser.
- **Distro / Patch / Truss / Pull Plot** — ported in as frames, unmodified.
- **Truck Plot** — trailer pack planning: load list, first-fit pack onto 53 × 8.5 ft decks,
  per-truck weight and cube, deck plan SVG, CSV and print.
- **Truss List** (2026-09-13) — per-show truss inventory: runs, type, length, piece auto-fill,
  colours, ends, weight roll-up. The Pre-Pro Truss Builder concept, native.
- **Pre-Pro port** (2026-09-13) — Rack Plot port links (rack↔rack, rack→loom line), splitter
  propagation, copy-to-spare; Loom Plot breakout + Pre-Pro CSV; Label Plot truss / snake-line /
  rack-port / rack-equipment / fixture-ID sources and the six thermal manual types on OL1159LP,
  OL285, OL875 and Rollo 6×4; Hub `ktm-show` import; BMW ABBS 2026 converted to a bundle at
  `data/shows/`. Map of what was taken and left: `docs/prepro-port-map.md`.

---

## 1. Spec-sheet import and manufacturer scraping

**This is the provenance mechanism, not a side feature.** All 29 fixture records are `observed` —
the shipped tools assert them and agree, but nothing sources them. The only thing that turns
`observed` into `verified` is a manufacturer document, and the only thing that makes that cheap
enough to do 29 times is ingest.

Two intakes:

- **Drop a spec sheet in.** A PDF lands on the Hub, gets read, and proposes a fixture record with
  every figure carrying the label the sheet used for it, verbatim. That last part is the whole
  point: `sourceLabel` is required on anything `verified` because the labelling trap is this
  project's known failure mode — nine of Distro Plot's first-pass wattages were wrong, and both
  traps were "LED engine wattage" and "lamp wattage" read as fixture draw. A human confirms
  before anything is written.
- **Fetch from the manufacturer.** Given a make and model, pull the current spec page or PDF and
  do the same. The Bright Data plugin is already installed and is the right tool for this — it
  handles the sites that block plain fetches. Same rule: propose, never auto-commit, and record
  the retrieval date so a figure can go stale visibly.

Applies to truss and rack equipment as much as fixtures. Manufacturer PDFs for five rack devices
are already sitting in Pre-Pro's `reference-docs/` and are the obvious first test.

**Never**: a retailer listing or rental-house page as a `verified` source. Those are `interpreted`
at best.

## 2. Shop-specific gear lists

Different shops carry different gear, and the same fixture comes in a different case at each one.
Truck Packer already models this crudely — `src/data/vendors.js` parses vendor prefixes `CL`,
`4W`, `PRG`, `CT` off item names.

The current seed already has this problem: **`gear/cases` and `gear/pack-items` are both Christie
Lites' catalogs**, sitting under generic names as though they were universal. That is exactly the
kind of wart that becomes permanent, so the ids get shop-scoped now even though the UI comes
later.

The distinction to hold:

- **Products** are manufacturer facts — a Tyler GT truss weighs 3.1 lb/ft wherever you rent it.
  `gear/truss` and `gear/rack-equipment` stay unscoped.
- **A shop's catalog** is that shop's own inventory convention — what a "Quarter Standard" case
  is, what it weighs, how many fixtures it holds. Those get `shop` on the document and a
  shop-scoped id.

Later: a `shops/{shopId}` collection with contacts and notes, a per-show "we are using these
shops" setting, and availability counts if that ever turns out to be worth tracking.

## 3. Takeoff — refined

The key on a lighting plot carries **manufacturer and model**, which is enough to resolve fixture
identity automatically against `fixtures/{id}` and its `aliases`. That is the hard-looking part
and it is actually the easy part.

**Mode is not on the plot, and is not inferable.** It comes from the production electrician. So
the takeoff is explicitly two-phase:

1. **Machine**: read the plot, resolve every fixture to a library id, count them, place them by
   position, pull channel/address/circuit where the paperwork carries it.
2. **Human**: one pass where Jason sets the mode per fixture type. Nothing downstream can be
   computed until that happens, because mode drives the DMX footprint Patch Plot packs against
   and, on some fixtures, the power draw Distro Plot balances.

Design consequence: a takeoff can complete phase 1 and sit in a reviewable state with modes
blank. It is not a failure state, it is the normal handoff point. The UI should make the pending
modes the obvious next action rather than an error.

Intake order stays easiest-first: Lightwright export, then Vectorworks (which exports to
Lightwright anyway), then reading a PDF plot directly.

## 4. Not yet started

- **Rack Plot** — rack elevations and port-level patching.
- **Loom Plot** — cable and loom list with real segment lengths.
- **Net Plot** — switch fabric, VLANs, IP scheme, fiber runs. Least certain of the five;
  alternates are Prep Plot, Crew Plot, Focus Plot.
- **Label Plot** — thermal case labels and truss end labels.

## 5. Loose ends carried forward

- **Provenance on the 27 `va` figures** — still the blocking task for trusting the library.
  Item 1 above is how it gets done.
- **Truck Packer's Firestore rules are written but not deployed.** Unrelated to this suite, but
  it is a live production database currently on open rules.
- **Pieces with no weight.** The 41 pack footprints (truss lengths, carts, straps) have a deck
  footprint but no weight, because Truck Packer never tracked weight. Truck Plot packs them by
  size and excludes them from weight totals rather than guessing. Real weights for those would
  make truck planning materially better.
- **Lighting cases cube out long before they weigh out.** A 120-piece test load filled two decks
  at 13% and 9% of a 44,000 lb payload. Worth remembering when reading Truck Plot's output: deck
  feet is the binding constraint, weight almost never is. The payload cap is there to catch the
  exception, not to drive the plan.

---

## Fixture library — verification pass, 2026-09-10

Six researchers, grouped by manufacturer. All 29 fixtures covered. Rule zero held: they gathered
and cited, never adjudicated, and every conflict came back flagged rather than resolved.

**Draw:** 24 verified · 4 conflicting · 1 with no manufacturer figure at all.

**Power in / pass-thru** — the fields added this pass, and the practically useful result:

| | Count |
|---|---|
| Daisy-chains (has a pass-thru output) | 8 |
| Needs its own home run or a two-fer | 18 |
| Unknown | 3 (all Claypaky) |

**Most big movers do not have a power pass-thru.** All five Robe fixtures, both large Martins,
the JDC1, the Q-7 and the Proteus Maximus are single-inlet. The fixtures that chain are the
smaller LED ones — MAC Aura PXL and XB, Source Four LED S3, ColorSource PAR, Maverick Force S,
Rogue R2 Wash, X4 Bar 20, Diablo-S. That is a cable-order fact, not a trivia fact.

**Connector families do not match across a rig.** powerCON blue A-type (Robe BMFL, Robe Pointe,
Rogue R2 Wash) and powerCON TRUE1 (most modern fixtures) are different cables. Chauvet's Maverick
uses Seetronic Powerkon IP65, not Neutrik. ETC never names the variant on the ColorSource PAR,
Elation never names it on the Proteus Maximus, and SGM ships the Q-7 with a bare-ended tail
someone has to terminate. Those four are flagged `interpreted` — field-check before ordering.

### Four numbers the library had wrong or unsupported

1. **Robe T1 Profile — was 650, is 750 W.** The MSL LED engine is 550 W. 650 matched neither. The
   engine-versus-draw trap, caught.
2. **Claypaky Sharpy — was 440, is 350 VA at 230 V.** Claypaky's own leaflet. 440 matched nothing.
3. **Claypaky Scenius Unico — was 1800, is unknown.** No manufacturer figure for fixture draw
   exists in any accessible source; the only published wattage is the dual-mode lamp (1400/1200 W).
   Discontinued, product page gone, technical docs behind a login. The 1800 has been removed rather
   than kept looking sourced.
4. **ETC ColorSource PAR — ETC's own documents disagree three ways**: 90 W (datasheet), 106 W
   ("typical, Direct at Full"), 120 W ("maximum power consumption"). Size off 120 W until settled.

Two more corrections worth keeping: **Rogue R2 Wash does not support RDM** (confirmed absent from
the whole manual — correcting Patch Plot's load-time default), and the **JEM ZR45 US and EU units
are different hardware**, 1800 W at 120 V versus 2100 W at 230 V, not one rating restated.

### Gaps that need a person, not another search

- Claypaky pass-thru on all three fixtures — behind the login-gated e-assist.tech portal.
- MAC Encore Performance DMX modes: every manual found shows one 38-channel mode, including the
  manual covering firmware 1.0.0. The library's "33ch legacy / fw ≥1.6" split could not be
  confirmed or refuted from primary sources.
- CM Lodestar: CM's own catalog and Entertainment manual disagree on 1-ton full-load current
  (3.7 A vs 3.0 A at 230 V), and no inrush figure is published anywhere.
- Domains worth allowlisting for a second pass: `looksolutionsusa.com` (robots-disallowed),
  `glp.de` (timeouts), `cmco.com` (login shell instead of content).

---

## GDTF ingest, 2026-09-10

Seven GDTF files were already on the Mac under `~/MALightingTechnology/gma3_library/fixturetypes/`.
Parser: `gdtf_read.py`; full notes in `GDTF_NOTES.md`.

**Library is now 35 fixtures** (was 29). Six added from GDTF, then a researcher pass filled the
power fields GDTF does not carry.

### GDTF corrected a fixture already in the library

MAC Ultra Performance carried two modes. The official Martin GDTF has **three** — Compact 42,
Basic 48, Extended 58. The spec-sheet pass had found only one. GDTF is what a console actually
loads, so it wins on modes, and those are now `verified`.

### And a community GDTF was caught carrying a wrong number

The ACME SANA Profile GDTF asserts **5.58 kg**. ACME's own spec sheet and user manual both say
**26 kg**, for a 582 mm moving-head profile — 5.58 kg is not physically plausible. The
manufacturer figure now stands, with the GDTF value recorded as the conflict.

This is the whole justification for the `official` check: the parser reads
`FixtureType@Description` and only marks a file `verified` when it says so outright. Of the seven,
**only the Martin file was official.** The rest are community builds — useful, and wrong at least
once.

### Pass-thru, updated across all 35

| | Count |
|---|---|
| Daisy-chains | 11 |
| Needs a home run or a two-fer | 21 |
| Unknown | 3 (all Claypaky) |

New findings worth carrying to a cable order:

- **Martin RUSH PAR 2 — 18 fixtures per circuit at 230 V, 8 at 120 V.** Highest link count in the
  library. Also **powerCON A-type blue** (NAC3FCA in, NAC3FCB grey out), not TRUE1 — different
  cable from nearly everything else here. Discontinued, but that is a rental-stock reality.
- **Ayrton Rivale Profile — pass-thru, 5 per circuit at 220/230 V, 3 at 110 V.** Ayrton publishes
  the per-circuit figure better than any other manufacturer checked.
- **Ayrton Zonda 9 FX — no pass-thru**, and no per-circuit figure published. So it is not an
  Ayrton-wide convention, it is per fixture.
- **Robe Esprite and iSpiider — no pass-thru.** That is now seven Robe fixtures checked and seven
  with none. Treat single-inlet as the Robe default until one proves otherwise.
- **iSpiider's inlet is TRUE1 in a Seetronic IP65 housing** — the family matches but the housing
  does not, which matters for whether a cable physically seats.

### Two things left unsettled on purpose

- **Ayrton Rivale connector**: Ayrton's own sheet says "True1" in one section while the sibling
  Rivale Profile S sheet says "PowerCON True1 TOP" in the same place. TOP is likely on an IP65
  fixture, but nothing says it outright. Flagged `conflicting` — field-check before ordering.
- **Zonda 9 FX modes**: GDTF has 6 modes to 131 channels; Ayrton's site says 3 modes, 26–199.
  Probably a firmware revision. GDTF figures kept because that is what loads, flagged
  `conflicting` until confirmed on the fixture.

---

## Ideas worth taking from the colleague's tool (2026-09-10)

Rob Smith is building "Felix Lighting — Gear Selector" (RSD Solutions), a single-file HTML
prototype like ours, but aimed at a different problem: **multi-tenant, role-based gear ordering
for a shop** (Admin / PM / Editor / Viewer, tenant switcher, offline toggle). Ours is a solo
production electrician's planning suite. Overlapping catalog, different calculation.

Four things in it worth adopting:

1. **Tenant-configurable report layout.** A side rail lets you reorder sections, hide them, rename
   them, and pick column sets — saved per tenant with per-project overrides. This is directly the
   answer to "everything leaves as a custom export for crew, the shop, and PMs": one shop order,
   several audiences, no re-authoring. Highest-value idea in the two screenshots.
2. **Cable as a length matrix.** Type down the side, lengths across the top (5' / 10' / 15' / 25' /
   50' / 100'), counts in the cells. That is how a shop order actually reads and how a truck
   actually packs. **Loom Plot should be built on this shape**, not a flat cable list.
3. **Adapters as a first-class section.** Cube taps, Edison break-outs, True1 break-outs, gender
   changers, terminators. Not fixtures, not cable, and the thing that ruins a load-in when it is
   missing. Nothing in our roadmap currently owns adapters.
4. **GDTF zip export → Vectorworks.** Populate the library, add fixtures to a show, download every
   GDTF as one zip, drop it into Vectorworks. This closes the loop back to the plot the takeoff
   came from. We already store `gdtf.file` and `fixtureTypeID` per fixture, so the join exists.
   **Caveat before promising it:** the artifact `assets` capability caps at 20 MiB and does not
   obviously accept ZIP, while a single GDTF runs 1–7 MB. Storing the files inside the artifact
   probably will not work — the realistic version fetches from GDTF Share by `fixtureTypeID`, or
   assembles from a local folder.

Also worth noting he tracks **rigging hardware per fixture per show** (trigger clamp,
cheeseborough, safety) and **spare counts as a separate column**. We have a `hang` field on the
fixture but nothing that records what a given show hangs it with, or how many spares go.

### Where our approach is ahead, and why it matters to him too

His fixture rows read "360W · 14.6 lb · True1" with no indication of where any of it came from.
We know the difference between `verified`, `interpreted`, `conflicting` and `observed`, and that
discipline caught four wrong numbers in one day — including a community GDTF asserting 5.58 kg
for a fixture the manufacturer says is 26 kg. A GDTF-fed library without a provenance field will
carry that error silently.

His message says the only thing GDTF omits is power draw. Across seven files we found **power
draw AND connectors** both absent every time. He will hit the connector wall next, and the
pass-thru question after that — which is what actually determines how many True1 jumpers his
cable matrix needs.

---

## Tool slate — settled 2026-09-10

Ten tools, seven shipped. Remaining order: **Loom Plot** (shipped this pass), **Net Plot**,
**Label Plot**.

Jason picked Net Plot for the last slot and asked to keep the alternates in the back pocket rather
than discard them:

- **Prep Plot** — the gap between the shop order and load-in. What arrived, what's short, what
  failed test, what got swapped. Directly downstream of Shop Order, which now exists.
- **Punch Plot** — running punch list per position through load-in and rehearsal. A phone-shaped
  tool, unlike everything else here.
- **Focus Plot** — channel hookup and focus charts. The most direct beneficiary of the takeoff
  once `units[]` is populated: it reads and prints.

**Crew Plot is ruled out** — the existing ADI Workflow app already does crew scheduling, and a
second one would drift out of sync with it.

## Loom Plot — shipped 2026-09-10

Model is Pre-Pro's Loom Builder, which ran BMW in production. Doc per cable sheet at
`shows/{showId}/looms/{sheetId}`, one sheet per position, cables in an array inside it. A sheet is
created from a position with one click, so the sheet list mirrors the rig rather than being typed
a second time.

Carried over verbatim:

- **`parts[6]` paired with `partPositions[6]`** — the field Pre-Pro's own docs omit and the reason
  the tool is worth having. A 100′ socapex run is a cut from the distro, a trunk run and four
  drops, each with its own length and its own place on the rig.
- **The spare convention** — `" SP"` label suffix plus PINK, same type as its primary. A label,
  not a boolean, because crew read it off the tape. The `+SP` button writes exactly that.
- **The assembly grid** — columns are segment slots, the *position* drives the cell colour, and a
  column summary names the positions most-common-first. Reading down a column says what every
  cable is doing at that point in its run.
- **No repaint on input.** Fields write the model and toggle a dirty class. Structural changes
  re-render; edits never do.

New, and the reason the segments were worth storing separately:

- **The cut list.** Every segment rounds *up* to the next standard length in `gear/cable` — a 22′
  run is bought as a 25′ — and aggregates into type × length. That is the matrix a shop order
  reads, so Loom Plot now feeds Shop Order directly. Anything longer than the largest standard
  length is reported as a **custom cut** and named, never silently bucketed.

`meta/tokens` seeded at the same time (14 colours, palette generation 2, plus the spare and
secondary-band conventions). Rule 2 now has something to resolve against: records store `RED`, the
table stores `#ff2020`, and the archived BMW `#ef4444` stays where it belongs.

Bundle 500 KB of a 16 MB cap. **52 of 5,000 documents used.**

## Net Plot — shipped 2026-09-10

Reads `gear/network`, writes `shows/{showId}/network/{planId}` — one document per network *plane*
(lighting, media, comms), each holding its devices and links inline.

Port counts in the catalogue are stored by kind (`{etherconFront:4, fiberSfp:2}`) and expand to
named ports here, because a link has to land somewhere specific and "one of the four front ports"
is not a plan. DMX ports are shown as context and are never offered as a link endpoint — that is
Rack Plot's business. Universe capacity stays unasserted, as the catalogue note says: it is a
property of a node's licence and firmware, not its connector count.

Four checks, each a real load-in failure, and all of them report rather than block:

1. **Duplicate IP** — both devices answer, neither works, and on a show floor the symptom looks
   like a bad cable.
2. **Outside the subnet** — an address that cannot route to the rest of the plane.
3. **Port claimed twice** — invisible on any per-device view; only indexing every link together
   finds it.
4. **No path to the root** — the reason links are a graph and not a list. An isolated switch has
   every field filled, every IP valid, and is still dark. Only walking from the root finds it.

The topology view tiers devices by hop count from the root, so tier 0 is the core and an orphan
has no tier at all — it lands in its own row labelled DARK and cannot be missed.

Picking a fiber port on either end sets the link media automatically, since a fiber port cannot
carry copper and typing it twice is a chance to get it wrong.

## Label Plot — shipped 2026-09-10

Pure output, and the last of the ten. Media geometry from `gear/label-formats`; all three
harvested techniques are implemented rather than described:

- **The font fitter** — binary search 6–520px over canvas `measureText`, 32 iterations, × 0.91,
  bounded on height as well as width so a one-character label cannot size to the width and run off
  the media.
- **Multi-colour ink** — ink and halo computed from the span between the lightest and darkest band,
  never from one colour's luminance. The halo widens as the span grows; a single-colour label gets
  none.
- **The 0.15 mm seam overlap** — each band reaches past its own inner edge so coordinate rounding
  cannot leave hairlines between bands on the printed sheet.

Sources are the tools that write into the show tree: racks, loom cables, loom cases and network
devices. **The four ported tools are deliberately not read** — they still save under
`tools/<tool>/`, so case labels from Pull Plot wait for the day Pull is natively integrated rather
than being asserted in the UI before they work.

A loom case label carries one band per distinct tape colour in the case, first-seen order, capped
at six — which is what makes it readable across a dock.

## Ten of ten, 2026-09-10

Every tool in the Hub is `ready`. Bundle 587 KB of a 16 MB cap; 52 of 5,000 documents.

What is left is no longer construction:

- **Takeoff** — the north star. Lightwright intake first.
- **Native integration of the four ported tools**, one at a time, folding `tools/<tool>/rigs/*`
  into the show tree. Pull Plot first, since it unlocks case labels and the cases the truck packs.
- **Fixture provenance** — the `rdmStatus` sweep, and the open conflicts (ACME SANA weight,
  Ayrton Rivale TRUE1 variant, Zonda 9 FX modes, Claypaky pass-thru ×3).
- **Vendor catalogues** from BOM sheets and past orders.
- **A 4Wall location field** before its catalogue is real.
