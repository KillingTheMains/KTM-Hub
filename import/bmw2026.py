#!/usr/bin/env python3
"""
Convert the legacy Pre-Pro BMW ABBS 2026 data into a single ktm-show JSON bundle.

Sources (read-only):
  - Pre-Pro Paperwork/BMW ABBS 2026.json         (loom list: locations + cables)
  - Pre-Pro-Paperwork/rack-builder/index.html    (bmw2026Project(): racks + snakes)
  - Pre-Pro-Paperwork/truss-builder/index.html   (bmw2026Trusses(): truss inventory)

Output:
  - KTM-Hub/data/shows/bmw-abbs-2026.ktm-show.json

Never eval()s a whole source file. The two Pre-Pro HTML sources are hand-written
app code; this script brace-balances out just the named function/array literal
it needs and evaluates *that* in a throwaway `node` process with tiny local
stubs for the helpers those literals call (uid(), makePL(), etc). Nothing else
in either HTML file is executed or read.

Standard library only, save for the one `node -e` subprocess call.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HUB = Path("/Users/jasonbielsker/Developer/KTM-Hub")
PP = Path(
    "/Users/jasonbielsker/Library/CloudStorage/GoogleDrive-jason@killingthemains.com"
    "/My Drive/Cowork Playground/Pre-Pro Paperwork"
)
PP_REPO = Path("/Users/jasonbielsker/Developer/Pre-Pro-Paperwork")
CATALOG_DIR = Path(__file__).parent.parent / "data" / "catalog"

LOOM_LIST_JSON = PP / "BMW ABBS 2026.json"
RACK_BUILDER_HTML = PP_REPO / "rack-builder" / "index.html"
TRUSS_BUILDER_HTML = PP_REPO / "truss-builder" / "index.html"

OUT_DIR = HUB / "data" / "shows"
OUT_FILE = OUT_DIR / "bmw-abbs-2026.ktm-show.json"

NODE = "/usr/local/bin/node"

ID_RE = re.compile(r"^[A-Za-z0-9_\-.~:@+]{1,200}$")
MAX_DOC_BYTES = 200 * 1024

errors = []  # unmapped-value list; script exits non-zero if non-empty


# ── brace-balance extraction (never eval the whole file) ───────────────────

def _balanced_from(src, start_idx, open_ch, close_ch):
    """start_idx must point at open_ch. Returns text[start_idx:end+1]."""
    depth = 0
    in_str = None
    esc = False
    for p in range(start_idx, len(src)):
        c = src[p]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if in_str:
            if c == in_str:
                in_str = None
            continue
        if c in ("'", '"', "`"):
            in_str = c
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return src[start_idx:p + 1]
    raise ValueError(f"unbalanced {open_ch}{close_ch} literal starting at {start_idx}")


def extract_array(src, name):
    i = src.index(name)
    open_i = src.index("[", i)
    return _balanced_from(src, open_i, "[", "]")


def extract_function(src, funcname):
    """Return the full `function funcname(...) { ... }` text, brace-balanced."""
    marker = f"function {funcname}("
    i = src.index(marker)
    open_i = src.index("{", i)
    body = _balanced_from(src, open_i, "{", "}")
    header = src[i:open_i]
    return header + body


# ── node eval helpers ───────────────────────────────────────────────────────

def run_node(js_src):
    r = subprocess.run([NODE, "-e", js_src], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"node eval failed:\n{r.stderr}")
    return json.loads(r.stdout)


def load_rack_builder_project():
    src = RACK_BUILDER_HTML.read_text()
    builtin_types = extract_array(src, "const BUILTIN_TYPES = [")
    make_pl = extract_function(src, "makePL")
    new_item = extract_function(src, "newItem")
    new_line = extract_function(src, "newLine")
    get_type = extract_function(src, "getType")
    bmw_project = extract_function(src, "bmw2026Project")
    js = f"""
function uid() {{ return 'x'; }}
const BUILTIN_TYPES = {builtin_types};
{make_pl}
{new_item}
{new_line}
const S = {{ project: {{ customTypes: [] }} }};
{get_type}
function _ppsGetShowName() {{ return ''; }}
{bmw_project}
console.log(JSON.stringify(bmw2026Project()));
"""
    return run_node(js)


def load_truss_builder_seed():
    src = TRUSS_BUILDER_HTML.read_text()
    make_truss = extract_function(src, "makeTruss")
    bmw_trusses = extract_function(src, "bmw2026Trusses")
    js = f"""
function uid() {{ return 'x'; }}
{make_truss}
{bmw_trusses}
console.log(JSON.stringify(bmw2026Trusses()));
"""
    return run_node(js)


# ── catalogs ─────────────────────────────────────────────────────────────

def load_catalog(name):
    return json.loads((CATALOG_DIR / "gear" / name).read_text())


def load_tokens():
    return json.loads((CATALOG_DIR / "meta" / "tokens.json").read_text())


def slug(s):
    s = re.sub(r"[^A-Za-z0-9]+", "-", str(s)).strip("-").lower()
    return s or "x"


# Nearest-name mapping of the Hub's 12 colour tokens onto Rack Plot's 9 CSS
# swatch vars (--s1..--s8, --s0). Rack Plot only has 9 slots; several tokens
# share the closest-hue slot. Recorded here per spec instruction.
TOKEN_TO_CSSVAR = {
    "BLUE": "--s1",
    "ORANGE": "--s2",
    "GREEN": "--s3",
    "BROWN": "--s4",
    "PURPLE": "--s5",
    "LIME": "--s6",
    "YELLOW": "--s6",   # nearest hue to olive/yellow-green s6; no dedicated slot
    "PINK": "--s7",
    "RED": "--s7",      # nearest hue to s7 (pink/red); no dedicated slot
    "TEAL": "--s8",
    "CYAN": "--s8",     # nearest hue to s8 (teal-blue); no dedicated slot
    "GREY": "--s0",
    "WHITE": "--s0",    # no dedicated slot; nearest neutral
    "BLACK": "--s0",    # no dedicated slot; nearest neutral
}

# Pre-Pro loom cable "type" free-text -> Hub cable catalog id. Only entries
# actually observed in the BMW loom list are exercised; anything else fails
# loudly (Must verify).
CABLE_TYPE_MAP = {
    "SOCAPEX": "socapex",
    "CPC4": "cpc4",
    "CPC8": "cpc8",
    "DMX": "dmx-5pin",
    "2X DMX": "dmx-5pin",
    "DMX 2X": "dmx-5pin",
    "FIBER": "fiber",
    "ETHERCON": "ethercon",
    "CAT5": "ethercon",
    "CAT6": "ethercon",
    "QM-8": "socapex",
    "POWER": "true1-jumper",
    "OTHER": "dmx-5pin",
}

TRUSS_TYPE_MAP = {
    "TYLER GT TRUSS": "TYLER GT TRUSS",
    "GLOBAL GT": "TYLER GT TRUSS",
    "GT": "TYLER GT TRUSS",
}

BREAKOUT_ENUM = {"CPC4", "CPC8", "SOCA", ""}


def normalize_breakout(v):
    u = (v or "").strip().upper()
    return u if u in BREAKOUT_ENUM else "OTHER"


UNIV_RE = re.compile(r"UNIV\s*(\d+)", re.IGNORECASE)


def pad6(arr):
    arr = list(arr or [])
    return (arr + [""] * 6)[:6]


def main():
    # ── load sources ────────────────────────────────────────────────────
    loom_data = json.loads(LOOM_LIST_JSON.read_text())
    rack_project = load_rack_builder_project()
    truss_seed = load_truss_builder_seed()

    rack_equip = {i["id"]: i for i in load_catalog("rack-equipment.json")["items"]}
    truss_cat_names = {i["name"] for i in load_catalog("truss.json")["items"]}
    cable_cat_ids = {i["id"] for i in load_catalog("cable.json")["items"]}
    tokens = load_tokens()
    hex_to_token = {v.upper(): k for k, v in tokens["colors"].items()}
    token_set = set(tokens["colors"].keys())

    # ── show doc ────────────────────────────────────────────────────────
    show_src = loom_data["show"]
    show_doc = {
        "id": "bmw-abbs-2026",
        "name": "BMW ABBS 2026",
        "client": show_src.get("client", ""),
        "venue": show_src.get("venue", ""),
        "date": show_src.get("date", ""),
        "notes": show_src.get("notes", ""),
    }

    # ── looms: sheets from Pre-Pro locations, cables from Pre-Pro cables ──
    sheets = {}
    for loc in loom_data["locations"]:
        sid = f"sheet_{loc['id']}"
        sheets[sid] = {"id": sid, "name": loc["name"], "cables": []}
        if loc.get("color") and loc["color"] not in token_set:
            errors.append(f"loom location color token not in catalog: {loc['color']}")

    loc_to_sheet = {loc["id"]: f"sheet_{loc['id']}" for loc in loom_data["locations"]}
    cable_labels_seen = set()

    for c in loom_data["cables"]:
        pp_type = (c.get("type") or "").strip().upper()
        if pp_type not in CABLE_TYPE_MAP:
            errors.append(f"unmapped cable type: {pp_type!r} (cable {c['id']})")
            continue
        cat_id = CABLE_TYPE_MAP[pp_type]
        if cat_id not in cable_cat_ids:
            errors.append(f"mapped cable type id not in catalog: {cat_id!r}")
            continue
        for col in ("color", "secColor"):
            v = c.get(col)
            if v and v not in token_set:
                errors.append(f"cable {col} token not in catalog: {v!r} (cable {c['id']})")
        cable_doc = {
            "id": f"cable_{c['id']}",
            "label": c.get("label", ""),
            "type": cat_id,
            "breakout": normalize_breakout(c.get("breakout")),
            "color": c.get("color", ""),
            "secColor": c.get("secColor", ""),
            "parts": pad6(c.get("parts")),
            "partPositions": pad6([]),
            "loomId": c.get("loomId", ""),
            "notes": c.get("notes", ""),
        }
        sheets[loc_to_sheet[c["locationId"]]]["cables"].append(cable_doc)
        cable_labels_seen.add(c.get("label", ""))

    # 13 rack-builder snakes with no matching loom cable -> add a cable on a
    # sheet named after the snake's location (all 13 have no location here,
    # so they all land on "SNAKES").
    snakes = rack_project.get("snakes", [])
    snakes_sheet_id = None
    for sn in snakes:
        if sn["name"] in cable_labels_seen:
            continue
        loc_name = sn.get("location") or "SNAKES"
        sid = f"sheet_{slug(loc_name)}"
        if sid not in sheets:
            sheets[sid] = {"id": sid, "name": loc_name, "cables": []}
        snake_type = (sn.get("type") or "").strip().upper()  # 'cpc4'/'cpc8' -> 'CPC4'/'CPC8'
        cat_id = CABLE_TYPE_MAP.get(snake_type)
        if cat_id is None or cat_id not in cable_cat_ids:
            errors.append(f"unmapped snake type: {snake_type!r} (snake {sn['name']})")
            continue
        hex_up = (sn.get("color") or "").upper()
        token = hex_to_token.get(hex_up)
        if token is None:
            errors.append(f"snake color hex has no token match: {sn.get('color')!r} (snake {sn['name']})")
            token = ""

        lines_out = [
            {
                "n": ln["lineNum"],
                "position": ln.get("position") or "",
                "universe": ln.get("universe") or "",
                "firstFixture": ln.get("firstFixture") or "",
            }
            for ln in sn.get("lines", [])
        ]
        # Loom Plot only has 6 physical part-position columns; lines 7/8 of a
        # CPC8 snake live only in `lines`, not in partPositions.
        part_positions = pad6([ln["position"] for ln in lines_out[:6]])

        sheets[sid]["cables"].append({
            "id": f"cable_snake_{slug(sn['name'])}",
            "label": sn["name"],
            "type": cat_id,
            "breakout": normalize_breakout(snake_type),
            "color": token,
            "secColor": "",
            "parts": pad6([]),
            "partPositions": part_positions,
            "loomId": "",
            "notes": "added: rack-builder snake with no matching loom cable",
            "lines": lines_out,
        })

    looms_out = list(sheets.values())

    # ── racks ───────────────────────────────────────────────────────────
    racks_out = []
    ports_with_universe = 0
    links_resolved = 0
    links_unresolved = 0
    total_items = 0

    for rack in rack_project.get("racks", []):
        rack_hex = (rack.get("color") or "").upper()
        rack_token = hex_to_token.get(rack_hex)
        if rack_token is None:
            errors.append(f"rack color hex has no token match: {rack.get('color')!r} (rack {rack['name']})")
            rack_token = "GREY"
        rack_cssvar = TOKEN_TO_CSSVAR.get(rack_token, "--s0")

        rack_id = f"rack_{slug(rack['name'])}"
        items_out = []
        ru_cursor = 1  # RU 1 is bottom; place Pre-Pro's listed order bottom-up

        for idx, item in enumerate(rack.get("equipment", [])):
            type_id = item.get("typeId")
            gear = rack_equip.get(type_id)
            if gear is None:
                errors.append(f"unmapped gearId: {type_id!r} (rack {rack['name']}, item {item.get('label')})")
                continue
            total_items += 1
            ru_height = gear.get("ruHeight", 1)

            ports_out = {}
            for pid, pl in (item.get("portLabels") or {}).items():
                label = (pl.get("label") or "").strip()
                if not label:
                    continue
                if not any(p["id"] == pid for p in gear.get("ports", [])):
                    errors.append(
                        f"unmapped port id: {pid!r} on gear {type_id!r} (rack {rack['name']}, item {item.get('label')})"
                    )
                    continue
                entry = {"label": label}
                m = UNIV_RE.search(label)
                if m:
                    entry["universe"] = m.group(1)
                    ports_with_universe += 1
                # rack<->rack / loom-break-in links: the Pre-Pro source data
                # never populates connRackId/snakeId on any item (verified
                # against the live rack-builder source), so there is nothing
                # to resolve here. Kept as a no-op branch for completeness.
                conn_rack = pl.get("connRackId")
                snake_id = pl.get("snakeId")
                if conn_rack or snake_id:
                    links_unresolved += 1  # would need real target data to resolve
                ports_out[pid] = entry

            items_out.append({
                "key": f"i-{idx:02d}",
                "gearId": type_id,
                "ru": ru_cursor,
                "col": 0,  # simplification: single-column bottom-up stack; see report
                "face": "front",
                "label": item.get("label") or None,
                "color": rack_cssvar,
                "ip": item.get("ip") or None,
                "ports": ports_out,
            })
            ru_cursor += ru_height

        racks_out.append({
            "id": rack_id,
            "name": rack["name"],
            "ru": ru_cursor - 1,
            "color": rack_cssvar,
            "items": items_out,
        })

    # ── truss ───────────────────────────────────────────────────────────
    truss_out = []
    for i, t in enumerate(truss_seed):
        type_name = TRUSS_TYPE_MAP.get(t["type"])
        if type_name is None or type_name not in truss_cat_names:
            errors.append(f"unmapped truss typeName: {t['type']!r} (truss {t['name']})")
            continue
        hex_up = (t.get("color") or "").upper()
        token = hex_to_token.get(hex_up)
        if token is None:
            errors.append(f"truss color hex has no token match: {t.get('color')!r} (truss {t['name']})")
            token = ""
        truss_out.append({
            "id": f"truss_{slug(t['name'])}",
            "name": t["name"],
            "typeName": type_name,
            "lengthFt": t.get("lengthFt", 0),
            "pieces": {
                "10": t["pieces"].get("ten", 0),
                "8": t["pieces"].get("eight", 0),
                "5": t["pieces"].get("five", 0),
                "2": t["pieces"].get("two", 0),
            },
            "colors": [token] if token else [],
            "endType": t.get("endType", ""),
            "customEnds": t.get("customEnds", []) or [],
            "notes": t.get("notes", ""),
            "sort": i,
        })

    # ── bail out on any unmapped value before writing anything ──────────
    if errors:
        print("UNMAPPED VALUES — aborting, nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    # ── envelope ─────────────────────────────────────────────────────────
    bundle = {
        "_format": "ktm-show",
        "_version": 1,
        "exported": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "show": show_doc,
        "fixtures": [],
        "gear": [],
        "collections": {
            "racks": racks_out,
            "looms": looms_out,
            "truss": truss_out,
        },
    }

    # ── validate: ids legal, doc size <=200KB ────────────────────────────
    def check_id(doc_id, where):
        if not ID_RE.match(str(doc_id)):
            errors.append(f"illegal doc id {doc_id!r} ({where})")

    check_id(show_doc["id"], "show")
    for r in racks_out:
        check_id(r["id"], "rack")
        for it in r["items"]:
            check_id(it["key"], f"rack {r['id']} item")
        size = len(json.dumps(r).encode())
        if size > MAX_DOC_BYTES:
            errors.append(f"rack doc too large: {r['id']} ({size} bytes)")
    for sh in looms_out:
        check_id(sh["id"], "loom sheet")
        for c in sh["cables"]:
            check_id(c["id"], f"loom sheet {sh['id']} cable")
        size = len(json.dumps(sh).encode())
        if size > MAX_DOC_BYTES:
            errors.append(f"loom sheet doc too large: {sh['id']} ({size} bytes)")
    for t in truss_out:
        check_id(t["id"], "truss")
        size = len(json.dumps(t).encode())
        if size > MAX_DOC_BYTES:
            errors.append(f"truss doc too large: {t['id']} ({size} bytes)")

    if errors:
        print("VALIDATION FAILED — aborting, nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_bytes = json.dumps(bundle, indent=2, sort_keys=False).encode()
    OUT_FILE.write_bytes(out_bytes)

    total_cables = sum(len(sh["cables"]) for sh in looms_out)
    print(f"racks: {len(racks_out)}")
    print(f"items: {total_items}")
    print(f"ports with universes: {ports_with_universe}")
    print(f"links resolved: {links_resolved}")
    print(f"links unresolved: {links_unresolved}")
    print(f"sheets: {len(looms_out)}")
    print(f"cables: {total_cables}")
    print(f"trusses: {len(truss_out)}")
    print(f"output file: {OUT_FILE} ({len(out_bytes)} bytes)")


if __name__ == "__main__":
    main()
