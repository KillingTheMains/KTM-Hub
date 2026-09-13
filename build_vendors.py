"""Vendor framework + the catalogs a shop order needs.

A shop order is addressed TO a vendor and priced FROM that vendor's stock, so
vendor is a first-class thing, not a tag on a gear item.

The distinction that matters:
  gear/*            manufacturer products. A Tyler GT truss is 3.1 lb/ft anywhere.
  vendors/{id}/*    one vendor's own reality — what they stock, what they call it,
                    what case it ships in, what it rents for.

Cable and adapters are new here. Neither existed in the library, and a shop
order is mostly cable and adapters by line count.
"""
import json, pathlib

OUT = pathlib.Path(__file__).parent / "vendors"; OUT.mkdir(exist_ok=True)
D = "2026-09-10"
batch = []

def w(coll, doc_id, body, sub=None):
    body["updatedAt"] = D + "T20:00:00.000Z"
    p = OUT / f"{coll.replace('/','_')}_{doc_id}.json"
    p.write_text(json.dumps(body, indent=1, ensure_ascii=False))
    batch.append({"op": "set", "collection": coll, "doc_id": doc_id,
                  "file_path": str(p.resolve())})

# ── vendors ───────────────────────────────────────────────────────────────
VENDORS = [
    {"id": "4wall", "name": "4Wall Entertainment", "shortCode": "4W",
     "note": "Multiple locations; stock varies by branch, so a location field will matter here."},
    {"id": "prg", "name": "PRG", "shortCode": "PRG", "note": ""},
    {"id": "ct", "name": "CT", "shortCode": "CT",
     "note": "Full legal name to confirm."},
    {"id": "christie-lites", "name": "Christie Lites", "shortCode": "CL",
     "note": "Case catalog and trailer pack footprints already seeded from their own data — "
             "the only vendor with real inventory in the store so far."},
    {"id": "osa", "name": "OSA International", "shortCode": "OSA",
     "note": "Full legal name to confirm."},
    {"id": "felix", "name": "Felix Lighting", "shortCode": "FLX", "note": ""},
]
for v in VENDORS:
    w("vendors", v["id"], {
        "name": v["name"], "shortCode": v["shortCode"], "note": v["note"],
        "contacts": [],          # {name, role, email, phone}
        "locations": [],         # branch/warehouse names
        "active": True,
    })

# ── cable catalog ─────────────────────────────────────────────────────────
# Lengths are the columns of the shop-order matrix. This is the shape a shop
# order actually reads: type down the side, length across the top.
LENGTHS = [5, 10, 15, 25, 50, 100]
CABLE = [
    ("true1-jumper",   "True1 Jumper",       "power", "powerCON TRUE1", ""),
    ("true1-tail",     "True1 Tail (bare)",  "power", "powerCON TRUE1", "For fixtures shipped with bare-ended tails"),
    ("powercon-blue",  "powerCON Blue Jumper","power","powerCON A-type", "NOT interchangeable with TRUE1"),
    ("edison-uground", "Edison U-Ground",    "power", "NEMA 5-15", ""),
    ("socapex",        "Socapex 19-pin",     "power", "Socapex", "6 circuits per run"),
    ("cpc8",           "CPC8",               "power", "CPC8", "8 circuits"),
    ("cpc4",           "CPC4",               "power", "CPC4", "4 circuits"),
    ("dmx-5pin",       "5-Pin DMX",          "data",  "XLR-5", ""),
    ("dmx-3pin",       "3-Pin DMX",          "data",  "XLR-3", ""),
    ("ethercon",       "EtherCON Cat5e",     "data",  "etherCON RJ45", ""),
    ("fiber",          "Fiber (LC duplex)",  "data",  "LC", ""),
]
w("gear", "cable", {
    "kind": "cable", "name": "Cable types",
    "source": "Pre-Pro Loom Builder cable types plus the shop-order conventions in use",
    "note": "Standard lengths are the shop-order matrix columns. A shop order is mostly cable "
            "by line count, which is why it gets its own catalog rather than living in notes.",
    "lengths": LENGTHS,
    "items": [{"id": i, "name": n, "class": c, "connector": conn, "note": note}
              for i, n, c, conn, note in CABLE],
})

# ── adapters ──────────────────────────────────────────────────────────────
# Not fixtures, not cable, and the thing that ruins a load-in when it is missing.
ADAPTERS = [
    ("cube-tap",        "Cube Tap",                 "power", "Edison 1-to-3"),
    ("edison-breakout", "Edison Break Out",         "power", "Socapex to 6x Edison"),
    ("true1-breakout",  "True1 Break Out",          "power", "Socapex to 6x TRUE1"),
    ("true1-twofer",    "True1 Two-fer",            "power", "One circuit, two fixtures — needed wherever a fixture has no pass-thru"),
    ("edison-twofer",   "Edison Two-fer",           "power", "One circuit, two fixtures"),
    ("l6-20-to-edison", "L6-20 to Edison",          "power", ""),
    ("dmx-3m-5f",       "3-Pin M to 5-Pin F",       "data",  ""),
    ("dmx-5m-3f",       "5-Pin M to 3-Pin F",       "data",  ""),
    ("dmx-term-3",      "3-Pin Terminator",         "data",  "120 ohm"),
    ("dmx-term-5",      "5-Pin Terminator",         "data",  "120 ohm"),
    ("ethercon-coupler","EtherCON Coupler",         "data",  ""),
]
w("gear", "adapters", {
    "kind": "adapter", "name": "Adapters",
    "source": "Shop-order practice; category adopted after seeing it as a first-class section "
              "in a colleague's tool",
    "note": "The two-fer entries are the ones the fixture library now drives directly: 21 of 35 "
            "fixtures have no power pass-thru, and each of those needs its own home run or a two-fer.",
    "items": [{"id": i, "name": n, "class": c, "note": note} for i, n, c, note in ADAPTERS],
})

# ── rigging hardware ──────────────────────────────────────────────────────
# What a given show hangs a fixture WITH, as opposed to the fixture's own
# `hang` field which records what it ships with.
HARDWARE = [
    ("safety",          "Safety Cable",        "Required on every hung fixture"),
    ("trigger-clamp",   "Trigger Clamp",       ""),
    ("cheeseborough",   "Cheeseborough",       "Right-angle clamp"),
    ("half-coupler",    "Half Coupler",        ""),
    ("mega-clamp",      "Mega Clamp",          ""),
    ("omega-bracket",   "Omega Bracket",       "Usually ships with the fixture"),
    ("truss-hook",      "Truss Hook",          ""),
    ("drop-arm",        "Drop Arm",            ""),
]
w("gear", "hardware", {
    "kind": "hardware", "name": "Rigging hardware",
    "source": "Shop-order practice",
    "note": "A fixture's own `hang` field says what it ships with. This is what a particular "
            "show hangs it with, which is a per-order decision and often differs.",
    "items": [{"id": i, "name": n, "note": note} for i, n, note in HARDWARE],
})

# ── default shop-order layout ─────────────────────────────────────────────
# Section order, visibility and titles, configurable per order. Taken from the
# colleague's tenant-config idea, which is the right answer to "one order,
# several audiences".
w("meta", "orderLayout", {
    "name": "Shop order layout — defaults",
    "note": "Every order copies this and can override it. Reorder, retitle or hide a section "
            "without re-authoring the order.",
    "sections": [
        {"key": "fixtures",  "title": "Fixtures",          "visible": True},
        {"key": "cable",     "title": "Power / Data Cable","visible": True},
        {"key": "adapters",  "title": "Adapters",          "visible": True},
        {"key": "hardware",  "title": "Rigging Hardware",  "visible": True},
        {"key": "control",   "title": "Control & Distro",  "visible": True},
        {"key": "truss",     "title": "Truss",             "visible": False},
        {"key": "totals",    "title": "Totals",            "visible": True},
    ],
})

pathlib.Path(__file__).parent.joinpath("vendor_batch.json").write_text(json.dumps(batch, indent=1))
for b in batch:
    body = json.loads(pathlib.Path(b["file_path"]).read_text())
    n = len(body.get("items", body.get("sections", [])))
    print(f"  {b['collection']}/{b['doc_id']:<16} {body.get('name','')[:34]:<36}{n or ''}")
print(f"\n{len(batch)} documents")
