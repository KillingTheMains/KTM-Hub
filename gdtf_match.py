"""Match the KTM Hub fixture library against the GDTF Share catalogue.

    python3 gdtf_match.py              # report matches, download nothing
    python3 gdtf_match.py --download   # pull the chosen file for each match

Ranking is deliberate, not clever: a manufacturer upload beats a user upload
every time, because the one thing the local files proved is that community
GDTFs carry wrong numbers (ACME SANA: 5.58 kg asserted against a 26 kg
fixture). Within a tier, newest revision wins.

Nothing here writes to the library. It reports, and optionally downloads.
Merging stays gdtf_ingest.py's job.
"""
import json, pathlib, re, sys, argparse
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gdtf_share as S

# id, manufacturer, name, aliases, already-has-a-local-gdtf
LIB = [
 ("acme-sana-profile","ACME","SANA Profile",["ACME SANA PROFILE (XA 300 BSWF IP)","XA 300 BSWF IP"],True),
 ("ayrton-diablo-s","Ayrton","Diablo",[],False),        # -S dropped: Jason, use the base file for now,
 ("ayrton-khamsin-s","Ayrton","Khamsin",[],False),      # -S dropped, same call,
 ("ayrton-rivale-profile","Ayrton","Rivale Profile",["Rivale"],True),
 ("ayrton-zonda-9-fx","Ayrton","Zonda 9 FX",["ZX9"],True),
 ("chauvet-maverick-force-s-profile","Chauvet","Maverick Force S Profile",[],False),
 ("chauvet-rogue-r2-wash","Chauvet","Rogue R2 Wash",[],False),
 ("claypaky-mythos-2","Claypaky","Mythos 2",[],False),
 ("claypaky-scenius-unico","Claypaky","Scenius Unico",[],False),
 ("claypaky-sharpy","Claypaky","Sharpy",[],False),
 ("cm-lodestar-1-ton-hoist","CM","Lodestar 1-ton hoist",[],False),
 ("elation-proteus-maximus","Elation","Proteus Maximus",[],False),
 ("etc-colorsource-par","ETC","ColorSource PAR",[],False),
 ("etc-source-four-750-w","ETC","Source Four 750 W",["Source Four"],False),
 ("etc-source-four-led-s3-lustr","ETC","S4 Series 3 Lustr X8 36Deg",[],False),  # barrel is a field
                                                       # variable, not a fixture: 36Deg stands in. Proven identical to
                                                       # 26Deg on modes, footprints, weight and dimensions — only name,
                                                       # description and fixtureTypeID differ. The ID being per-barrel is
                                                       # the catch for a Vectorworks export: send the barrel actually hung.,
 ("glp-impression-x4-bar-20","GLP","impression X4 Bar 20",["X4 Bar 20"],False),
 ("glp-jdc1","GLP","JDC1",[],False),
 ("look-viper-nt-fogger","Look","Viper NT",["Viper NT fogger"],False),
 ("ma-lighting-grandma3-full-size","MA Lighting","grandMA3 full-size",[],False),
 ("martin-jem-zr45-fogger","Martin","JEM ZR45",["ZR45"],False),
 ("martin-mac-aura-pxl","Martin","MAC Aura PXL",[],False),
 ("martin-mac-aura-xb","Martin","MAC Aura XB",[],False),
 ("martin-mac-encore-performance","Martin","MAC Encore Performance CLD",[],False),  # CLD for now, not WRM,
 ("martin-mac-ultra-performance","Martin","MAC Ultra Performance",[],True),
 ("martin-mac-viper-profile","Martin","MAC Viper Profile",[],False),
 ("martin-rush-par-2-rgbw-zoom","Martin","RUSH PAR 2 RGBW Zoom",["RUSH PAR 2 RGBW"],True),
 ("mdg-theone-hazer","MDG","theONE",["theONE hazer"],False),
 ("robe-bmfl-blade","Robe","BMFL Blade",[],False),
 ("robe-megapointe","Robe","MegaPointe",[],False),
 ("robe-pointe","Robe","Pointe",[],False),
 ("robe-robin-esprite","Robe","Robin Esprite",["Esprite"],True),
 ("robe-robin-ispiider","Robe","Robin iSpiider",["iSpiider"],True),
 ("robe-spiider","Robe","Spiider",[],False),
 ("robe-t1-profile","Robe","T1 Profile",[],False),
 ("sgm-q-7","SGM","Q-7",["Q7"],False),
]

# Our short manufacturer name -> how the Share spells it. Substring match.
MFR = {
 "Martin":"martinprofessional", "Robe":"robelighting", "Chauvet":"chauvet",
 "Claypaky":"claypaky", "ETC":"etc", "GLP":"glp", "Look":"look",
 "MDG":"mdg", "SGM":"sgm", "Ayrton":"ayrton", "ACME":"acme",
 "Elation":"elation", "MA Lighting":"malighting", "CM":"cm",
}

# Deliberately not matched. Reported as decided, not as a gap to chase again.
SKIP = {
 "claypaky-mythos-2":   "dropped — the Share only has Mythos, a different fixture",
 "look-viper-nt-fogger":"dropped — the Share only has Viper, community, wrong model",
 "cm-lodestar-1-ton-hoist":       "not a DMX fixture, nothing in the catalogue",
 "ma-lighting-grandma3-full-size":"a console, nothing in the catalogue",
 "etc-source-four-750-w":         "a conventional, nothing in the catalogue",
}

norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())

# Series prefixes the Share puts in front of a model name that the shop floor
# does not. Stripped before comparing, so "Pointe" matches "Robin Pointe".
# Stripping is the ONLY liberty taken: a trailing token is never removed,
# because that is where the model actually differs (Pointe / GigaPointe,
# T1 Profile / T1 Profile FS, Encore Performance / Encore Performance CLD).
PREFIX = {"robelighting": ["robin"], "martinprofessional": ["martin"],
          "chauvet": ["chauvetprofessional"]}

def strip_prefix(rf, want_m):
    for pre in PREFIX.get(want_m, []):
        if rf.startswith(pre) and len(rf) > len(pre):
            return rf[len(pre):]
    return rf

def candidates(rows, mfr, name, aliases):
    want_m = MFR.get(mfr, norm(mfr))
    names  = [norm(n) for n in [name] + list(aliases)]
    out = []
    for r in rows:
        rm, rf = norm(r.get("manufacturer")), norm(r.get("fixture"))
        if want_m not in rm and rm not in want_m:
            continue
        rf = strip_prefix(rf, want_m)
        # Exact scores 2, containment 1. Containment is kept only so a real
        # match is not lost, and an exact hit anywhere in the list discards
        # every containment hit below — otherwise a newer GigaPointe outranks
        # the Pointe we asked for.
        score = 2 if rf in names else (1 if any(n and n in rf for n in names) else 0)
        if score:
            out.append((score, r))
    if any(s == 2 for s, _ in out):
        out = [(s, r) for s, r in out if s == 2]
    return out

def near_matches(rows, mfr, name):
    """One name is a prefix of the other, five characters or more. Catches
    "Mythos" for "Mythos 2" and "Khamsin" for "Khamsin-S" — which are real
    products, not typos, so these are reported and never auto-chosen."""
    want_m, n = MFR.get(mfr, norm(mfr)), norm(name)
    out = []
    for r in rows:
        rm, rf = norm(r.get("manufacturer")), norm(r.get("fixture"))
        if want_m not in rm and rm not in want_m:
            continue
        if len(rf) >= 5 and (n.startswith(rf) or rf.startswith(n)):
            out.append(r)
    out.sort(key=lambda r: (str(r.get("uploader")) == "Manuf.",
                            str(r.get("lastModified") or "")), reverse=True)
    return out

def rank(cands):
    def key(t):
        score, r = t
        return (score,
                1 if str(r.get("uploader")) == "Manuf." else 0,
                str(r.get("lastModified") or r.get("creationDate") or ""))
    return sorted(cands, key=key, reverse=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    a = ap.parse_args()

    s = S.session()
    rows = S.catalog(s)
    print(f"catalogue: {len(rows)} rows\n")
    print(f"  {'fixture':34} {'up':5} {'rid':>7}  {'other':>5}  chosen revision")
    print("  " + "-"*92)

    chosen, missing, skipped = [], [], []
    for fid, mfr, name, aliases, has_local in LIB:
        if fid in SKIP:
            skipped.append((fid, mfr, name)); continue
        ranked = rank(candidates(rows, mfr, name, aliases))
        if not ranked:
            missing.append((fid, mfr, name)); continue
        score, best = ranked[0]
        up = "MANUF" if str(best.get("uploader")) == "Manuf." else "user"
        print(f"  {(mfr + ' ' + name)[:34]:34} {up:5} {str(best.get('rid')):>7}  "
              f"{len(ranked)-1:>5}  {str(best.get('revision'))[:34]}")
        chosen.append((fid, best, up))

    manuf = sum(1 for _,_,u in chosen if u == "MANUF")
    print(f"\n  matched {len(chosen)}/{len(LIB)} — {manuf} manufacturer-uploaded, "
          f"{len(chosen)-manuf} community")
    if skipped:
        print("\n  deliberately skipped:")
        for fid, mfr, name in skipped:
            print(f"    {mfr + ' ' + name:34} {SKIP[fid]}")

    if missing:
        print("\n  no exact match — near matches need a human, because a trailing"
              "\n  token is a different product, not a spelling variant:")
        for fid, mfr, name in missing:
            near = near_matches(rows, mfr, name)
            if not near:
                print(f"\n    {mfr} {name}  — nothing in the catalogue")
                continue
            print(f"\n    {mfr} {name}")
            for r in near[:5]:
                up = "MANUF" if str(r.get("uploader")) == "Manuf." else "user "
                print(f"        {up} {str(r.get('rid')):>7}  {r.get('manufacturer')[:20]:20} "
                      f"{r.get('fixture')[:40]:40} {str(r.get('revision'))[:22]}")

    if not a.download:
        print("\n  (report only — pass --download to pull these files)")
        return

    print("\ndownloading:")
    for fid, row, up in chosen:
        out, err = S.download(s, str(row.get("rid")), row)
        print(f"  {'FAIL ' + err if err else 'ok   ' + out.name + f'  ({out.stat().st_size//1024} KB)'}")

if __name__ == "__main__":
    main()
