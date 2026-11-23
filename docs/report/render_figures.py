"""Render Mermaid diagrams to cropped PNGs for the report.

Uses the Edge installation on this Windows host and the pinned Mermaid bundle
already vendored in tools/guides/assets. No network access is required.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
FIG = Path(__file__).resolve().parent / "figures"
MERMAID = ROOT / "tools" / "guides" / "assets" / "mermaid.min.js"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

DIAGRAMS = {
    "architecture": """
flowchart TD
  U["Operator / Browser<br/>GUI"] -->|"HTTP + WebSocket"| M["Master Node<br/>FastAPI + SQLite WAL"]
  M -->|"HTTP lease pull"| W1["Worker 1<br/>Agent + Process Pool"]
  M -->|"HTTP lease pull"| W2["Worker 2<br/>Agent + Process Pool"]
  M -->|"HTTP lease pull"| W9["Worker 9<br/>Agent + Process Pool"]
  W1 -->|"result + links"| M
  W2 -->|"result + links"| M
  W9 -->|"result + links"| M
""",
    "master-components": """
flowchart TD
  subgraph MASTER["Master Node"]
    NM["Node Manager"]
    TS["Task Scheduler"]
    FR["URL Frontier"]
    LB["Load Balancer<br/>capacity reservation + CPU gate"]
    FT["Fault Tolerance<br/>heartbeat + requeue"]
    AG["Result Aggregator"]
    MC["Metrics Collector"]
  end
  MASTER --> DB[("SQLite WAL")]
  MASTER --> WS["WebSocket Event Hub"]
  WS --> GUI["GUI Operator"]
""",
    "topology": """
flowchart TD
  M["Master-01<br/>192.168.18.141:8000"]
  M --- W1["Worker-01"]
  M --- W2["Worker-02"]
  M --- W3["Worker-03"]
  W1 --- W4["Worker-04"]
  W1 --- W5["Worker-05"]
  W2 --- W6["Worker-06"]
  W2 --- W7["Worker-07"]
  W3 --- W8["Worker-08"]
  W3 --- W9["Worker-09"]
""",
    "crawl-flow": """
sequenceDiagram
  autonumber
  participant O as Operator
  participant M as Master
  participant W as Worker
  O->>M: POST /api/jobs (seed, scope, budget)
  M->>M: normalisasi + dedupe + frontier
  M->>M: dekomposisi URL menjadi task
  loop lease pull setiap 0.25 s
    W->>M: POST /api/worker/lease
    M-->>W: batch task
  end
  W->>W: fetch async + parse process pool
  W->>M: POST /api/worker/tasks/{id}/result
  M->>M: upsert result + enqueue link baru
  M->>M: complete_if_done
  M-->>O: event WebSocket
""",
    "fault-tolerance": """
sequenceDiagram
  participant M as Master
  participant WA as Worker A
  participant WB as Worker B
  WA->>M: heartbeat
  Note over WA: agent berhenti / jaringan putus
  M->>M: offline monitor setiap 2 s
  Note over M: tidak ada heartbeat > 15 s
  M->>M: status Worker A = offline
  M->>M: task leased/ running di-requeue
  M-->>WB: lease task pengganti
  WB->>M: result
  M->>M: recovery time = t_selesai - t_terdeteksi
""",
    "scheduling": """
flowchart TD
  A["Heartbeat Worker"] --> B{"assigned?"}
  B -- tidak --> A
  B -- ya --> C["Lease request<br/>free_slots"]
  C --> D{"status aktif<br/>heartbeat < 30 s?"}
  D -- tidak --> A
  D -- ya --> E["room = capacity - inflight"]
  E --> F["grant = min(free_slots, room)"]
  F --> G{"cpu_usage > 92%?"}
  G -- ya --> A
  G -- tidak --> H["Pilih task queued"]
  H --> I["status = leased<br/>attempt + 1<br/>lease_deadline"]
  I --> J["Worker fetch + parse"]
""",
}


def render(name: str, source: str) -> Path:
    FIG.mkdir(parents=True, exist_ok=True)
    html = FIG / f"{name}.html"
    png = FIG / f"{name}.png"
    html.write_text(
        f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body {{ margin: 0; padding: 28px; background: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif; }}
  .mermaid {{ text-align: center; }}
</style></head>
<body>
<pre class="mermaid">
{source}
</pre>
<script src="{MERMAID.as_uri()}"></script>
<script>
mermaid.initialize({{ startOnLoad: true, theme: 'neutral', securityLevel: 'loose',
  flowchart: {{ useMaxWidth: true, htmlLabels: true }},
  sequence: {{ useMaxWidth: true }} }});
</script>
</body></html>
""",
        encoding="utf-8",
    )
    profile = Path(tempfile.mkdtemp(prefix="crawlmesh-edge-"))
    size = "1500,1200"
    if name in {"crawl-flow", "fault-tolerance"}:
        size = "1500,1500"
    subprocess.run(
        [
            str(EDGE),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--user-data-dir={profile}",
            f"--window-size={size}",
            "--virtual-time-budget=12000",
            f"--screenshot={png}",
            html.as_uri(),
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not png.exists():
        raise RuntimeError(f"Edge tidak menghasilkan {png}")
    image = Image.open(png).convert("RGB")
    background = Image.new("RGB", image.size, (255, 255, 255))
    diff = ImageChops.difference(image, background)
    bbox = diff.getbbox()
    if bbox:
        left, top, right, bottom = bbox
        margin = 24
        image = image.crop(
            (
                max(0, left - margin),
                max(0, top - margin),
                min(image.width, right + margin),
                min(image.height, bottom + margin),
            )
        )
        image.save(png, optimize=True)
    print(f"ok {png.relative_to(ROOT)} {image.size}")
    return png


def main() -> None:
    if not MERMAID.exists():
        raise SystemExit("mermaid.min.js tidak ditemukan")
    if not EDGE.exists():
        raise SystemExit("Microsoft Edge tidak ditemukan")
    for name, source in DIAGRAMS.items():
        render(name, source)


if __name__ == "__main__":
    main()
