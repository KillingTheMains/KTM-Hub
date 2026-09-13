"""Build the four gear catalog documents for the KTM Hub store.

Catalogs are ONE document each holding an array, not one document per item.
The aggregation rule in the data model is "one document per thing a person
names, arrays inside for what belongs to it" — and a reference catalog is
always read whole, so 114 case types is one 14 KB document rather than 114
documents (2.3% of the 5,000 cap) that are never read individually.
"""
import json, pathlib, openpyxl

HERE = pathlib.Path(__file__).parent
raw = json.loads((HERE / "gear_raw.json").read_text())
out = HERE / "gear"; out.mkdir(exist_ok=True)

def write(doc_id, body):
    (out / f"{doc_id}.json").write_text(json.dumps(body, indent=1, ensure_ascii=False))
    return {"op": "set", "collection": "gear", "doc_id": doc_id,
            "file_path": str((out / f"{doc_id}.json").resolve())}

batch = []

# ── 1. Cases ────────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(
    "/mnt/user-data/uploads/Truck Packer/Case Weights and Dims (2).xlsx", data_only=True)
ws = wb.worksheets[0]
cases = []
for row in ws.iter_rows(min_row=2, values_only=True):
    name, lb, ctype, w, l, h = (row + (None,) * 6)[:6]
    if not name or lb is None:
        continue
    rec = {"name": str(name).strip(), "weightLb": lb, "caseType": ctype,
           "wIn": w, "lIn": l, "hIn": h}
    if all(isinstance(x, (int, float)) for x in (w, l, h)):
        rec["cubeFt"] = round(w * l * h / 1728, 2)
    cases.append(rec)
batch.append(write("cases", {
    "kind": "case",
    "name": "Christie Lites case catalog",
    "source": "Case Weights and Dims (2).xlsx — Truck Packer repo",
    "note": "Real weights and outside dimensions in inches. This is the data Truck "
            "Packer never read: it tracks neither weight nor cube, while this sheet "
            "sat unused in its own repo root. Truck Plot is built on it.",
    "items": cases,
}))

# ── 2. Truss products ───────────────────────────────────────────────────────
truss = [{
    "name": t.get("name"), "manufacturer": t.get("manufacturer"),
    "profile": t.get("profile"), "chord": t.get("chord"),
    "sections": t.get("sections"), "weightPerFt": t.get("weightPerFt"),
    "notes": t.get("notes"),
} for t in raw["truss"]]
batch.append(write("truss", {
    "kind": "truss",
    "name": "Truss products",
    "source": "TRUSS_LIBRARY — Pre-Pro Truss Builder",
    "note": "weightPerFt is real per-manufacturer data and was dead in Pre-Pro — "
            "defined once and never read anywhere. Truss Plot needs exactly this.",
    "items": truss,
}))

# ── 3. Rack equipment ───────────────────────────────────────────────────────
def ports_summary(ports):
    kinds = {}
    for p in ports or []:
        kinds[p.get("type", "?")] = kinds.get(p.get("type", "?"), 0) + 1
    return ", ".join(f"{n}x {k}" for k, n in sorted(kinds.items()))

rack = [{
    "id": e.get("id"), "name": e.get("name"), "manufacturer": e.get("manufacturer"),
    "model": e.get("model"), "ruHeight": e.get("ruHeight"), "hasIp": e.get("hasIp"),
    "portCount": len(e.get("ports") or []), "portSummary": ports_summary(e.get("ports")),
    "ports": [{"id": p.get("id"), "name": p.get("name"), "type": p.get("type")}
              for p in (e.get("ports") or [])],
} for e in raw["rackEq"]]
batch.append(write("rack-equipment", {
    "kind": "rack-equipment",
    "name": "Rack equipment",
    "source": "BUILTIN_TYPES — Pre-Pro Rack Builder",
    "note": "RU heights and full port maps. Note this roster differs from what "
            "Pre-Pro's own CLAUDE.md documents — the code is right, that doc is stale. "
            "Manufacturer PDFs for five of these are in Pre-Pro reference-docs/.",
    "items": rack,
}))

# ── 4. Pack items ───────────────────────────────────────────────────────────
pack = [{"name": p.get("name"), "cat": p.get("cat"),
         "wFt": p.get("w"), "hFt": p.get("h")} for p in raw["packItems"]]
batch.append(write("pack-items", {
    "kind": "pack-item",
    "name": "Trailer pack footprints",
    "source": "DEFAULT_LIBRARY — Truck Packer src/data/library.js",
    "note": "Deck footprints in feet on a 53 x 8.5 ft trailer, 2-inch snap grid. "
            "Used in production at SAP Sapphire 2026.",
    "items": pack,
}))

(HERE / "gear_batch.json").write_text(json.dumps(batch, indent=1))
for b, label in zip(batch, ("cases", "truss", "rack-equipment", "pack-items")):
    body = json.loads(pathlib.Path(b["file_path"]).read_text())
    print(f"{label:16} {len(body['items']):4} items   "
          f"{len(json.dumps(body)) / 1024:6.1f} KB of the 256 KB doc cap")
