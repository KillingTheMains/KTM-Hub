# Pre-Pro Suite → KTM Hub port map

Written 2026-09-13 from a two-agent inventory of both projects. Source reports (scratch, not
kept): `prepro-inventory.md`, `hub-inventory.md`. This is the handoff: what the Hub already
took from Pre-Pro, what is still worth taking, and what is deliberately left behind.

## Where things live

| Project | Location | State |
|---|---|---|
| Pre-Pro Suite (canonical) | `~/Developer/Pre-Pro-Paperwork` | Clean, in sync with GitHub `KillingTheMains/Pre-Pro-Paperwork` main |
| Pre-Pro Suite (Drive copy) | `Cowork Playground/Pre-Pro Paperwork` | `.git` corrupt (missing object), 3 commits behind, "modified" flags are index noise. Only `truss-builder/index.html` actually differs. Extras there (`import-loom-bmw2026.html`, `restore.html`, `pre-pro-suite-fixes.patch`, `_to_delete/`) are superseded or non-code. |
| KTM Hub | `Cowork Playground/RigPlot` | Not a git repo. No GitHub remote. `assemble.py` does not run on the Mac (see Housekeeping). |

## Already taken (do not redo)

- Catalogs: `BUILTIN_TYPES` → `gear/rack-equipment` and `gear/network`; `TRUSS_LIBRARY` →
  `gear/truss` (weightPerFt now live); `LABEL_FORMATS` + `LW/LH/LP` → `gear/label-formats`.
- Loom Builder model: `parts[6]`, `partPositions[6]`, spare ` SP` convention, assembly grid, cut
  list rounding, no-repaint inputs. Loom Plot has CSV, print, Lightwright text export.
- Label Plot techniques: canvas binary-search font fitter (32 iterations, ×0.91), multi-colour
  ink/halo from band luminance, 0.15 mm seam overlap.
- Rack Builder scope is covered by Rack Plot (elevations, DMX ports) plus Net Plot (IP, VLAN,
  fiber, switch ports).

## Still worth taking

Ordered by value. Line numbers refer to the `~/Developer` clone.

### 1. Label Plot: the label types Pre-Pro had and the Hub does not

Label Plot's sources are Manual, Racks, Loom cables, Loom cases, Network. Missing versus Pre-Pro:

| Label | Pre-Pro source | Format | Portable piece |
|---|---|---|---|
| Truss end + joint labels | Truss Builder `generateLabels()` L1211, `_buildPDFBlob()` L1864, `_pdfBands()` L1933, `_haloShadow()` L1818 | OL1159LP 8×2 in, 5/sheet, up to 3 colour bands, US/DS · SR/SL · custom ends | Self-contained. Analytic font fit (no canvas) is a cheaper PDF path than the binary search. |
| CPC snake labels | Rack Builder `_buildCpcColumns()` L4652, `exportCPCLabelsPDF()` L4897, `_interleaveCols()` | OL285 1.25×0.75 in, 6×12, one column per snake, header cell = universe + location | Self-contained grid + interleave. Data comes from Loom/Rack Plot. |
| Port labels (direct, non-snake) | Rack Builder `_buildPortLabelColumns()` L4813, `exportPortLabelsPDF()` L5037 | OL285, filters out opto and unlabeled input ports | Layout self-contained, filter needs Rack Plot's port model. |
| Rack equipment labels | Rack Builder `_rackLabelData()` L4743, `exportRackLabelsPDF()` L4968 | OL875 2.625×1 in, 3×10 | Self-contained. |
| Thermal 4×6: Free text, Fixture (type / ID range / location), Case #, Device (name / unit / address), Shipping | Label Builder | 576×384 px, `calcFsPxWrapped()` L274 word-only wrap | Self-contained. "Fixture" should read `shows/{id}/positions` units; "Device" should read Net Plot devices. |

### 2. Truss Plot: still a legacy frame

Truss Plot is the one tool still on `claude.use("db")`, not `window.KTM`. When it goes native,
fold in from Truss Builder:

- `_autoCalcFromType()` L1279: greedy largest-piece-first fill against the type's real section
  sizes. Two near-duplicate copies in Pre-Pro; port once.
- Per-truss colour (1–3 colours), end type (`uds` / `srsl` / `custom`), notes.
- Roadmap items Pre-Pro never built: truck-space estimator (Truck Plot now owns this), weight
  summary by type (Truss Plot has weightPerFt, so this is a roll-up).

### 3. Rack Plot: small behaviours

- Splitter universe propagation, ~15 lines inside `savePort()` around L3138: when an input port
  on a splitter type gets universe X, stamp X on every output port that is blank or still held
  the old input value.
- `copyUniversesToSpare()`: copy a device's universe map onto its matching spare device.
- Check whether Rack Plot has port-to-port cross-rack links and snake break-in links. Pre-Pro
  stored both on the port (`connRackId/connItemId/connPortId`, `snakeId/snakeLineId`) and
  rendered a connection badge (`connInfo()`). If Rack Plot lacks it, this is the largest
  remaining Rack Builder feature.
- `exportSchematicPDF()` L3067: SVG → canvas at 2× → jsPDF at Letter / Legal / ARCH D / ARCH E.
  Generic pipeline, useful for any Hub tool that draws SVG (Rack, Truck, Net).

### 4. Loom Plot: export compatibility

Match Pre-Pro's exact shapes so old spreadsheets still open:

- Cable CSV header: `Location,Label,Color,SecColor,Type,Parts,Breakout,LoomCase,Notes`; Parts is
  the six segments joined with `+`, empties kept.
- Lightwright text line: `<label>: <part> <type>, <part> <type>, …`, grouped under
  `=== <Location> ===`, header `LIGHTWRIGHT CABLE STRINGS — <show>`.
- Order-sheet CSV (`exportInventoryCSV()` L1985): `Item,Detail,Qty Needed,Qty Ordered,Remaining`
  with a literal `=C<n>-D<n>` formula in Remaining. Shop Order may already supersede this; if so,
  drop the formula trick rather than copy it.

### 5. Real show data as a test fixture

The BMW 2026 show exists in Pre-Pro as loom list, breakouts, network layout, and power calc
spreadsheets plus `import-loom-bmw2026.html`. Importing it into the Hub as a show is the best
end-to-end test the suite can have, and it exercises the takeoff path the roadmap calls the
north star. Pre-Pro's `reference-docs/` PDFs (GigaCore 10, ProPlex 1616, LumiNode 12, LumiSplit,
XSP/XSR) are the provenance sources roadmap item 1 already names.

## Deliberately left behind

- `syncFromLoom()`, `deduplicateSnakes()`, `repairConnections()`, `purgeStaleSnakes()`: repair
  passes that exist because Pre-Pro let two tools write the same data. The Hub's one-writer rule
  removes the need. Keep only the design lesson: bidirectional refs need one authoritative side.
- Full `render()` on input. Already rejected in the Hub.
- Landing page multi-show manager with GitHub Contents API push/pull (`pushShow()` L549,
  `pullShow()` L575, PAT in localStorage) and share links. Undocumented in Pre-Pro's CLAUDE.md.
  The Hub has a real store and `ktm-show` export, so this is not needed. Note the pattern in case
  the Hub ever needs a public share path, since the `db` capability makes it org-internal.
- `_driveScheduleSync()` Google Drive auto-backup, duplicated in Rack and Loom Builder.
- Per-tool localStorage keys and the `pps_suite` identity record.

## Housekeeping

- `assemble.py` fails on the Mac: `UPLOADS` points at `/mnt/user-data/uploads/RigPlot` (the
  Cowork VM path) and it reads `shim.js` where the file is `ktm-shim.js`. Two-line fix.
- RigPlot has no git history. Making it a repo (and pushing to GitHub like Pre-Pro) is the
  prerequisite for working on it from both Claude Code and Cowork without a Drive sync race.
  `gdtf-share.json` holds credentials and must be gitignored first.
- The Drive copy of Pre-Pro should be re-cloned or removed; its `.git` cannot traverse history.
- `gh` is not installed; git push works over https if the keychain credential is present.
