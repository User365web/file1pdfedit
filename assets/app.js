/* File1pdfedit - all PDF processing runs locally in the visitor's browser. */
(() => {
'use strict';
const $ = (s, r = document) => r.querySelector(s);

/* ---------- mobile nav ---------- */
const navBtn = $('#navToggle'), nav = $('#nav');
if (navBtn && nav) navBtn.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  navBtn.setAttribute('aria-expanded', open);
});

const ws = $('#workspace');
if (!ws) return;
const TOOL = ws.dataset.tool;

/* ---------- lazy library loading (keeps pages fast) ---------- */
const CDN = {
  pdflib: 'https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js',
  pdfjs: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',
  worker: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js',
  jszip: 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js'
};
const loaded = {};
const loadScript = k => loaded[k] || (loaded[k] = new Promise((res, rej) => {
  const s = document.createElement('script');
  s.src = CDN[k]; s.onload = res;
  s.onerror = () => { delete loaded[k]; rej(new Error('Could not load a required library. Check your internet connection and try again.')); };
  document.head.appendChild(s);
}));
const needPdfLib = () => loadScript('pdflib');
const needPdfJs = async () => { await loadScript('pdfjs'); pdfjsLib.GlobalWorkerOptions.workerSrc = CDN.worker; };
const needZip = () => loadScript('jszip');

/* ---------- helpers ---------- */
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = b => b < 1024 ? b + ' B' : b < 1048576 ? (b / 1024).toFixed(1) + ' KB' : (b / 1048576).toFixed(2) + ' MB';
const baseName = n => n.replace(/\.[^.]+$/, '');
const isPdf = f => f.type === 'application/pdf' || /\.pdf$/i.test(f.name);
const isImg = f => /^image\/(jpeg|png|webp)$/.test(f.type) || /\.(jpe?g|png|webp)$/i.test(f.name);
const toBlobAsync = (c, type, q) => new Promise(r => c.toBlob(r, type, q));

function parseRange(str, total) {
  const out = [], seen = new Set();
  const parts = String(str || '').split(',').map(s => s.trim()).filter(Boolean);
  for (const part of parts) {
    let a, b, m = part.match(/^(\d*)\s*-\s*(\d*)$/);
    if (m) { a = m[1] ? +m[1] : 1; b = m[2] ? +m[2] : total; }
    else if (/^\d+$/.test(part)) { a = b = +part; }
    else throw new Error('Invalid page range "' + part + '". Use a format like 1-3, 5, 8-');
    if (a > b) [a, b] = [b, a];
    if (a < 1 || b > total) throw new Error('Page numbers must be between 1 and ' + total + '.');
    for (let i = a; i <= b; i++) if (!seen.has(i)) { seen.add(i); out.push(i - 1); }
  }
  if (!out.length) throw new Error('Enter at least one page number.');
  return out;
}

async function loadPdf(file, opts) {
  await needPdfLib();
  const bytes = await file.arrayBuffer();
  try {
    return await PDFLib.PDFDocument.load(bytes, Object.assign({ updateMetadata: false }, opts || {}));
  } catch (e) {
    if (/encrypt/i.test(e.message)) throw new Error('"' + file.name + '" is password-protected. Remove the password first, then try again.');
    throw new Error('Could not read "' + file.name + '". The file may be damaged or is not a valid PDF.');
  }
}
const pdfBlob = bytes => new Blob([bytes], { type: 'application/pdf' });

async function renderPage(pdf, n, dpi, type, quality) {
  const pg = await pdf.getPage(n);
  const vp = pg.getViewport({ scale: dpi / 72 });
  const c = document.createElement('canvas');
  c.width = Math.ceil(vp.width); c.height = Math.ceil(vp.height);
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height);
  await pg.render({ canvasContext: ctx, viewport: vp }).promise;
  const blob = await toBlobAsync(c, type, quality);
  c.width = c.height = 0; pg.cleanup();
  return blob;
}

/* ---------- tools ---------- */
async function compress(o) {
  const f = files[0].file, orig = f.size;
  let out;
  if (o.mode === 'basic') {
    const d = await loadPdf(f);
    out = await d.save({ useObjectStreams: true });
  } else {
    await needPdfLib(); await needPdfJs();
    const q = { high: [150, .8], med: [110, .6], low: [72, .5] }[o.level] || [110, .6];
    const src = await pdfjsLib.getDocument({ data: await f.arrayBuffer() }).promise;
    const dst = await PDFLib.PDFDocument.create();
    for (let i = 1; i <= src.numPages; i++) {
      setStatus('Compressing page ' + i + ' of ' + src.numPages + '...'); setProgress((i - 1) / src.numPages);
      const pg = await src.getPage(i), base = pg.getViewport({ scale: 1 });
      const blob = await renderPage(src, i, q[0], 'image/jpeg', q[1]);
      const img = await dst.embedJpg(await blob.arrayBuffer());
      dst.addPage([base.width, base.height]).drawImage(img, { x: 0, y: 0, width: base.width, height: base.height });
    }
    out = await dst.save();
  }
  const blob = pdfBlob(out);
  if (blob.size >= orig) return { message: 'This PDF is already well optimized and could not be made smaller with these settings. Try Strong mode or a lower image quality.', type: 'info' };
  const pct = Math.round((1 - blob.size / orig) * 100);
  return { blob, name: baseName(f.name) + '-compressed.pdf', note: 'Reduced from ' + fmt(orig) + ' to ' + fmt(blob.size) + ' (' + pct + '% smaller).' };
}

async function img2pdf(o) {
  await needPdfLib();
  const doc = await PDFLib.PDFDocument.create();
  const sizes = { a4: [595.28, 841.89], letter: [612, 792] };
  const m = { none: 0, small: 20, med: 40 }[o.margin] || 0;
  let n = 0;
  for (const it of files) {
    n++; setStatus('Adding image ' + n + ' of ' + files.length + '...'); setProgress((n - 1) / files.length);
    let bmp;
    try { bmp = await createImageBitmap(it.file); } catch (e) { throw new Error('Could not open "' + it.file.name + '". Use a valid JPG, PNG or WebP image.'); }
    let img;
    if (it.file.type === 'image/png') img = await doc.embedPng(await it.file.arrayBuffer());
    else {
      const c = document.createElement('canvas'); c.width = bmp.width; c.height = bmp.height;
      const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height); x.drawImage(bmp, 0, 0);
      img = await doc.embedJpg(await (await toBlobAsync(c, 'image/jpeg', .92)).arrayBuffer());
      c.width = c.height = 0;
    }
    const iw = bmp.width, ih = bmp.height; bmp.close && bmp.close();
    let pw, ph;
    if (o.size === 'fit') { pw = iw + 2 * m; ph = ih + 2 * m; }
    else {
      [pw, ph] = sizes[o.size] || sizes.a4;
      if (o.orient === 'land' || (o.orient === 'auto' && iw > ih)) [pw, ph] = [ph, pw];
    }
    const s = Math.min((pw - 2 * m) / iw, (ph - 2 * m) / ih), w = iw * s, h = ih * s;
    doc.addPage([pw, ph]).drawImage(img, { x: (pw - w) / 2, y: (ph - h) / 2, width: w, height: h });
  }
  return { blob: pdfBlob(await doc.save()), name: 'images.pdf', note: files.length + ' image(s) combined into one PDF.' };
}

async function merge() {
  if (files.length < 2) throw new Error('Add at least two PDF files to merge.');
  await needPdfLib();
  const out = await PDFLib.PDFDocument.create();
  for (let i = 0; i < files.length; i++) {
    setStatus('Merging file ' + (i + 1) + ' of ' + files.length + '...'); setProgress(i / files.length);
    const d = await loadPdf(files[i].file);
    (await out.copyPages(d, d.getPageIndices())).forEach(p => out.addPage(p));
  }
  return { blob: pdfBlob(await out.save()), name: 'merged.pdf', note: out.getPageCount() + ' pages in total.' };
}

async function split(o) {
  const f = files[0].file, src = await loadPdf(f), total = src.getPageCount(), base = baseName(f.name);
  if (o.mode === 'range') {
    const idx = parseRange(o.range, total), d = await PDFLib.PDFDocument.create();
    (await d.copyPages(src, idx)).forEach(p => d.addPage(p));
    return { blob: pdfBlob(await d.save()), name: base + '-pages.pdf', note: idx.length + ' page(s) extracted.' };
  }
  await needZip();
  const z = new JSZip();
  for (let i = 0; i < total; i++) {
    setStatus('Splitting page ' + (i + 1) + ' of ' + total + '...'); setProgress(i / total);
    const d = await PDFLib.PDFDocument.create();
    d.addPage((await d.copyPages(src, [i]))[0]);
    z.file(base + '-page-' + (i + 1) + '.pdf', await d.save());
  }
  return { blob: await z.generateAsync({ type: 'blob' }), name: base + '-pages.zip', note: total + ' single-page PDFs in a ZIP file.' };
}

async function rotate(o) {
  const f = files[0].file, d = await loadPdf(f), total = d.getPageCount();
  const idx = (o.pages || '').trim() ? parseRange(o.pages, total) : d.getPageIndices();
  idx.forEach(i => { const p = d.getPage(i); p.setRotation(PDFLib.degrees((p.getRotation().angle + (+o.angle) + 360) % 360)); });
  return { blob: pdfBlob(await d.save()), name: baseName(f.name) + '-rotated.pdf', note: idx.length + ' page(s) rotated.' };
}

async function removePages(o) {
  const f = files[0].file, d = await loadPdf(f), total = d.getPageCount();
  const idx = parseRange(o.range, total);
  if (idx.length >= total) throw new Error('You cannot delete every page. Leave at least one page in the PDF.');
  idx.sort((a, b) => b - a).forEach(i => d.removePage(i));
  return { blob: pdfBlob(await d.save()), name: baseName(f.name) + '-edited.pdf', note: idx.length + ' page(s) removed. ' + d.getPageCount() + ' left.' };
}

async function counter() {
  let rows = '';
  for (const it of files) {
    const d = await loadPdf(it.file, { ignoreEncryption: true });
    rows += '<div class="res-file"><h3>' + esc(it.file.name) + '</h3><p><span class="pill">' + d.getPageCount() + ' page' + (d.getPageCount() === 1 ? '' : 's') + '</span> &nbsp; ' + fmt(it.file.size) + '</p></div>';
  }
  return { html: rows };
}

const PAPER = [['A3', 841.89, 1190.55], ['A4', 595.28, 841.89], ['A5', 419.53, 595.28], ['Letter', 612, 792], ['Legal', 612, 1008]];
async function info() {
  let out = '';
  for (const it of files) {
    const f = it.file, bytes = new Uint8Array(await f.arrayBuffer());
    const d = await loadPdf(f, { ignoreEncryption: true });
    const ver = new TextDecoder().decode(bytes.slice(0, 8)).replace('%PDF-', '');
    const p = d.getPage(0), { width, height } = p.getSize();
    const name = (PAPER.find(s => (Math.abs(s[1] - width) < 3 && Math.abs(s[2] - height) < 3) || (Math.abs(s[1] - height) < 3 && Math.abs(s[2] - width) < 3)) || [])[0];
    const dt = x => x ? x.toLocaleString() : '-';
    const rows = [
      ['File name', f.name], ['File size', fmt(f.size)], ['Pages', d.getPageCount()],
      ['Page size', Math.round(width) + ' x ' + Math.round(height) + ' pt (' + (width * 25.4 / 72).toFixed(0) + ' x ' + (height * 25.4 / 72).toFixed(0) + ' mm)' + (name ? ' - ' + name : '')],
      ['Orientation', width > height ? 'Landscape' : 'Portrait'], ['PDF version', /^\d\.\d$/.test(ver) ? ver : 'Unknown'],
      ['Title', d.getTitle() || '-'], ['Author', d.getAuthor() || '-'], ['Subject', d.getSubject() || '-'],
      ['Keywords', d.getKeywords() || '-'], ['Creator', d.getCreator() || '-'], ['Producer', d.getProducer() || '-'],
      ['Created', dt(d.getCreationDate())], ['Modified', dt(d.getModificationDate())], ['Encrypted', d.isEncrypted ? 'Yes' : 'No']
    ];
    out += '<div class="res-file"><h3>' + esc(f.name) + '</h3><table class="info">' + rows.map(r => '<tr><th>' + esc(r[0]) + '</th><td>' + esc(r[1]) + '</td></tr>').join('') + '</table></div>';
  }
  return { html: out };
}

async function pdf2img(o) {
  await needPdfJs();
  const f = files[0].file, base = baseName(f.name);
  const src = await pdfjsLib.getDocument({ data: await f.arrayBuffer() }).promise;
  const idx = (o.pages || '').trim() ? parseRange(o.pages, src.numPages) : Array.from({ length: src.numPages }, (_, i) => i);
  const png = o.format === 'png', type = png ? 'image/png' : 'image/jpeg', ext = png ? 'png' : 'jpg';
  const shots = [];
  for (let k = 0; k < idx.length; k++) {
    setStatus('Converting page ' + (idx[k] + 1) + ' (' + (k + 1) + ' of ' + idx.length + ')...'); setProgress(k / idx.length);
    shots.push([base + '-page-' + (idx[k] + 1) + '.' + ext, await renderPage(src, idx[k] + 1, +o.dpi, type, .92)]);
  }
  if (shots.length === 1) return { blob: shots[0][1], name: shots[0][0], note: '1 image created.' };
  await needZip();
  const z = new JSZip(); shots.forEach(s => z.file(s[0], s[1]));
  return { blob: await z.generateAsync({ type: 'blob' }), name: base + '-images.zip', note: shots.length + ' images in a ZIP file.' };
}

async function numbers(o) {
  const f = files[0].file, d = await loadPdf(f), font = await d.embedFont(PDFLib.StandardFonts.Helvetica);
  const total = d.getPageCount(), start = parseInt(o.start, 10) || 1, size = 11, mg = 28;
  d.getPages().forEach((p, i) => {
    const n = start + i, t = o.format === 'pn' ? 'Page ' + n : o.format === 'nofm' ? n + ' / ' + (start + total - 1) : String(n);
    const { width, height } = p.getSize(), w = font.widthOfTextAtSize(t, size);
    const x = o.pos.endsWith('l') ? mg : o.pos.endsWith('r') ? width - mg - w : (width - w) / 2;
    const y = o.pos.startsWith('t') ? height - mg : mg - size / 2;
    p.drawText(t, { x, y, size, font, color: PDFLib.rgb(.2, .2, .2) });
  });
  return { blob: pdfBlob(await d.save()), name: baseName(f.name) + '-numbered.pdf', note: 'Page numbers added to ' + total + ' page(s).' };
}

async function watermark(o) {
  const text = (o.text || '').trim();
  if (!text) throw new Error('Type the watermark text first.');
  const f = files[0].file, d = await loadPdf(f), font = await d.embedFont(PDFLib.StandardFonts.HelveticaBold);
  const op = +o.opacity, ang = o.layout === 'diag' ? 45 : 0, th = ang * Math.PI / 180;
  try {
    d.getPages().forEach(p => {
      const { width, height } = p.getSize();
      let size = +o.size; const maxW = (o.layout === 'diag' ? Math.hypot(width, height) : width) * .85;
      if (font.widthOfTextAtSize(text, size) > maxW) size = size * maxW / font.widthOfTextAtSize(text, size);
      const w = font.widthOfTextAtSize(text, size);
      const x = width / 2 - (w / 2 * Math.cos(th) - .3 * size * Math.sin(th));
      const y = height / 2 - (w / 2 * Math.sin(th) + .3 * size * Math.cos(th));
      p.drawText(text, { x, y, size, font, color: PDFLib.rgb(.5, .5, .5), opacity: op, rotate: PDFLib.degrees(ang) });
    });
  } catch (e) { throw new Error('The watermark supports Latin letters, numbers and common symbols only. Remove special characters and try again.'); }
  return { blob: pdfBlob(await d.save()), name: baseName(f.name) + '-watermarked.pdf', note: 'Watermark added to every page.' };
}

async function meta(o) {
  const f = files[0].file, d = await loadPdf(f);
  d.setTitle(o.title || ''); d.setAuthor(o.author || ''); d.setSubject(o.subject || '');
  d.setKeywords((o.keywords || '').split(',').map(s => s.trim()).filter(Boolean));
  d.setModificationDate(new Date());
  return { blob: pdfBlob(await d.save()), name: baseName(f.name) + '-updated.pdf', note: 'Document properties updated.' };
}
async function metaPrefill() {
  try {
    const d = await loadPdf(files[0].file, { ignoreEncryption: true });
    $('#opt-title').value = d.getTitle() || ''; $('#opt-author').value = d.getAuthor() || '';
    $('#opt-subject').value = d.getSubject() || ''; $('#opt-keywords').value = d.getKeywords() || '';
  } catch (e) { setStatus(e.message, 'err'); }
}

/* ---------- tool configuration ---------- */
const PAGES = { k: 'pages', t: 'text', l: 'Pages (optional)', ph: 'e.g. 1-3, 5 - leave empty for all', hint: 'Leave empty to use every page.' };
const T = {
  compress: { accept: isPdf, btn: 'Compress PDF', run: compress, opts: [
    { k: 'mode', t: 'select', l: 'Compression mode', o: [['basic', 'Basic - keeps text selectable'], ['strong', 'Strong - much smaller (pages become images)']], d: 'strong' },
    { k: 'level', t: 'select', l: 'Image quality (Strong mode)', o: [['high', 'High quality'], ['med', 'Balanced'], ['low', 'Smallest size']], d: 'med', showIf: ['mode', 'strong'] }] },
  img2pdf: { accept: isImg, multi: true, sortable: true, btn: 'Convert to PDF', run: img2pdf, opts: [
    { k: 'size', t: 'select', l: 'Page size', o: [['a4', 'A4'], ['letter', 'US Letter'], ['fit', 'Same as image']], d: 'a4' },
    { k: 'orient', t: 'select', l: 'Orientation', o: [['auto', 'Automatic'], ['port', 'Portrait'], ['land', 'Landscape']], d: 'auto', showIf: ['size', 'a4,letter'] },
    { k: 'margin', t: 'select', l: 'Margin', o: [['none', 'None'], ['small', 'Small'], ['med', 'Medium']], d: 'none' }] },
  merge: { accept: isPdf, multi: true, sortable: true, btn: 'Merge PDFs', run: merge, opts: [] },
  split: { accept: isPdf, btn: 'Split PDF', run: split, opts: [
    { k: 'mode', t: 'select', l: 'Split mode', o: [['range', 'Extract selected pages into one PDF'], ['all', 'Save every page as its own PDF (ZIP)']], d: 'range' },
    { k: 'range', t: 'text', l: 'Pages to extract', ph: 'e.g. 1-3, 5, 8-', showIf: ['mode', 'range'] }] },
  rotate: { accept: isPdf, btn: 'Rotate PDF', run: rotate, opts: [
    { k: 'angle', t: 'select', l: 'Rotation', o: [['90', '90 degrees clockwise'], ['180', '180 degrees'], ['270', '90 degrees counter-clockwise']], d: '90' }, PAGES] },
  counter: { accept: isPdf, multi: true, auto: true, btn: 'Count pages', run: counter, opts: [] },
  info: { accept: isPdf, multi: true, auto: true, btn: 'Show PDF info', run: info, opts: [] },
  delete: { accept: isPdf, btn: 'Delete pages', run: removePages, opts: [
    { k: 'range', t: 'text', l: 'Pages to delete', ph: 'e.g. 2, 4-6' }] },
  pdf2img: { accept: isPdf, btn: 'Convert to images', run: pdf2img, opts: [
    { k: 'format', t: 'select', l: 'Image format', o: [['jpg', 'JPG'], ['png', 'PNG']], d: 'jpg' },
    { k: 'dpi', t: 'select', l: 'Quality', o: [['72', 'Screen (72 DPI)'], ['150', 'Standard (150 DPI)'], ['200', 'High (200 DPI)']], d: '150' }, PAGES] },
  numbers: { accept: isPdf, btn: 'Add page numbers', run: numbers, opts: [
    { k: 'pos', t: 'select', l: 'Position', o: [['bc', 'Bottom center'], ['br', 'Bottom right'], ['bl', 'Bottom left'], ['tc', 'Top center'], ['tr', 'Top right'], ['tl', 'Top left']], d: 'bc' },
    { k: 'format', t: 'select', l: 'Format', o: [['n', '1, 2, 3'], ['pn', 'Page 1, Page 2'], ['nofm', '1 / 10, 2 / 10']], d: 'n' },
    { k: 'start', t: 'number', l: 'Start numbering at', d: '1' }] },
  watermark: { accept: isPdf, btn: 'Add watermark', run: watermark, opts: [
    { k: 'text', t: 'text', l: 'Watermark text', ph: 'e.g. CONFIDENTIAL', d: 'CONFIDENTIAL' },
    { k: 'layout', t: 'select', l: 'Layout', o: [['diag', 'Diagonal'], ['flat', 'Horizontal']], d: 'diag' },
    { k: 'size', t: 'select', l: 'Text size', o: [['48', 'Small'], ['72', 'Medium'], ['110', 'Large']], d: '72' },
    { k: 'opacity', t: 'select', l: 'Opacity', o: [['.15', 'Light'], ['.3', 'Medium'], ['.5', 'Strong']], d: '.3' }] },
  meta: { accept: isPdf, btn: 'Save properties', run: meta, onAdd: metaPrefill, opts: [
    { k: 'title', t: 'text', l: 'Title' }, { k: 'author', t: 'text', l: 'Author' },
    { k: 'subject', t: 'text', l: 'Subject' }, { k: 'keywords', t: 'text', l: 'Keywords', hint: 'Separate with commas.' }] }
};
const cfg = T[TOOL];
if (!cfg) return;

/* ---------- UI ---------- */
let files = [], uid = 0, busy = false, lastUrl = null;
const zone = $('#dropzone'), input = $('#fileInput'), list = $('#fileList'), optsBox = $('#opts'),
  runBtn = $('#runBtn'), clearBtn = $('#clearBtn'), statusEl = $('#status'), resEl = $('#result'), prog = $('#progress');
runBtn.textContent = cfg.btn;

optsBox.innerHTML = cfg.opts.map(f => {
  const id = 'opt-' + f.k, h = f.hint ? '<span class="hint">' + esc(f.hint) + '</span>' : '';
  const show = f.showIf ? ' data-showif="' + f.showIf.join(':') + '"' : '';
  if (f.t === 'select') return '<label' + show + '>' + esc(f.l) + '<select id="' + id + '">' + f.o.map(o => '<option value="' + o[0] + '"' + (o[0] === f.d ? ' selected' : '') + '>' + esc(o[1]) + '</option>').join('') + '</select>' + h + '</label>';
  return '<label' + show + '>' + esc(f.l) + '<input id="' + id + '" type="' + f.t + '" value="' + esc(f.d || '') + '" placeholder="' + esc(f.ph || '') + '" autocomplete="off">' + h + '</label>';
}).join('');
if (!cfg.opts.length) optsBox.style.display = 'none';

function getOpts() { const o = {}; cfg.opts.forEach(f => { o[f.k] = $('#opt-' + f.k).value; }); return o; }
function syncOpts() {
  const o = getOpts();
  optsBox.querySelectorAll('[data-showif]').forEach(l => {
    const [k, v] = l.dataset.showif.split(':'); l.style.display = v.split(',').includes(o[k]) ? '' : 'none';
  });
}
optsBox.addEventListener('change', syncOpts); syncOpts();

function setStatus(msg, type) { statusEl.textContent = msg || ''; statusEl.className = type || ''; }
function setProgress(p) {
  if (p < 0) { prog.style.display = 'none'; return; }
  prog.style.display = 'block'; prog.firstElementChild.style.width = Math.round(p * 100) + '%';
}
function clearResult() { resEl.innerHTML = ''; if (lastUrl) { URL.revokeObjectURL(lastUrl); lastUrl = null; } }

function renderList() {
  ws.classList.toggle('has-files', files.length > 0);
  list.innerHTML = files.map((f, i) => '<li data-id="' + f.id + '"><span class="nm" title="' + esc(f.file.name) + '">' + esc(f.file.name) + '</span><span class="sz">' + fmt(f.file.size) + '</span>' +
    (cfg.sortable && files.length > 1 ? '<button type="button" data-act="up" aria-label="Move up"' + (i === 0 ? ' disabled' : '') + '>&uarr;</button><button type="button" data-act="down" aria-label="Move down"' + (i === files.length - 1 ? ' disabled' : '') + '>&darr;</button>' : '') +
    '<button type="button" data-act="rm" aria-label="Remove file">&times;</button></li>').join('');
}
list.addEventListener('click', e => {
  const b = e.target.closest('button[data-act]'); if (!b) return;
  const id = +b.closest('li').dataset.id, i = files.findIndex(f => f.id === id);
  if (b.dataset.act === 'rm') files.splice(i, 1);
  else { const j = b.dataset.act === 'up' ? i - 1 : i + 1; if (files[j]) [files[i], files[j]] = [files[j], files[i]]; }
  clearResult(); setStatus(''); renderList();
});

function addFiles(fl) {
  const ok = Array.from(fl).filter(cfg.accept);
  if (!ok.length) { setStatus(cfg.accept === isImg ? 'Please choose JPG, PNG or WebP images.' : 'Please choose a PDF file.', 'err'); return; }
  if (!cfg.multi) files = [];
  ok.forEach(f => files.push({ id: ++uid, file: f }));
  if (!cfg.multi && ok.length > 1) setStatus('This tool works with one file at a time. Using "' + ok[0].name + '".', 'info'); else setStatus('');
  clearResult(); renderList();
  if (cfg.onAdd) cfg.onAdd();
  if (cfg.auto) runBtn.click();
}

zone.addEventListener('click', e => { if (e.target !== input) input.click(); });
zone.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); } });
input.addEventListener('change', () => { addFiles(input.files); input.value = ''; });
['dragenter', 'dragover'].forEach(ev => zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.add('over'); }));
['dragleave', 'drop'].forEach(ev => zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.remove('over'); }));
zone.addEventListener('drop', e => { if (e.dataTransfer && e.dataTransfer.files.length) addFiles(e.dataTransfer.files); });
['dragover', 'drop'].forEach(ev => window.addEventListener(ev, e => e.preventDefault())); /* stop the browser opening files dropped outside the zone */

clearBtn.addEventListener('click', () => { files = []; clearResult(); setStatus(''); setProgress(-1); renderList(); });

runBtn.addEventListener('click', async () => {
  if (busy) return;
  if (!files.length) { setStatus('Add a file first.', 'err'); return; }
  busy = true; runBtn.disabled = true; clearResult(); setStatus('Working...'); setProgress(0);
  try {
    const r = await cfg.run(getOpts());
    setProgress(1);
    if (r.html) { resEl.innerHTML = r.html; setStatus(''); }
    else if (r.blob) {
      lastUrl = URL.createObjectURL(r.blob);
      resEl.innerHTML = '<div class="done"><div><strong>Done!</strong> ' + esc(r.note || '') + '</div><a class="btn" href="' + lastUrl + '" download="' + esc(r.name) + '">Download ' + esc(r.name) + ' (' + fmt(r.blob.size) + ')</a></div>';
      setStatus('');
    } else setStatus(r.message || '', r.type || 'info');
  } catch (e) {
    console.error(e); setStatus(e.message || 'Something went wrong. Please try again.', 'err'); setProgress(-1);
  } finally {
    busy = false; runBtn.disabled = false; setTimeout(() => setProgress(-1), 700);
  }
});
})();
