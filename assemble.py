"""Assemble the KTM Hub: shell template + every tool as a srcdoc frame.

Tool sources are read, shimmed and embedded here in the container. They are
never printed, so hundreds of KB of working code stays out of the conversation.

LEGACY tools are the four ported from standalone artifacts. Their store paths
get namespaced under tools/<tool>/ because all four save rigs at "rigs/{key}"
and would otherwise overwrite each other. Tools written for the Hub are not
namespaced — they read and write the shared schema directly.
"""
import json, pathlib, re, sys

HERE    = pathlib.Path(__file__).parent
UPLOADS = HERE   # legacy tool sources live beside this script (was the Cowork VM upload path)
SHIM    = (HERE / "ktm-shim.js").read_text()

#      key       source path                          legacy
TOOLS = [
    ("distro", UPLOADS / "distro-plot.html",          True),
    ("patch",  UPLOADS / "patch-plot.html",           True),
    ("truss",  UPLOADS / "truss-plot.html",           True),
    ("pull",   UPLOADS / "pull-plot.html",            True),
    ("truck",  HERE    / "truck-plot.html",           False),
    ("trusslist", HERE / "truss-list.html",         False),
    ("rack",   HERE    / "rack-plot.html",            False),
    ("loom",   HERE    / "loom-plot.html",            False),
    ("net",    HERE    / "net-plot.html",             False),
    ("label",  HERE    / "label-plot.html",           False),
    ("order",  HERE    / "shop-order.html",           False),
]

def shim_into(html: str, key: str, legacy: bool) -> str:
    """Insert the shim immediately after <body> so it runs before the tool's code."""
    body = (SHIM.replace("__TOOLKEY__", key)
                .replace("__LEGACY__", "true" if legacy else "false"))
    block = "\n<script>\n" + body + "</script>\n"
    m = re.search(r"<body[^>]*>", html, re.I)
    if not m:
        sys.exit(f"{key}: no <body> tag found — refusing to guess where the shim goes")
    return html[:m.end()] + block + html[m.end():]

bundle, report = {}, []
for key, path, legacy in TOOLS:
    if not path.exists():
        sys.exit(f"missing source: {path}")
    raw = html = path.read_text()

    if legacy:
        # Sanity: these must be the published tools, not something else.
        for needle in ('claude.use("db")', 'claude.use("downloads")'):
            if needle not in raw:
                sys.exit(f"{key}: expected {needle} — wrong file?")
    else:
        if "window.KTM" not in raw:
            sys.exit(f"{key}: a hub-native tool must use window.KTM — wrong file?")

    out = shim_into(raw, key, legacy)
    if out.count("__ktmTheme") != 1:
        sys.exit(f"{key}: shim injected {out.count('__ktmTheme')} times, expected 1")
    bundle[key] = out
    report.append((key, len(raw), len(out), "legacy" if legacy else "native"))

tpl = (HERE / "ktm-hub.template.html").read_text()
if "/*__TOOLSRC__*/" not in tpl:
    sys.exit("template has no /*__TOOLSRC__*/ placeholder")

# json.dumps gives a correctly escaped JS string literal for each document.
# Frames are assigned via iframe.srcdoc from JS, so no HTML attribute escaping
# is involved and the tool markup survives byte for byte.
payload = ("const TOOLSRC = " +
           json.dumps(bundle, ensure_ascii=False).replace("</script", "<\\/script") +
           ";")

final = tpl.replace("/*__TOOLSRC__*/", payload)
(HERE / "ktm-hub.html").write_text(final)

print(f"{'tool':8} {'source':>9} {'shimmed':>9}  kind")
for key, a, b, kind in report:
    print(f"{key:8} {a:9,} {b:9,}  {kind}")
print(f"\nshell    {len(tpl):9,}")
print(f"bundle   {len(final):9,}  ({len(final)/1024/1024:.2f} MB of a 16 MB cap)")
