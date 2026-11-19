"""Seed a demo cluster and capture screenshots for the printable guide.

Run from repo root:  .venv\\Scripts\\python.exe tools\\guides\\capture.py

Keeps a backup of the existing SQLite database and restores it afterwards.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx
import psutil

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
IMG_DIR = ROOT / "docs" / "guides" / "img"
DATA = ROOT / "data"
BASE = "http://127.0.0.1:8000"
LOGS = DATA / "guide-logs"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def log(message: str) -> None:
    print(f"[capture] {message}", flush=True)


def stop_services() -> None:
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"] or [])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if "capture.py" in cmdline or "build_html.py" in cmdline:
            continue
        if "master.app.main" in cmdline or "worker.agent" in cmdline:
            try:
                proc.kill()
            except psutil.Error:
                pass
    time.sleep(1.0)


def start(cmd: list[str], name: str) -> subprocess.Popen:
    LOGS.mkdir(parents=True, exist_ok=True)
    out = (LOGS / f"{name}.log").open("w", encoding="utf-8")
    err = (LOGS / f"{name}.err.log").open("w", encoding="utf-8")
    return subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=out,
        stderr=err,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def wait_health(timeout: float = 60.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = httpx.get(f"{BASE}/api/health", timeout=2.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    raise RuntimeError("master tidak siap")


def wait_jobs_done(job_id: str, timeout: float = 240.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = httpx.get(f"{BASE}/api/jobs/{job_id}", timeout=5.0).json()
        if job["status"] in ("completed", "cancelled", "failed"):
            return job
        time.sleep(1.0)
    raise RuntimeError(f"job {job_id} tidak selesai tepat waktu")


def wait_experiment(exp_id: str, timeout: float = 300.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        exp = httpx.get(f"{BASE}/api/experiments/{exp_id}", timeout=5.0).json()
        if exp["status"] not in ("pending", "running"):
            return exp
        time.sleep(1.5)
    raise RuntimeError(f"experiment {exp_id} tidak selesai tepat waktu")


def backup_db() -> None:
    for suffix in ("", "-wal", "-shm"):
        src = DATA / f"crawlmesh.db{suffix}"
        dst = DATA / f"crawlmesh.backup.db{suffix}"
        if dst.exists():
            dst.unlink()
        if src.exists():
            shutil.copy2(src, dst)


def restore_db() -> None:
    for suffix in ("", "-wal", "-shm"):
        current = DATA / f"crawlmesh.db{suffix}"
        backup = DATA / f"crawlmesh.backup.db{suffix}"
        if current.exists():
            current.unlink()
        if backup.exists():
            shutil.move(backup, current)


def shot(page, name: str, *, full: bool = True, pause: float = 0.6) -> None:
    page.wait_for_timeout(int(pause * 1000))
    path = IMG_DIR / f"{name}.jpg"
    page.screenshot(path=str(path), full_page=full, type="jpeg", quality=88)
    log(f"screenshot {path.name}")


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    backup_db()
    stop_services()
    for suffix in ("", "-wal", "-shm"):
        target = DATA / f"crawlmesh.db{suffix}"
        if target.exists():
            target.unlink()
    log("database demo disiapkan")

    master = start([str(PY), "-m", "master.app.main"], "master")
    wait_health()

    cluster = httpx.post(
        f"{BASE}/api/cluster/init", json={"name": "CrawlMesh Lab"}, timeout=10.0
    ).json()
    token = cluster["pairing_token"]
    log(f"cluster {cluster['cluster_id']}")

    worker_specs = [("8010", "5600"), ("8011", "5601")]
    for port, discovery_port in worker_specs:
        start(
            [
                str(PY), "-m", "worker.agent",
                "--master", BASE, "--token=" + token,
                "--port", port, "--pool-size", "4",
                "--discovery-port", discovery_port,
                "--state-dir", f"data/agent-demo-{port}",
            ],
            f"worker-{port}",
        )

    # Ghost agent: online on UDP discovery but pointed at an unreachable master.
    # It demonstrates the "available" card and the add-by-IP onboarding path.
    ghost = start(
        [
            str(PY), "-m", "worker.agent",
            "--master", "http://127.0.0.1:9", "--token=" + token,
            "--port", "8012", "--pool-size", "1",
            "--discovery-port", "5599",
            "--state-dir", "data/agent-demo-8012",
        ],
        "worker-ghost",
    )
    time.sleep(7.0)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
        except Exception:
            browser = playwright.chromium.launch(
                executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                headless=True,
            )
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000}, device_scale_factor=2
        )
        page = context.new_page()
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector("text=Cluster members", timeout=40000)
        page.wait_for_timeout(1200)

        # ---------------------------------------------------------- discovery
        page.get_by_role("link", name="Node Discovery").click()
        page.get_by_role("button", name="scan network").click()
        page.wait_for_selector("text=available", timeout=20000)
        shot(page, "02-discovery-scan")

        # Drop the discovery-only demo agent, then enrol the two real workers
        # through the manual add-by-IP form.
        nodes = httpx.get(f"{BASE}/api/nodes", timeout=5.0).json()
        for node in nodes:
            if node.get("port") == 8012:
                httpx.post(f"{BASE}/api/nodes/{node['worker_id']}/remove", timeout=5.0)
        ghost.kill()

        for port in ("8010", "8011"):
            page.locator('input[placeholder="192.168.18.142"]').fill("127.0.0.1")
            page.locator("form input").nth(1).fill(port)
            page.get_by_role("button", name="probe & register").click()
            page.wait_for_timeout(1600)
            page.get_by_role("button", name="assign").last.click()
            page.wait_for_timeout(1200)
        shot(page, "03-discovery-enrolled")

        # ---------------------------------------------------------- topology
        page.get_by_role("link", name="Cluster").click()
        page.wait_for_selector("text=node inspector", timeout=20000)
        shot(page, "04-topology")

        page.locator("button", has_text="8010").first.click()
        page.wait_for_timeout(800)
        shot(page, "05-topology-inspector")

        # ------------------------------------------------------------- crawl
        page.get_by_role("link", name="Crawl Jobs").click()
        page.wait_for_selector("text=Create Crawl Job", timeout=20000)
        fields = page.locator("form input")
        fields.nth(0).fill("Bench Crawl 2 Workers")
        fields.nth(1).fill("http://127.0.0.1:8000/bench/")
        fields.nth(2).fill("150")
        fields.nth(3).fill("2")
        fields.nth(4).fill("5")
        fields.nth(5).fill("10")
        fields.nth(6).fill("0.05")
        shot(page, "06-jobs-form")

        page.get_by_role("button", name="start crawling").click()
        page.wait_for_timeout(2500)
        shot(page, "07-jobs-running")

        page.get_by_role("link", name="Task Monitor").click()
        page.wait_for_timeout(2000)
        shot(page, "08-tasks")

        jobs = httpx.get(f"{BASE}/api/jobs", timeout=5.0).json()
        job = jobs[0]
        finished = wait_jobs_done(job["job_id"])
        log(f"job {finished['job_id']} {finished['status']} pages={finished['pages_crawled']}")

        page.get_by_role("link", name="Results").click()
        page.wait_for_timeout(2000)
        shot(page, "09-results")

        # ------------------------------------------------------- performance
        page.get_by_role("link", name="Performance Lab").click()
        page.wait_for_selector("text=Run experiment", timeout=20000)
        page.wait_for_timeout(800)
        shot(page, "10-performance-form")

        start_payload = {
            "experiment_type": "scalability",
            "maximum_pages": 100,
            "maximum_depth": 2,
            "batch_size": 5,
            "domain_delay": 0.02,
            "repeat": 1,
        }
        exp = httpx.post(f"{BASE}/api/experiments/run", json=start_payload, timeout=15.0).json()
        page.wait_for_timeout(2500)
        shot(page, "11-performance-running")
        wait_experiment(exp["experiment_id"])
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(2500)
        shot(page, "12-performance-curve")

        # ------------------------------------------------------- experiments
        page.get_by_role("link", name="Experiment History").click()
        page.wait_for_timeout(1800)
        shot(page, "13-experiments-table")

        page.locator("tr", has_text="Distributed").first.click()
        page.wait_for_timeout(1800)
        shot(page, "14-experiments-detail")

        # ---------------------------------------------------------- settings
        page.get_by_role("link", name="Settings").click()
        page.wait_for_timeout(1000)
        shot(page, "15-settings")

        # ---------------------------------------------------------- overview
        page.goto(f"{BASE}/", wait_until="networkidle")
        page.wait_for_timeout(2500)
        shot(page, "01-overview")

        context.close()
        browser.close()

    stop_services()
    restore_db()
    log("selesai, database lama dipulihkan")
    _ = master


if __name__ == "__main__":
    main()

