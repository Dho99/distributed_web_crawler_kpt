"""Build a single self-contained, print-ready A4 HTML guide.

Usage:  .venv\\Scripts\\python.exe tools\\guides\\build_html.py
Output: docs/CrawlMesh-Panduan-Lengkap.html
"""

from __future__ import annotations

import base64
import hashlib
import html as html_lib
import io
import re
import urllib.request
from datetime import date
from pathlib import Path

import markdown
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT = DOCS / "CrawlMesh-Panduan-Lengkap.html"
MERMAID_JS = ROOT / "tools" / "guides" / "assets" / "mermaid.min.js"
MERMAID_VERSION = "10.9.1"
MERMAID_URL = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"
MERMAID_SHA256 = "61B335A46DF05A7CE1C98378F60E5F3E77A7FB608A1056997E8A649304A936D6"
MAX_WIDTH = 1400

APPENDICES = [
    ("Lampiran A — Runbook Deployment 10 Node", DOCS / "RUNBOOK-10NODES.md"),
    ("Lampiran B — Protokol Benchmark", DOCS / "BENCHMARK.md"),
    ("Lampiran C — Referensi API", DOCS / "API.md"),
    ("Lampiran D — Technical Design Document", DOCS / "TDD.md"),
]
ARCHITECTURE = ("Lampiran F — Arsitektur Sistem", DOCS / "architecture.md")

ADR_FILES = [
    DOCS / "adr" / "0001-sqlite-instead-of-redis-postgres.md",
    DOCS / "adr" / "0002-outbound-lease-communication.md",
    DOCS / "adr" / "0003-udp-discovery-and-windows-udp-reset.md",
    DOCS / "adr" / "0004-benchmark-methodology.md",
]

IMAGE_RE = re.compile(r"<p><img alt=\"([^\"]*)\" src=\"([^\"]+)\" /></p>")
MERMAID_RE = re.compile(
    r'<pre><code class="language-mermaid">(.*?)</code></pre>', re.DOTALL
)


def image_data_uri(path: Path) -> str:
    with Image.open(path) as image:
        image = image.convert("RGB")
        if image.width > MAX_WIDTH:
            height = int(image.height * MAX_WIDTH / image.width)
            image = image.resize((MAX_WIDTH, height), Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=82, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def inline_images(html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        alt, src = match.group(1), match.group(2)
        path = (DOCS / src).resolve()
        if not path.exists():
            print(f"  ! image missing: {src}")
            return match.group(0)
        uri = image_data_uri(path)
        return (
            f'<figure><img src="{uri}" alt="{alt}">'
            f"<figcaption>{alt}</figcaption></figure>"
        )

    return IMAGE_RE.sub(replace, html)


def render_mermaid(html: str) -> str:
    """Convert fenced ```mermaid blocks into elements processed by mermaid.js."""
    if not MERMAID_JS.exists():
        return html

    def replace(match: re.Match[str]) -> str:
        source = html_lib.unescape(match.group(1)).strip()
        return f'<div class="mermaid">{source}</div>'

    return MERMAID_RE.sub(replace, html)


def ensure_mermaid() -> None:
    """Fetch the pinned Mermaid bundle once; it is intentionally not committed."""
    if MERMAID_JS.exists():
        return
    MERMAID_JS.parent.mkdir(parents=True, exist_ok=True)
    print(f"  · mengunduh mermaid {MERMAID_VERSION} ...")
    try:
        urllib.request.urlretrieve(MERMAID_URL, MERMAID_JS)
    except Exception as exc:  # noqa: BLE001 - build falls back to code blocks
        print(f"  ! mermaid tidak tersedia ({exc}); diagram tampil sebagai kode")
        return
    digest = hashlib.sha256(MERMAID_JS.read_bytes()).hexdigest().upper()
    if digest != MERMAID_SHA256:
        print(f"  ! checksum mermaid berbeda: {digest}")
    else:
        print("  · mermaid siap (checksum cocok)")


def mermaid_script() -> str:
    if not MERMAID_JS.exists():
        return ""
    source = MERMAID_JS.read_text(encoding="utf-8")
    init = (
        "<script>mermaid.initialize({startOnLoad:true,theme:'neutral',"
        "securityLevel:'loose',flowchart:{useMaxWidth:true},"
        "sequence:{useMaxWidth:true}});</script>"
    )
    return f"<script>{source}</script>{init}"


def convert(md_text: str) -> tuple[str, list[dict]]:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
        extension_configs={"toc": {"permalink": False, "toc_depth": "1-2"}},
    )
    html = md.convert(md_text)
    return html, md.toc_tokens


def render_toc(tokens: list[dict], depth: int = 1) -> str:
    items = []
    for token in tokens:
        items.append(
            f'<li class="toc-l{depth}"><a href="#{token["id"]}">{token["name"]}</a></li>'
        )
        if token.get("children") and depth < 2:
            items.append(render_toc(token["children"], depth + 1))
    if not items:
        return ""
    return f'<ul class="toc-list toc-depth-{depth}">' + "".join(items) + "</ul>"


COVER = """
<section class="cover">
  <div class="cover-grid"></div>
  <div class="cover-top">
    <span class="cover-badge">CRAWMESH</span>
    <span class="cover-meta">v0.1 · {today}</span>
  </div>
  <div class="cover-main">
    <div class="cover-brand">CRAWL MESH</div>
    <h1>Panduan Lengkap</h1>
    <p class="cover-sub">Distributed Web Crawler dengan Orkestrasi Master–Worker</p>
    <p class="cover-desc">
      Instalasi, operasi GUI, deployment 10 node, fault tolerance,
      dan protokol benchmark untuk laporan UAS.
    </p>
  </div>
  <div class="cover-bottom">
    <div><span>Arsitektur</span><strong>1 Master + 9 Worker</strong></div>
    <div><span>Komunikasi</span><strong>HTTP lease + WebSocket</strong></div>
    <div><span>Output</span><strong>GUI · SQLite · CSV</strong></div>
  </div>
</section>
<section class="print-help">
  <h2>Cara mencetak dokumen ini</h2>
  <ol>
    <li>Buka file HTML ini di Microsoft Edge, Google Chrome, atau Firefox.</li>
    <li>Tekan <kbd>Ctrl</kbd> + <kbd>P</kbd> (Windows) atau <kbd>Cmd</kbd> + <kbd>P</kbd> (macOS).</li>
    <li>Pilih <strong>Save as PDF</strong> atau printer fisik.</li>
    <li>Paper: <strong>A4</strong>. Margins: <strong>Default</strong>.</li>
    <li>Aktifkan <strong>Background graphics</strong> agar screenshot dan warna tidak hilang.</li>
    <li>Aktifkan <strong>Headers and footers</strong> bila ingin nomor halaman otomatis.</li>
  </ol>
  <p class="muted">Gambar pada dokumen ini di-embed langsung, tidak butuh koneksi internet.
  Diagram Mermaid dirender otomatis saat halaman dibuka — tunggu 1–2 detik sebelum mencetak.</p>
</section>
"""

CSS = """
:root {
  --ink: #14202b;
  --muted: #5b6b78;
  --line: #d7dee4;
  --accent: #3f7d20;
  --accent-soft: #eef7e6;
  --code: #f4f6f8;
}
* { box-sizing: border-box; }
html { background: #e9edf1; }
body {
  margin: 0;
  color: var(--ink);
  background: #e9edf1;
  font-family: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.62;
}
.print-bar {
  position: sticky; top: 0; z-index: 50;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 10px 22px; background: #0f171e; color: #dfe8ed;
  font-size: 12px; letter-spacing: .04em;
}
.print-bar strong { color: #b8f24a; }
.print-bar button {
  background: #b8f24a; color: #0c1405; border: 0; border-radius: 6px;
  padding: 8px 16px; font-weight: 700; cursor: pointer; font-size: 12px;
}
.page {
  width: 210mm; min-height: 297mm; margin: 18px auto 40px; background: #fff;
  padding: 18mm 16mm 20mm; box-shadow: 0 18px 50px rgba(16, 32, 44, .18);
}
h1, h2, h3, h4 { line-height: 1.25; color: #101c26; page-break-after: avoid; }
h1 { font-size: 20pt; margin: 0 0 10px; padding-bottom: 8px; border-bottom: 2px solid var(--accent); }
h2 { font-size: 14.5pt; margin: 22px 0 8px; }
h3 { font-size: 11.8pt; margin: 16px 0 6px; }
h4 { font-size: 10.5pt; margin: 12px 0 4px; }
p { margin: 7px 0 9px; }
ul, ol { margin: 6px 0 10px; padding-left: 20px; }
li { margin: 2px 0; }
a { color: #1f5f8b; text-decoration: none; }
strong { color: #0d1a24; }
hr { border: 0; border-top: 1px solid var(--line); margin: 18px 0; }
table {
  width: 100%; border-collapse: collapse; margin: 10px 0 14px;
  font-size: 8.6pt; page-break-inside: avoid;
}
th, td { border: 1px solid var(--line); padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #f0f4f7; font-weight: 600; }
tbody tr:nth-child(even) { background: #fafbfc; }
code {
  font-family: "Cascadia Mono", Consolas, "SFMono-Regular", monospace;
  font-size: 8.6pt; background: var(--code); padding: 1px 4px; border-radius: 3px;
}
pre {
  background: var(--code); border: 1px solid #e0e6ea; border-left: 3px solid var(--accent);
  padding: 9px 11px; border-radius: 4px; overflow-x: auto;
  page-break-inside: avoid; margin: 9px 0 12px;
}
pre code { background: none; padding: 0; font-size: 8.2pt; line-height: 1.5; white-space: pre-wrap; }
blockquote { margin: 10px 0; padding: 6px 12px; border-left: 3px solid #9db8c8; background: #f6f9fb; color: #33475a; }
figure { margin: 12px 0 16px; page-break-inside: avoid; }
figure img {
  width: 100%; height: auto; display: block;
  border: 1px solid #cfd8df; border-radius: 6px;
}
.mermaid { margin: 10px 0 14px; text-align: center; page-break-inside: avoid; }
.mermaid svg { max-width: 100%; height: auto; }
figcaption { margin-top: 5px; font-size: 8.4pt; color: var(--muted); font-style: italic; }
kbd {
  font-family: Consolas, monospace; font-size: 8.4pt; border: 1px solid #b9c4cc;
  border-bottom-width: 2px; border-radius: 3px; padding: 0 4px; background: #f4f6f8;
}
.cover {
  position: relative; color: #f2f7f9; overflow: hidden;
  background: radial-gradient(1000px 520px at 82% -10%, rgba(82,217,232,.18), transparent 60%),
              radial-gradient(720px 460px at 0% 110%, rgba(184,242,74,.14), transparent 55%),
              #0a1014;
  min-height: 242mm; padding: 18mm 18mm 14mm; page-break-after: always;
}
.cover-grid {
  position: absolute; inset: 0; opacity: .5;
  background-image: linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px);
  background-size: 42px 42px;
}
.cover-top, .cover-main, .cover-bottom { position: relative; }
.cover-top { display: flex; justify-content: space-between; align-items: center; font-size: 10px; letter-spacing: .18em; }
.cover-badge { border: 1px solid rgba(184,242,74,.5); color: #cdf98a; padding: 4px 10px; border-radius: 999px; }
.cover-meta { color: #93a6b2; }
.cover-main { margin-top: 46mm; max-width: 150mm; }
.cover-brand { font-size: 10pt; letter-spacing: .34em; color: #8fbf4a; margin-bottom: 7mm; }
.cover-main h1 { font-size: 40pt; border: 0; margin: 0; color: #fff; letter-spacing: -.02em; }
.cover-sub { font-size: 15pt; color: #b8f24a; margin: 8px 0 14px; }
.cover-desc { font-size: 11pt; color: #b3c2cb; line-height: 1.7; }
.cover-bottom { position: absolute; left: 18mm; right: 18mm; bottom: 16mm; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; border-top: 1px solid rgba(255,255,255,.14); padding-top: 10px; }
.cover-bottom span { display: block; font-size: 8px; letter-spacing: .16em; text-transform: uppercase; color: #7f94a1; }
.cover-bottom strong { font-size: 10pt; color: #e7f0f4; }
.print-help { padding: 14mm 18mm 4mm; }
.print-help h2 { margin-top: 0; }
.muted { color: var(--muted); font-size: 9pt; }
.toc h2 { margin-bottom: 4px; }
.toc-list { list-style: none; padding-left: 0; margin: 0; }
.toc-list.toc-depth-2 { padding-left: 16px; }
.toc-l1 { margin: 5px 0; font-weight: 600; font-size: 9.6pt; }
.toc-l2 { margin: 2px 0; font-weight: 400; font-size: 8.8pt; color: #3c4d5a; }
.toc a { color: inherit; }
.doc h1 { page-break-before: always; margin-top: 0; }
.doc > h1:first-of-type { page-break-before: auto; }
.doc > h2 { border-left: 3px solid var(--accent); padding-left: 8px; }
.appendix h1 { font-size: 17pt; }
.appendix .note { color: var(--muted); font-size: 9pt; }
@media print {
  html, body { background: #fff; }
  .print-bar { display: none; }
  .page { width: auto; min-height: 0; margin: 0; padding: 0; box-shadow: none; }
  @page { size: A4; margin: 15mm 14mm 16mm; }
  .cover { min-height: 240mm; margin: 0; }
  a { color: inherit; }
  figure, table, pre, blockquote { break-inside: avoid; }
  h1, h2, h3 { break-after: avoid; }
  tr, img { break-inside: avoid; }
  .appendix h1 { break-before: page; }
}
@page { size: A4; margin: 15mm 14mm 16mm; }
"""

TEMPLATE = """<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CrawlMesh — Panduan Lengkap</title>
<style>{css}</style>
</head>
<body>
<div class="print-bar">
  <span><strong>CrawlMesh</strong> · panduan lengkap · siap cetak A4</span>
  <button onclick="window.print()">Cetak / Simpan PDF</button>
</div>
{cover}
<main class="page">
<section class="toc">
  <h2>Daftar Isi</h2>
  {toc}
</section>
<div class="doc">
{body}
</div>
</main>
{mermaid_script}
</body>
</html>
"""


def main() -> None:
    print("Menyusun dokumen...")
    ensure_mermaid()
    guide_md = (DOCS / "GUIDE.md").read_text(encoding="utf-8")

    appendix_md = []
    for title, path in APPENDICES:
        text = path.read_text(encoding="utf-8")
        # Drop the document's own H1 so the appendix wrapper provides the title.
        text = re.sub(r"^# .*\n", "", text, count=1)
        appendix_md.append(f"\n\n# {title}\n\n")
        appendix_md.append(text)

    adr_md = ["\n\n# Lampiran E — Architecture Decision Records\n"]
    for path in ADR_FILES:
        adr_md.append("\n\n")
        adr_md.append(path.read_text(encoding="utf-8"))
    appendix_md.extend(adr_md)

    title, path = ARCHITECTURE
    text = re.sub(r"^# .*\n", "", path.read_text(encoding="utf-8"), count=1)
    appendix_md.append(f"\n\n# {title}\n\n")
    appendix_md.append(text)

    combined = guide_md + "".join(appendix_md)
    html, tokens = convert(combined)
    html = inline_images(html)
    html = render_mermaid(html)

    toc = render_toc(tokens)
    document = TEMPLATE.format(
        css=CSS,
        cover=COVER.format(today=date.today().isoformat()),
        toc=toc,
        body=html,
        mermaid_script=mermaid_script(),
    )

    OUT.write_text(document, encoding="utf-8")
    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"OK  {OUT.relative_to(ROOT)}  ({size_mb:.2f} MB)")
    print(f"    {len(tokens)} bagian utama, {document.count('<figure>')} gambar")


if __name__ == "__main__":
    main()
