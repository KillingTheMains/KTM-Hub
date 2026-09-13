/* Pull the gear catalogs out of the legacy sources.

   The two Pre-Pro files are 112 KB and 245 KB of hand-written app code; the
   arrays we want are buried in them. Rather than parse HTML, find the array
   literal by name, brace-balance to its close, and evaluate just that literal.
   Nothing else in those files is executed or read. */
const fs = require('fs');

function literalAfter(src, name) {
  const i = src.indexOf(name);
  if (i < 0) throw new Error(`not found: ${name}`);
  const open = src.indexOf('[', i);
  if (open < 0) throw new Error(`no array literal after ${name}`);
  let depth = 0, inStr = null, esc = false;
  for (let p = open; p < src.length; p++) {
    const c = src[p];
    if (esc) { esc = false; continue; }
    if (c === '\\') { esc = true; continue; }
    if (inStr) { if (c === inStr) inStr = null; continue; }
    if (c === '"' || c === "'" || c === '`') { inStr = c; continue; }
    if (c === '[') depth++;
    else if (c === ']') { depth--; if (depth === 0) return src.slice(open, p + 1); }
  }
  throw new Error(`unbalanced literal for ${name}`);
}

const evalLit = (src, name) => new Function('return ' + literalAfter(src, name))();

const TP = '/mnt/user-data/uploads/Truck Packer/';
const PP = '/mnt/user-data/uploads/Pre-Pro-Paperwork/';

// ── Truck Packer: the 41-item Christie Lites pack catalog ────────────────
const libSrc = fs.readFileSync(TP + 'src/data/library.js', 'utf8');
const packItems = evalLit(libSrc, 'DEFAULT_LIBRARY');

// ── Pre-Pro: truss products (weightPerFt is real manufacturer data that
//    has never been read anywhere in that codebase) ───────────────────────
const trussSrc = fs.readFileSync(PP + 'Truss Builder.html', 'utf8');
const truss = evalLit(trussSrc, 'TRUSS_LIBRARY');

// ── Pre-Pro: rack equipment roster with RU heights and port maps ─────────
const rackSrc = fs.readFileSync(PP + 'Rack Builder.html', 'utf8');
const rackEq = evalLit(rackSrc, 'BUILTIN_TYPES');

fs.writeFileSync('gear_raw.json', JSON.stringify({ packItems, truss, rackEq }, null, 1));

console.log('pack items :', packItems.length, '→', JSON.stringify(packItems[0]));
console.log('truss      :', truss.length, '→', JSON.stringify(truss[0]));
console.log('rack equip :', rackEq.length, '→',
  JSON.stringify({ ...rackEq[0], ports: `[${(rackEq[0].ports || []).length} ports]` }));
