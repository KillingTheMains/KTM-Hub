"""GDTF Share client — search the catalogue and pull a file, no browser.

    python3 gdtf_share.py probe                     # what works, and whether login is needed
    python3 gdtf_share.py search "mac ultra"        # find it
    python3 gdtf_share.py get 12345 [12346 ...]     # pull by rid into gdtf/
    python3 gdtf_share.py get --name "Robin Esprite"

Then gdtf_ingest.py merges what landed. Download and merge stay separate on
purpose: the merge is the part that can quietly corrupt the library, and it
should be runnable and re-runnable without touching the network.

═══════════════════════════════════════════════════════════════════════════
VERIFIED LIVE 2026-09-10, once gdtf-share.com was allowlisted.

  login     POST  user + password, form-encoded → {"result": true, ...}
            The `user` field is the Share USERNAME, not the account email.
            The same password with the email returns 401 "No valid user or
            password provided" — identical to a bogus password, so a wrong
            field here is indistinguishable from a wrong password. A missing
            or misnamed field returns 400 "No valid information provided",
            which is how the two were told apart.
  list      GET   401 anonymously; needs the session cookie from login.
  download  GET   401 anonymously; same.
═══════════════════════════════════════════════════════════════════════════

CREDENTIALS
    Read from gdtf-share.json beside this script, or ~/.gdtf-share.json:

        {"user": "you@example.com", "password": "..."}

    The file is never printed, never logged, never echoed into an error, and
    never written to the Hub database, the project docs or an artifact. It
    stays on the machine that runs this. Nothing else in this repo reads it.
    Add it to .gitignore before the folder is ever pushed anywhere.
"""
import json, pathlib, sys, argparse, re, time

try:
    import requests
except ImportError:
    sys.exit("needs requests:  pip install requests --break-system-packages")

HERE  = pathlib.Path(__file__).parent
GDTF  = HERE / "gdtf";  GDTF.mkdir(exist_ok=True)
CACHE = HERE / "gdtf_catalog.json"
COOKIE= HERE / ".gdtf-session"

BASE = "https://gdtf-share.com"
ENDPOINTS = {
    "login":    BASE + "/apis/public/login.php",
    "list":     BASE + "/apis/public/getList.php",
    "download": BASE + "/apis/public/downloadFile.php",   # ?rid=NNN
}
UA = {"User-Agent": "KTM-Hub/1.0 (fixture library ingest)"}

def creds():
    for p in (HERE/"gdtf-share.json", pathlib.Path.home()/".gdtf-share.json"):
        if p.exists():
            d = json.loads(p.read_text())
            if d.get("user") and d.get("password"):
                return d, p
    return None, None

def session(need_login=True):
    s = requests.Session(); s.headers.update(UA)
    if COOKIE.exists():
        try: s.cookies.update(json.loads(COOKIE.read_text()))
        except Exception: pass
    if not need_login:
        return s
    c, where = creds()
    if not c:
        sys.exit("No credentials. Create gdtf-share.json beside this script:\n"
                 '  {"user": "...", "password": "..."}')
    # Try the stored value, then its local part if it looks like an email —
    # the API wants the username and the two are often the same string.
    names = [c["user"].strip()]
    if "@" in names[0]:
        names.append(names[0].split("@")[0])
    for name in names:
        r = s.post(ENDPOINTS["login"], data={"user": name, "password": c["password"]},
                   timeout=45)
        # Never surface the request body — an error must not leak the password.
        if r.status_code == 200 and _json(r).get("result") is True:
            COOKIE.write_text(json.dumps(s.cookies.get_dict()))
            return s
    sys.exit(f"Login rejected (HTTP {r.status_code}). Check {where.name} — the `user` "
             "field must be the GDTF Share username, not the account email.")

def _json(r):
    try: return r.json()
    except Exception: return {}

def probe():
    """Run this first once the domain is allowlisted. It answers the two
    questions the design depends on: does anything work anonymously, and does
    the list endpoint return the fields the search below assumes."""
    s = requests.Session(); s.headers.update(UA)
    for name, url in ENDPOINTS.items():
        try:
            r = s.get(url, timeout=45)
            body = r.text[:160].replace("\n", " ")
            j = _json(r)
            shape = (f"json keys={list(j)[:6]}" if j else f"text[:160]={body!r}")
            print(f"  {name:9} HTTP {r.status_code}  {shape}")
            if name == "list" and j:
                rows = j.get("list") or j.get("data") or (j if isinstance(j, list) else [])
                if rows:
                    print(f"    {len(rows)} rows; first row fields: {list(rows[0])}")
        except Exception as e:
            print(f"  {name:9} FAILED  {type(e).__name__}: {e}")
    c, where = creds()
    print(f"\n  credentials: {'found in ' + where.name if c else 'none on disk'}")
    print("  If list returned rows anonymously, no login is needed — drop the login step.")

def catalog(s, refresh=False):
    """The whole catalogue, cached. It is one request and thousands of rows,
    so re-fetching it per search would be rude to the site and slow for us."""
    if CACHE.exists() and not refresh:
        age = (time.time() - CACHE.stat().st_mtime) / 86400
        if age < 7:
            return json.loads(CACHE.read_text())
    r = s.get(ENDPOINTS["list"], timeout=120)
    j = _json(r)
    rows = j.get("list") or j.get("data") or (j if isinstance(j, list) else [])
    if not rows:
        sys.exit(f"List returned nothing usable (HTTP {r.status_code}). Run `probe` and fix ENDPOINTS.")
    CACHE.write_text(json.dumps(rows))
    return rows

def field(row, *names):
    for n in names:
        if row.get(n): return row[n]
    return ""

def search(rows, q, limit=25):
    """Loose match across fixture and manufacturer. Whitespace-insensitive,
    because "MAC Ultra" and "MACUltra" should find the same thing."""
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    nq = norm(q)
    hits = [r for r in rows if nq in norm(field(r,"fixture","name") + field(r,"manufacturer"))]
    hits.sort(key=lambda r: (norm(field(r,"manufacturer")), norm(field(r,"fixture","name"))))
    return hits[:limit]

def show(hits):
    if not hits: return print("  no matches")
    print(f"  {'rid':>7}  {'manufacturer':22} {'fixture':38} revision")
    for r in hits:
        print(f"  {str(field(r,'rid','id')):>7}  {field(r,'manufacturer')[:22]:22} "
              f"{field(r,'fixture','name')[:38]:38} {str(field(r,'revision','version'))[:26]}")

def download(s, rid, row=None):
    r = s.get(ENDPOINTS["download"], params={"rid": rid}, timeout=180)
    if r.status_code != 200 or len(r.content) < 2000 or r.content[:2] != b"PK":
        # A .gdtf is a ZIP. Anything that is not is an error page wearing a 200.
        return None, f"rid {rid}: not a GDTF (HTTP {r.status_code}, {len(r.content)} bytes)"
    if row:
        base = f"{field(row,'manufacturer')}@{field(row,'fixture','name')}@{field(row,'revision','version')}"
    else:
        base = f"gdtf-{rid}"
    name = re.sub(r"[^\w@().-]+", "_", base)[:150] + ".gdtf"
    out = GDTF / name
    out.write_bytes(r.content)
    return out, None

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    sp = sub.add_parser("search"); sp.add_argument("q"); sp.add_argument("--refresh", action="store_true")
    g = sub.add_parser("get")
    g.add_argument("rids", nargs="*"); g.add_argument("--name"); g.add_argument("--anon", action="store_true")
    a = ap.parse_args()

    if a.cmd == "probe": return probe()
    s = session(need_login=not getattr(a, "anon", False))

    if a.cmd == "search":
        return show(search(catalog(s, a.refresh), a.q))

    rows = catalog(s)
    by = {str(field(r,"rid","id")): r for r in rows}
    targets = list(a.rids)
    if a.name:
        hits = search(rows, a.name, limit=8)
        if len(hits) != 1:
            print(f"'{a.name}' matched {len(hits)} — name it by rid:"); return show(hits)
        targets = [str(field(hits[0],"rid","id"))]
    if not targets: return print("nothing to get")

    for rid in targets:
        out, err = download(s, rid, by.get(str(rid)))
        print(f"  {'✗ ' + err if err else '✓ ' + out.name + f'  ({out.stat().st_size//1024} KB)'}")
    print(f"\nNow merge:  python3 gdtf_ingest.py {GDTF}")

if __name__ == "__main__":
    main()
