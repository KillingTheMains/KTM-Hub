"""Read GDTF files into KTM Hub fixture records.

WHAT A GDTF FILE IS
    A .gdtf is a ZIP archive. Everything structured lives in `description.xml`
    at the root; the rest is 3D models, gobo images, SVGs and a thumbnail —
    typically 95%+ of the file size and irrelevant to us. A 6 MB GDTF is 6 MB
    of geometry wrapped around ~400 KB of XML.

WHAT IT IS AUTHORITATIVE FOR
    DMX modes and their footprints. That is the format's whole purpose, it is
    what consoles actually load, and it is better than any spec sheet — spec
    sheets summarise modes in prose and get them wrong or omit them.

WHAT IT IS NOT
    A power reference. The GDTF spec has places for power consumption and for
    connectors, but manufacturers frequently leave them empty. Never treat an
    absent value as zero, and never treat GDTF as a source for fixture draw
    unless the element is actually populated.

PROVENANCE
    Two signals decide whether a file counts as a manufacturer source:
      - FixtureType@Description often literally says "Official <brand> File".
      - <Revisions> records who uploaded it, when, and why.
    A manufacturer-published file is a primary source. A community file is not,
    and is recorded as `interpreted`.

FOOTPRINT MATH
    A mode's footprint is the highest DMX offset any of its channels occupies,
    NOT the number of <DMXChannel> nodes. A 16-bit channel occupies two offsets
    ("12,13"), so counting nodes undercounts. MAC Ultra Basic has 37 channel
    nodes and a 48-channel footprint.
"""
import zipfile, xml.etree.ElementTree as ET, pathlib, json, re, sys

KG_TO_LB = 2.20462262

def parse(path):
    p = pathlib.Path(path)
    z = zipfile.ZipFile(p)
    name = next((n for n in z.namelist() if n.lower().endswith("description.xml")), None)
    if not name:
        raise ValueError(f"{p.name}: no description.xml — not a valid GDTF")
    root = ET.fromstring(z.read(name))
    ft = root.find("FixtureType")
    if ft is None:
        raise ValueError(f"{p.name}: no <FixtureType>")

    out = {
        "file": p.name,
        "dataVersion": root.get("DataVersion"),
        "name": ft.get("Name"), "longName": ft.get("LongName"),
        "shortName": ft.get("ShortName"), "manufacturer": ft.get("Manufacturer"),
        "description": ft.get("Description"), "fixtureTypeID": ft.get("FixtureTypeID"),
    }

    # ── provenance ────────────────────────────────────────────────────────
    revs = [{"date": r.get("Date"), "text": r.get("Text"), "user": r.get("UserID")}
            for r in (ft.find("Revisions") or [])]
    out["revisions"] = revs
    desc = (out["description"] or "")
    official = bool(re.search(r"\bofficial\b", desc, re.I))
    out["official"] = official
    out["provenanceStatus"] = "verified" if official else "interpreted"

    # ── DMX modes — the authoritative part ────────────────────────────────
    modes = []
    for m in (ft.find("DMXModes") or []):
        offsets, breaks = [], set()
        for c in m.iter("DMXChannel"):
            o = c.get("Offset")
            if o and o.lower() != "none":
                offsets += [int(v) for v in o.split(",") if v.strip().isdigit()]
            b = c.get("DMXBreak")
            if b and b.isdigit(): breaks.add(int(b))
        modes.append({
            "name": m.get("Name"),
            "footprint": max(offsets) if offsets else 0,   # highest offset, not node count
            "channelNodes": len(list(m.iter("DMXChannel"))),
            "breaks": sorted(breaks) or [1],
        })
    modes.sort(key=lambda x: x["footprint"])
    out["modes"] = modes

    pd = ft.find("PhysicalDescriptions")

    # ── weight ────────────────────────────────────────────────────────────
    out["weightKg"] = out["weightLb"] = None
    props = pd.find("Properties") if pd is not None else None
    if props is not None:
        w = props.find("Weight")
        if w is not None and w.get("Value"):
            kg = float(w.get("Value"))
            if kg > 0:
                out["weightKg"] = round(kg, 2)
                out["weightLb"] = round(kg * KG_TO_LB, 1)
        ot = props.find("OperatingTemperature")
        if ot is not None:
            out["operatingTempC"] = [ot.get("Low"), ot.get("High")]
        lh = props.find("LegHeight")
        if lh is not None and lh.get("Value"):
            out["legHeightM"] = float(lh.get("Value"))

    # ── power: present in the spec, usually absent in the file ────────────
    out["power"] = None
    if props is not None:
        pc = props.find("PowerConsumption")
        if pc is not None:
            out["power"] = {k: pc.get(k) for k in pc.keys()}

    # ── connectors: also frequently empty ─────────────────────────────────
    conns = []
    if pd is not None:
        cn = pd.find("Connectors")
        if cn is not None:
            for c in cn:
                conns.append({"name": c.get("Name"), "type": c.get("Type"),
                              "dmxBreak": c.get("DMXBreak")})
    out["connectors"] = conns

    # ── physical envelope from the top-level model ────────────────────────
    dims = None
    for mdl in (ft.find("Models") or []):
        try:
            L, W, H = (float(mdl.get(k) or 0) for k in ("Length", "Width", "Height"))
        except (TypeError, ValueError):
            continue
        if max(L, W, H) > 0:
            vol = L * W * H
            if dims is None or vol > dims["_vol"]:
                dims = {"_vol": vol, "model": mdl.get("Name"),
                        "lengthM": round(L, 3), "widthM": round(W, 3), "heightM": round(H, 3)}
    if dims: dims.pop("_vol")
    out["dimensions"] = dims

    # ── what the file did NOT give us ─────────────────────────────────────
    out["gaps"] = [k for k, present in (
        ("power draw",  bool(out["power"])),
        ("connectors",  bool(conns)),
        ("weight",      out["weightKg"] is not None),
        ("dimensions",  dims is not None),
        ("dmx modes",   bool(modes)),
    ) if not present]

    out["archive"] = {"entries": len(z.namelist()),
                      "bytes": p.stat().st_size,
                      "xmlBytes": z.getinfo(name).file_size}
    return out


if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                       else "/mnt/user-data/uploads/RigPlot/gdtf")
    files = sorted(src.glob("*.gdtf")) if src.is_dir() else [src]
    results = []
    for f in files:
        try:
            results.append(parse(f))
        except Exception as e:
            print(f"  !! {f.name}: {e}")
    pathlib.Path("gdtf_parsed.json").write_text(json.dumps(results, indent=1))

    print(f"{'fixture':<34} {'modes':<5} {'footprints':<26} {'lb':>6}  {'off':<4} gaps")
    print("-" * 108)
    for r in results:
        fps = ", ".join(f"{m['name'][:11]}:{m['footprint']}" for m in r["modes"][:3])
        if len(r["modes"]) > 3: fps += f" +{len(r['modes'])-3}"
        print(f"{(r['manufacturer'] or '')[:14]+' '+(r['name'] or '')[:19]:<34} "
              f"{len(r['modes']):<5} {fps[:26]:<26} {r['weightLb'] or '—':>6}  "
              f"{'yes' if r['official'] else 'no':<4} {', '.join(r['gaps']) or '—'}")
