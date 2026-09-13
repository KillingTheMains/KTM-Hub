/* ── KTM tool shim ────────────────────────────────────────────────────────
   Injected into each tool immediately after <body>, ahead of the tool's code.

   Why tools run in frames: the four ported tools were written independently
   as standalone artifacts and share 22 top-level function names between them
   — render, compute, save, esc, uid, exportCSV, snapshot, applySnapshot and
   more. Merged into one global scope they would clobber each other. A
   same-origin srcdoc frame gives each its own window, so they port unmodified
   and keep working exactly as they were verified.

   Frames have no capabilities of their own, so the shim hands each tool the
   Hub's. Same origin, so these are direct calls into the parent realm — no
   postMessage, no serialization.                                           */
(function () {
  var TOOL   = "__TOOLKEY__";
  var LEGACY = __LEGACY__;          // ported tool, or written for the Hub
  var host   = window.parent;

  /* ── Shared data layer ────────────────────────────────────────────────
     Every tool written for the Hub uses this. It reaches the real
     collections — fixtures, gear, shows — with no namespacing, because
     that shared library is the entire point of the suite.                */
  window.KTM = host && host.KTM ? host.KTM : null;

  /* ── Legacy namespacing ───────────────────────────────────────────────
     The four ported tools each save rigs at "rigs/{key}". In four separate
     stores that was fine; in one shared store they overwrite each other.
     So for those tools only, every path gets namespaced under tools/<tool>/.

     The prefix is TWO segments on purpose. Document paths must have an even
     number of segments and collections an odd number, so a one-segment
     prefix would flip every path's parity and throw:
       rigs      (1, collection) -> tools/distro/rigs      (3, collection)
       rigs/foo  (2, document)   -> tools/distro/rigs/foo  (4, document)

     New tools are NOT namespaced — they read and write the shared schema
     directly, which is why this is gated on LEGACY rather than applied to
     everything.                                                           */
  function ns(p) { return "tools/" + TOOL + "/" + p; }

  function wrapDb(db) {
    return {
      doc:        function (p) { return db.doc(ns(p)); },
      collection: function (p) { return db.collection(ns(p)); }
    };
  }

  window.claude = {
    use: function (name) {
      if (!host || !host.claude || !host.claude.use) return Promise.resolve(null);
      return Promise.resolve(host.claude.use(name)).then(function (api) {
        if (!api) return null;
        return (LEGACY && name === "db") ? wrapDb(api) : api;
      }).catch(function () { return null; });
    }
  };

  /* The Hub owns the theme; it calls this on every frame when you toggle. */
  window.__ktmTheme = function (t) {
    var r = document.documentElement;
    if (t) r.setAttribute("data-theme", t); else r.removeAttribute("data-theme");
  };
})();
