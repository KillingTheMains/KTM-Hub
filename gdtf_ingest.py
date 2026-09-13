"""Ingest a folder of .gdtf files into KTM Hub fixture records — MERGING,
never overwriting.

This is the step that runs whether a file arrived from the GDTF Share API or
was dragged into the folder by hand. The download is the easy half; this is
the half that has to be careful.

THE RULE, and it is the whole point:

    GDTF is authoritative for DMX modes and nothing else.

So a merge only ever WRITES modes. Every other field it touches — weight,
dimensions — is compared against what the library already holds and, when the
two disagree beyond tolerance, recorded as a CONFLICT rather than replaced.
That rule is not theoretical: a community GDTF for the ACME SANA asserts
5.58 kg for a fixture its manufacturer publishes at 26 kg, a 4.6x error. An
overwriting importer would have silently destroyed the right number.

Power is never taken from GDTF at all. Across every file tested, zero
populated power draw and zero populated power connectors — the spec has the
fields, manufacturers leave them empty. An empty element is not zero.

Existing records are read from lib/fixtures/*.json, which is a snapshot of the
live library pulled with read_db. Anything not already in the library becomes a
NEW record with power fields deliberately marked `missing`, so the gap is
visible rather than absent.
"""
import json, pathlib, re, sys, argparse
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from gdtf_read import parse

HERE = pathlib.Path(__file__).parent
LIB  = HERE / "lib" / "fixtures"
OUT  = HERE / "ingest"; OUT.mkdir(exist_ok=True)

# How the library spells each manufacturer, against how GDTF files spell it.
BRAND = {
    "martin professional":"Martin", "martin":"Martin", "robe lighting":"Robe",
    "robe":"Robe", "ayrton":"Ayrton", "acme":"ACME", "claypaky":"Claypaky",
    "clay paky":"Claypaky", "chauvet professional":"Chauvet", "chauvet":"Chauvet",
    "elation professional":"Elation", "elation":"Elation", "etc":"ETC",
    "glp":"GLP", "german light products":"GLP", "sgm":"SGM",
    "ma lighting":"MA Lighting", "high end systems":"High End Systems",
    "vari-lite":"Vari-Lite", "varilite":"Vari-Lite", "prolights":"Prolights",
    "jb-lighting":"JB-Lighting", "cameo":"Cameo", "adj":"ADJ", "look":"Look",
}
def brand(m):
    return BRAND.get(str(m or "").strip().lower(), str(m or "").strip())

def slug(b, n):
    s = f"{b} {n}".lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    return re.sub(r"[\s_]+", "-", s).strip("-")

def gap(unit, why):
    """A field we know we do NOT have. Present so the hole is visible."""
    return {"value": None, "unit": unit, "sourceLabel": None, "sourceUrl": None,
            "retrieved": None, "status": "missing", "note": why}

def close(a, b, tol=0.06):
    try: return abs(float(a)-float(b)) <= max(abs(float(b))*tol, 0.5)
    except (TypeError, ValueError): return False

def merge_one(g, existing, date, fid_hint=None):
    """Return (record, notes). `existing` is None for a fixture we do not hold."""
    notes = []
    b, n = brand(g.get("manufacturer")), (g.get("name") or "").strip()
    fid  = fid_hint or slug(b, n)   # keep the library's own id when it has one

    modes = [[m["name"], m["footprint"]] for m in (g.get("modes") or [])]
    modes.sort(key=lambda x: x[1])
    src = {"sourceLabel": f"GDTF {g.get('file','')}",
           "sourceUrl": "https://gdtf-share.com/",
           "retrieved": date,
           "status": g.get("provenanceStatus") or "interpreted"}

    rec = dict(existing) if existing else {
        "name": n, "manufacturer": b, "aliases": [], "category": None,
        "power":  gap("VA", "GDTF carries no power draw for this fixture; needs a manufacturer source"),
        "weight": gap("lb", "not yet sourced"),
        "case": {}, "hang": None, "flags": {},
    }
    rec.pop("id", None); rec.pop("version", None)

    # ── modes: GDTF wins, because this is what it is for ──────────────────
    if modes:
        prev = ((existing or {}).get("dmx") or {}).get("footprints")
        rec.setdefault("dmx", {})
        rec["dmx"] = dict(rec.get("dmx") or {})
        rec["dmx"]["footprints"] = modes
        rec["dmx"]["default"] = modes[0][1]
        rec["dmx"]["modeSource"] = src
        if prev and [list(x) for x in prev] != modes:
            notes.append(f"{fid}: modes replaced from GDTF ({len(prev)} → {len(modes)})")

    # ── weight: compare, never replace ────────────────────────────────────
    lb = g.get("weightLb")
    if lb:
        cur = (rec.get("weight") or {}).get("value")
        if cur in (None, 0):
            rec["weight"] = {"value": round(lb,1), "unit":"lb", **src,
                             "sourceLabel": src["sourceLabel"]+" (Weight attribute)"}
        elif not close(lb, cur):
            # The ACME lesson. Keep what is there; record the disagreement.
            # The library already uses `conflicting` for this; do not invent a
            # second key for the same idea.
            w = dict(rec["weight"]); w["status"] = "conflicting"
            w["conflicting"] = list(w.get("conflicting") or [])
            already = any(close(c.get("value"), lb) or close(c.get("value"), g.get("weightKg"))
                          for c in w["conflicting"])
            if not already:
                w["conflicting"].append(
                    {"value": round(lb,1), "unit":"lb", "sourceLabel": src["sourceLabel"],
                     "retrieved": date, "note": "GDTF Weight attribute disagrees with the held figure"})
            rec["weight"] = w
            notes.append(f"{fid}: WEIGHT CONFLICT — held {cur} lb, GDTF says {round(lb,1)} lb")

    # ── dimensions and identity, additive only ────────────────────────────
    d = g.get("dimensions")
    if d and not rec.get("dimensions"):
        rec["dimensions"] = {**d, "source": src["sourceLabel"], "retrieved": date}
    gd = rec.setdefault("gdtf", {})
    gd.update({"fixtureTypeID": g.get("fixtureTypeID"), "file": g.get("file"),
               "dataVersion": g.get("dataVersion"), "official": bool(g.get("official")),
               "retrieved": date})
    if g.get("revisions"):
        gd["latestRevision"] = g["revisions"][-1].get("date")

    # Names the plot's key might use, so a takeoff join still lands.
    for alt in filter(None, [g.get("longName"), g.get("shortName"), n]):
        if alt != rec.get("name") and alt not in rec.get("aliases", []):
            rec.setdefault("aliases", []).append(alt)

    if not existing:
        notes.append(f"{fid}: NEW — power missing, needs a researcher pass")
    rec["updatedAt"] = date + "T00:00:00.000Z"
    return fid, rec, notes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="folder of .gdtf files, or a parsed .json from gdtf_read")
    ap.add_argument("--date", default="2026-09-10")
    a = ap.parse_args()

    p = pathlib.Path(a.src)
    parsed = json.loads(p.read_text()) if p.suffix == ".json" else [
        parse(f) for f in sorted(p.glob("*.gdtf"))]

    have, byUUID, byAlias = {}, {}, {}
    for f in LIB.glob("*.json"):
        doc = json.loads(f.read_text())
        rec = doc.get("data", doc)
        have[f.stem] = rec
        u = (rec.get("gdtf") or {}).get("fixtureTypeID")
        if u: byUUID[u.upper()] = f.stem
        for al in [rec.get("name")] + list(rec.get("aliases") or []):
            if al: byAlias[slug(brand(rec.get("manufacturer")), al)] = f.stem

    def match(g):
        """Find the library record this file is about.

        Slug alone is not enough and the ACME file proves it: GDTF calls it
        "ACME SANA PROFILE (XA 300 BSWF IP)" — brand repeated in the name, plus
        the model code — while the library calls it "SANA Profile". A slug-only
        importer creates a duplicate and splits the fixture in two, which is
        worse than not importing at all.

        So: fixtureTypeID first (a real identity, stable across revisions and
        renames), then the aliases already on the record, then the slug, then
        the slug with a repeated brand prefix stripped.
        """
        u = (g.get("fixtureTypeID") or "").upper()
        if u and u in byUUID: return byUUID[u]
        b, n = brand(g.get("manufacturer")), (g.get("name") or "").strip()
        for cand in [slug(b, n), byAlias.get(slug(b, n))]:
            if cand and cand in have: return cand
        if n.lower().startswith(b.lower()):
            s2 = slug(b, n[len(b):].strip())
            if s2 in have: return s2
            if byAlias.get(s2) in have: return byAlias[s2]
        return None

    batch, allnotes, new, upd = [], [], 0, 0
    for g in parsed:
        if g.get("error"): allnotes.append(f"SKIP {g.get('file')}: {g['error']}"); continue
        hit = match(g)
        fid, rec, notes = merge_one(g, have.get(hit), a.date, hit)
        (OUT / f"{fid}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
        batch.append({"op":"set","collection":"fixtures","doc_id":fid,
                      "file_path": str((OUT/f"{fid}.json").resolve())})
        allnotes += notes
        new, upd = (new, upd+1) if hit else (new+1, upd)

    (HERE/"ingest_batch.json").write_text(json.dumps(batch, indent=1))
    print(f"{len(batch)} records — {new} new, {upd} updated\n")
    for n in allnotes: print("  " + n)

if __name__ == "__main__":
    main()
