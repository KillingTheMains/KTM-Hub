"""Merge parsed GDTF data into the KTM Hub fixture library.

Same three rules as gdtf_ingest.py, which stays the offline/folder path:

  1. GDTF wins on DMX modes, and on nothing else.
  2. Weight is COMPARED, never replaced. Disagreement is recorded as a
     conflict against the held figure. The ACME SANA is why: a file the
     Share flags as manufacturer-uploaded asserts 5.58 kg for a fixture
     ACME publishes at 26 kg.
  3. Power is never taken from GDTF. Zero of 29 files carry it.

Two differences from gdtf_ingest, both deliberate:

  - Emits `update`, not `set`. An update cannot drop a field that is not in
    the payload, so a mistake here cannot silently delete researched power
    data. Every nested object (dmx, weight, gdtf) is still rebuilt WHOLE
    from the existing record, because an update replaces a nested map
    rather than merging into it.
  - `dmx.default` is remapped BY MODE NAME, not left to fall to the
    smallest footprint. The library's MAC Aura PXL default is 89, which is
    its "Extended"; the official file says Extended is 35. Following the
    name moves the default to 35. If the old default matches no named mode,
    it is left alone and reported — guessing which mode the patch is built
    around is not a call to make silently.
"""
import json, pathlib, re

HERE = pathlib.Path(__file__).parent
LIB  = HERE.parent / "fixtures" / "fixtures"
OUT  = HERE / "out"; OUT.mkdir(exist_ok=True)
DATE = "2026-09-10"

gdtf  = {g["file"]: g for g in json.loads((HERE/"gdtf_parsed.json").read_text())}
rids  = json.loads((HERE/"rids.json").read_text())
files = json.loads((HERE/"files.json").read_text())

norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())

def close(a, b, tol=0.06):
    try: return abs(float(a)-float(b)) <= max(abs(float(b))*tol, 0.5)
    except (TypeError, ValueError): return False

batch, report, flags = [], [], []
for fid, fname in files.items():
    if not fname:
        report.append((fid, "no usable file — Share entry rejected")); continue
    g   = gdtf[fname]
    rec = json.loads((LIB/f"{fid}.json").read_text())
    meta, upd = rids.get(fid, {}), {}
    src = {"sourceLabel": f"GDTF {fname}", "sourceUrl": "https://gdtf-share.com/",
           "retrieved": DATE, "status": "verified" if g.get("official") else "interpreted"}
    line = []

    # 1 ── modes -------------------------------------------------------
    # "GDTF wins on modes" holds for a file the manufacturer stands behind.
    # It does NOT hold for a community upload that knows FEWER modes than the
    # library already does: the SGM Q-7 file is a BETA user upload carrying 2
    # modes against the library's researched 5, and applying it would delete
    # three real modes and orphan the patch default. Trust is `uploader ==
    # "Manuf."` or a self-declared official file — the in-file claim alone is
    # too narrow, since only Martin and ETC write it.
    trusted = bool(g.get("official")) or meta.get("uploader") == "Manuf."
    modes = sorted([list(m) for m in g.get("modes") or []], key=lambda x: x[1])
    if modes and not trusted and len(modes) < len(rec.get("dmx", {}).get("footprints") or []):
        flags.append(f"{fid}: mode set NOT applied — community file has {len(modes)} modes "
                     f"against the library's {len(rec['dmx']['footprints'])}; recorded, not merged")
        dmx = dict(rec.get("dmx") or {})
        dmx["gdtfModes"] = {"footprints": modes, **src,
                            "note": "fewer modes than the library holds; kept for comparison only"}
        upd["dmx"] = dmx
        modes = []
    if modes:
        old_dmx = dict(rec.get("dmx") or {})
        old_fps = [list(x) for x in (old_dmx.get("footprints") or [])]
        dmx = dict(old_dmx)
        dmx["footprints"] = modes
        dmx["modeSource"] = src
        old_def = old_dmx.get("default")
        if old_def is not None and old_def not in [m[1] for m in modes]:
            was = next((n for n, f in old_fps if f == old_def), None)
            new = next((f for n, f in modes if was and norm(n) == norm(was)), None)
            if new is None and was:
                new = next((f for n, f in modes if was and
                            (norm(was) in norm(n) or norm(n) in norm(was))), None)
            if new is not None:
                dmx["default"] = new
                line.append(f"default {old_def}→{new} (followed mode name '{was}')")
            else:
                flags.append(f"{fid}: default {old_def} matches no mode in the new set "
                             f"— LEFT AS IS, needs a decision")
        if old_fps != modes:
            line.append(f"modes {len(old_fps)}→{len(modes)}")
        upd["dmx"] = dmx

    # 2 ── weight: compare, never replace ------------------------------
    lb, w = g.get("weightLb"), dict(rec.get("weight") or {})
    if lb:
        cur = w.get("value")
        if cur in (None, 0):
            upd["weight"] = {**w, "value": round(lb,1), "unit": "lb", **src,
                             "sourceLabel": src["sourceLabel"] + " (Weight attribute)"}
            line.append(f"weight filled {round(lb,1)} lb")
        elif not close(lb, cur):
            w["status"] = "conflicting"
            w["conflicting"] = list(w.get("conflicting") or [])
            if not any(close(c.get("value"), lb) for c in w["conflicting"]):
                w["conflicting"].append({"value": round(lb,1), "unit": "lb",
                    "sourceLabel": src["sourceLabel"], "retrieved": DATE,
                    "note": "GDTF Weight attribute disagrees with the held figure"})
            upd["weight"] = w
            flags.append(f"{fid}: WEIGHT — library {cur} lb vs GDTF {round(lb,1)} lb, "
                         f"library figure kept")

    # 3 ── additive only ----------------------------------------------
    if g.get("dimensions") and not rec.get("dimensions"):
        upd["dimensions"] = {**g["dimensions"], "source": src["sourceLabel"], "retrieved": DATE}
    upd["gdtf"] = {**(rec.get("gdtf") or {}),
        "file": fname, "rid": meta.get("rid"), "uploader": meta.get("uploader"),
        "shareRevision": meta.get("revision"), "fixtureTypeID": g.get("fixtureTypeID"),
        "dataVersion": g.get("dataVersion"), "official": bool(g.get("official")),
        "latestRevision": g.get("revisions"), "retrieved": DATE}
    al = list(rec.get("aliases") or [])
    for alt in filter(None, [g.get("longName"), g.get("shortName"), g.get("name")]):
        if alt != rec.get("name") and alt not in al: al.append(alt)
    if al != (rec.get("aliases") or []): upd["aliases"] = al
    upd["updatedAt"] = DATE + "T00:00:00.000Z"

    (OUT/f"{fid}.json").write_text(json.dumps(upd, indent=1, ensure_ascii=False))
    batch.append({"op": "update", "collection": "fixtures", "doc_id": fid,
                  "file_path": str((OUT/f"{fid}.json").resolve()),
                  "if_version": 3 if fid == "martin-mac-ultra-performance" else 2})
    report.append((fid, "; ".join(line) or "identity + provenance only"))

(HERE/"batch.json").write_text(json.dumps(batch, indent=1))
print(f"{len(batch)} update payloads\n")
for fid, what in report: print(f"  {fid:34} {what}")
print("\nNEEDS A DECISION:" if flags else "\nno flags")
for f in flags: print("  " + f)
