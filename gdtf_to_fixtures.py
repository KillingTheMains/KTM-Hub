"""Turn parsed GDTF into KTM Hub fixture records.

GDTF carries modes, weight and dimensions. It does NOT carry power draw or
power connectors — zero of the seven files tested populated either. So these
records land deliberately INCOMPLETE: power fields exist with status `missing`
so the gap is visible in the library rather than silently absent, and a
researcher pass fills them from manufacturer documents.

Mode status follows the file's own provenance claim: `verified` only when
FixtureType@Description says the file is official, `interpreted` otherwise.
"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from gdtf_read import parse

SRC  = pathlib.Path("/mnt/user-data/uploads/RigPlot/gdtf")
OUT  = pathlib.Path(__file__).parent / "verified"; OUT.mkdir(exist_ok=True)
D    = "2026-09-10"
SKIP = {"martin-mac-ultra-performance"}          # already in the library

# Manufacturer names as the library spells them, and a category per fixture.
BRAND = {"Martin Professional": "Martin", "Robe Lighting": "Robe",
         "Ayrton": "Ayrton", "ACME": "ACME"}
CATEGORY = {
    "robe-robin-esprite":      "Moving light",
    "robe-robin-ispiider":     "Moving light",
    "ayrton-rivale-profile":   "Moving light",
    "ayrton-zonda-9-fx":       "Moving light",
    "martin-rush-par-2-rgbw-zoom": "Wash / bar / strobe",
    "acme-sana-profile":       "Moving light",
}
ID_FIX = {  # tidy the ids the raw names would slug into
    "acme-acme-sana-profile-xa-300-bswf-ip": "acme-sana-profile",
    "martin-rush-par-2-rgbw-zoom": "martin-rush-par-2-rgbw-zoom",
}

def slug(b, n):
    s = re.sub(r"[^a-z0-9]+", "-", f"{b} {n}".lower()).strip("-")
    return ID_FIX.get(s, s)

def gap(unit, why):
    return {"value": None, "unit": unit, "sourceLabel": None, "sourceUrl": None,
            "retrieved": None, "status": "missing", "note": why}

GDTF_NO_POWER = ("GDTF carries no power data for this fixture — the format has elements for "
                 "consumption and connectors but none of the seven files tested populated them. "
                 "Needs a manufacturer document.")

batch, made = [], []
for f in sorted(SRC.glob("*.gdtf")):
    g = parse(f)
    brand = BRAND.get(g["manufacturer"], g["manufacturer"])
    fid = slug(brand, g["name"])
    if fid in SKIP:
        continue

    modes = [[m["name"], m["footprint"]] for m in g["modes"]]
    default = max(modes, key=lambda m: m[1])[1] if modes else None

    doc = {
        "name": g["longName"] or g["name"],
        "manufacturer": brand,
        "aliases": sorted({x for x in (g["name"], g["longName"], g["shortName"]) if x}
                          - {g["longName"] or g["name"]}),
        "category": CATEGORY.get(fid, "Moving light"),

        # ── from GDTF ──────────────────────────────────────────────────────
        "dmx": {
            "footprints": modes, "default": default,
            "connector": None, "rdm": None,
            "status": g["provenanceStatus"],
            "sourceLabel": "DMXModes in the GDTF file",
            "sourceUrl": "gdtf:" + g["file"].replace(".gdtf", ""),
            "retrieved": D,
            "note": ("Footprint is the highest DMX offset each mode occupies, not its "
                     "channel-node count. " + ("Official manufacturer file."
                      if g["official"] else
                      "Community-published file, not manufacturer-authored — modes are "
                      "reliable in practice but recorded as interpreted, not verified.")),
        },
        "weight": ({"value": g["weightLb"], "unit": "lb", "sourceValue": g["weightKg"],
                    "sourceUnit": "kg", "sourceLabel": "Properties/Weight in the GDTF file",
                    "sourceUrl": "gdtf:" + g["file"].replace(".gdtf", ""), "retrieved": D,
                    "status": g["provenanceStatus"]}
                   if g["weightLb"] else gap("lb", "Not populated in the GDTF file.")),

        # ── deliberately absent, flagged so the library shows the hole ──────
        "power":    gap("VA", GDTF_NO_POWER),
        "powerIn":  {"connector": None, "voltageRange": None, "sourceLabel": None,
                     "sourceUrl": None, "retrieved": None, "status": "missing",
                     "note": GDTF_NO_POWER},
        "powerOut": {"present": None, "connector": None, "maxLinked": None,
                     "sourceLabel": None, "sourceUrl": None, "retrieved": None,
                     "status": "missing", "note": GDTF_NO_POWER},

        "case": {"family": None, "perCase": None},
        "hang": None, "flags": {},
        "gdtf": {"file": g["file"], "fixtureTypeID": g["fixtureTypeID"],
                 "official": g["official"], "shortName": g["shortName"],
                 "revision": (g["revisions"][0]["date"] if g["revisions"] else None),
                 "dimensionsM": g["dimensions"]},
        "addedFrom": "gdtf", "updatedAt": D + "T18:30:00.000Z",
    }
    p = OUT / f"{fid}.json"
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    batch.append({"op": "set", "collection": "fixtures", "doc_id": fid,
                  "file_path": str(p.resolve())})
    made.append((fid, brand, doc["name"], len(modes), default, g["weightLb"], g["official"]))

pathlib.Path(__file__).parent.joinpath("gdtf_batch.json").write_text(json.dumps(batch, indent=1))
print(f"{'id':<30}{'fixture':<28}{'modes':>6}{'max ch':>8}{'lb':>7}  official")
print("-"*88)
for fid, brand, name, nm, dflt, lb, off in made:
    print(f"{fid:<30}{(brand+' '+name)[:26]:<28}{nm:>6}{dflt or '—':>8}{lb or '—':>7}  {'yes' if off else 'no'}")
print(f"\n{len(batch)} new fixture records — power, connector and pass-thru all `missing`")
