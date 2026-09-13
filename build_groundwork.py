"""Catalogs the remaining tools need before they can be built.

Groundwork, not scaffolding. Each of these is real reference data a tool will
read on day one — seeding it now means the tool gets written against something
rather than inventing its own copy, which is how the legacy projects ended up
with the same fixture in four places.

  gear/label-formats   Label Plot   — media geometry, harvested from Pre-Pro
  gear/network         Net Plot     — switches, nodes, media converters
"""
import json, pathlib

OUT = pathlib.Path(__file__).parent / "vendors"
D = "2026-09-10"
batch = []

def w(coll, doc_id, body):
    body["updatedAt"] = D + "T21:00:00.000Z"
    p = OUT / f"{coll}_{doc_id}.json"
    p.write_text(json.dumps(body, indent=1, ensure_ascii=False))
    batch.append({"op": "set", "collection": coll, "doc_id": doc_id,
                  "file_path": str(p.resolve())})

# ── label media ───────────────────────────────────────────────────────────
# Geometry verified in Pre-Pro's Truss Builder and Label Builder source. These
# are physical media dimensions, so they are products, not vendor inventory.
w("gear", "label-formats", {
    "kind": "label-format", "name": "Label media",
    "source": "LABEL_FORMATS in Pre-Pro Truss Builder; LW/LH/LP constants in Pre-Pro Label Builder",
    "note": "Sheet formats are millimetres on US Letter. The Rollo format is a 6x4in thermal "
            "label expressed at 96dpi CSS pixels, which is how the generator lays it out.",
    "items": [
        {"id": "ol1159lp", "name": "OL1159LP", "kind": "sheet", "wMm": 203.2, "hMm": 50.8,
         "cols": 1, "rows": 5, "page": "letter",
         "marginTopMm": 12.7, "marginSideMm": 6.35, "gapMm": 0,
         "note": '8" x 2", 5 per sheet. Truss end labels.'},
        {"id": "ol125", "name": "OL125", "kind": "sheet", "wMm": 101.6, "hMm": 50.8,
         "cols": 2, "rows": 5, "page": "letter", "note": '4" x 2", 10 per sheet.'},
        {"id": "ol75", "name": "OL75", "kind": "sheet", "wMm": 101.6, "hMm": 25.4,
         "cols": 2, "rows": 10, "page": "letter", "note": '4" x 1", 20 per sheet.'},
        {"id": "rollo-6x4", "name": "Rollo 6x4 thermal", "kind": "thermal",
         "wPx": 576, "hPx": 384, "padPx": 20, "dpi": 96, "previewScale": 0.551,
         "note": 'One label per page at @page{size:6in 4in;margin:0}. Case, shipping and rack labels.'},
    ],
    "techniques": {
        "fontFit": "Binary search 6-520px over canvas measureText, 32 iterations, result x0.91 "
                   "for safety margin. jsPDF cannot measure text, so PDF output sizes "
                   "analytically from Helvetica-Bold's ~0.62em average advance instead.",
        "multiColourInk": "Ink and halo are computed from the SPAN between the lightest and "
                          "darkest colour band on a label, not from a single colour's luminance. "
                          "Halo stroke widens as the span grows. A single-colour luminance test "
                          "fails as soon as a label carries two bands.",
        "seams": "Colour bands are painted with a 0.15mm inner-edge overlap to kill hairline "
                 "seams from coordinate rounding.",
    },
})

# ── network devices ───────────────────────────────────────────────────────
# Net Plot plans the fabric that carries what Patch Plot assigns. The rack
# equipment catalog already holds the DMX side; this is the ethernet side.
w("gear", "network", {
    "kind": "network", "name": "Network devices",
    "source": "Pre-Pro Rack Builder BUILTIN_TYPES for the port counts already verified there, "
              "plus the switches in common use on these rigs",
    "note": "Port counts here are physical ports. Universe capacity is a property of the node's "
            "licence and firmware, not the connector count, and is deliberately not asserted — "
            "that is a per-device figure a researcher pass should source.",
    "items": [
        {"id": "gigacore-10", "name": "GigaCore 10", "manufacturer": "Luminex", "ru": 1,
         "ports": {"etherconFront": 4, "etherconRear": 4, "fiberSfp": 2},
         "poe": None, "note": "Verified against Pre-Pro's own roster."},
        {"id": "gigacore-14r", "name": "GigaCore 14R", "manufacturer": "Luminex", "ru": 1,
         "ports": {"ethercon": 12, "fiberSfp": 2}, "poe": None, "note": "Port count to verify."},
        {"id": "gigacore-16xt", "name": "GigaCore 16Xt", "manufacturer": "Luminex", "ru": 1,
         "ports": {"ethercon": 12, "fiberSfp": 4}, "poe": None, "note": "Port count to verify."},
        {"id": "luminode-12", "name": "LumiNode 12", "manufacturer": "Luminex", "ru": 1,
         "ports": {"dmxOut": 12, "ethercon": 2}, "note": "Verified against Pre-Pro's own roster."},
        {"id": "luminode-4", "name": "LumiNode 4", "manufacturer": "Luminex", "ru": 1,
         "ports": {"dmxOut": 4, "ethercon": 2}, "note": "To verify."},
        {"id": "proplex-iq-two-1616", "name": "ProPlex IQ Two 1616", "manufacturer": "TMB", "ru": 2,
         "ports": {"dmxBidirectional": 16, "ethercon": 2},
         "note": "Verified: 16 bidirectional XLR5 plus 2 etherCON."},
        {"id": "ma3-npu", "name": "MA3 NPU", "manufacturer": "MA Lighting", "ru": 2,
         "ports": {"dmxOut": 8}, "note": "Ports A-H. Verified against Pre-Pro's own roster."},
        {"id": "swisson-xnd-8", "name": "Swisson XND-8", "manufacturer": "Swisson", "ru": 1,
         "ports": {"dmxOut": 8, "ethercon": 2}, "note": "To verify."},
        {"id": "media-converter", "name": "Fiber media converter", "manufacturer": "—", "ru": 0,
         "ports": {"ethercon": 1, "fiberSfp": 1}, "note": "Generic; note the fiber type per show."},
    ],
    "ipConventions": {
        "note": "Placeholder for the show-level IP plan Net Plot will own. Not asserted here "
                "because it is a per-show decision, not a product fact.",
        "common": ["2.x.x.x / 255.0.0.0 (Art-Net legacy)",
                   "10.x.x.x / 255.0.0.0",
                   "192.168.x.x / 255.255.255.0"],
    },
})

pathlib.Path(__file__).parent.joinpath("groundwork_batch.json").write_text(json.dumps(batch, indent=1))
for b in batch:
    body = json.loads(pathlib.Path(b["file_path"]).read_text())
    print(f"  {b['collection']}/{b['doc_id']:<16} {body['name']:<20} {len(body['items'])} items")
