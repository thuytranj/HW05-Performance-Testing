#!/usr/bin/env python3
"""HW05 local isolated runtime, CSV preparation and evidence-preserving k6 runner."""
import argparse
import csv
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime/backend"
PIDFILE = ROOT / ".runtime/backend.pid"
REPORTER = "https://raw.githubusercontent.com/benc-uk/k6-reporter/3.0.4/dist/bundle.js"


def now():
    return datetime.now(timezone.utc).isoformat()


def config():
    return json.loads((ROOT / "perf.config.json").read_text())


def event(kind, **fields):
    with (ROOT / "evidence/events.jsonl").open("a") as f:
        f.write(json.dumps(dict(timestamp=now(), event=kind, **fields), ensure_ascii=False) + "\n")


def verify_source(cfg):
    for relative, expected in cfg["source_sha256"].items():
        path = Path(cfg["project"]) / relative
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Source changed: {relative}; re-discover in a fresh workspace and review adapter")


def copy_backend(cfg):
    verify_source(cfg)
    if (RUNTIME / "database.sqlite").is_symlink():
        raise ValueError("Refusing a symlinked runtime database")
    for name in ["server.js", "database.js", "package.json", "package-lock.json"]:
        shutil.copy2(Path(cfg["project"]) / "backend" / name, RUNTIME / name)
    path = RUNTIME / "server.js"
    text = path.read_text()
    text, changes = re.subn(r"const PORT\s*=\s*\d+\s*;", f"const PORT = {cfg['port']};", text, count=1)
    if changes != 1:
        raise ValueError("Could not adapt runtime port")
    text = text.replace("app.listen(PORT, () =>", 'app.listen(PORT, "127.0.0.1", () =>')
    path.write_text(text)
    (ROOT / "evidence/runtime-adaptation.json").write_text(json.dumps({
        "source_sha256": cfg["source_sha256"], "runtime_server_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "changes": [f"PORT={cfg['port']}", "bind loopback 127.0.0.1"],
        "database": str(RUNTIME / "database.sqlite"), "original_database_modified": False}, indent=2) + "\n")


def install(cfg):
    copy_backend(cfg)
    # Explicit install command; no dependency installation during discovery/generation.
    subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=RUNTIME, check=True)
    vendor = ROOT / "scripts/lib/vendor"
    vendor.mkdir(exist_ok=True)
    target = vendor / "k6-reporter.js"
    with urllib.request.urlopen(REPORTER, timeout=60) as response:
        content = response.read()
    target.write_bytes(content)
    license_url = "https://raw.githubusercontent.com/benc-uk/k6-reporter/3.0.4/LICENSE"
    with urllib.request.urlopen(license_url, timeout=30) as response:
        (vendor / "LICENSE.k6-reporter").write_bytes(response.read())
    (ROOT / "data/dependencies.json").write_text(json.dumps({"reporter_url": REPORTER,
        "sha256": hashlib.sha256(content).hexdigest(), "k6": subprocess.check_output(["k6", "version"], text=True).strip(),
        "node": subprocess.check_output(["node", "--version"], text=True).strip()}, indent=2) + "\n")
    event("dependencies_installed", reporter=REPORTER)


def owned_pid():
    if not PIDFILE.exists():
        return None
    raw_pid = PIDFILE.read_text().strip()
    if not raw_pid:
        PIDFILE.unlink(missing_ok=True)
        return None
    pid = int(raw_pid)
    try:
        os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        pass
    proc = subprocess.run(["ps", "-p", str(pid), "-o", "state=,command="], capture_output=True, text=True)
    line = proc.stdout.strip()
    if proc.returncode or not line:
        PIDFILE.unlink(missing_ok=True)
        return None
    parts = line.split(None, 1)
    state = parts[0] if parts else ""
    cmd = parts[1] if len(parts) > 1 else ""
    # Never kill a PID recycled into another process, another Node server or a user backend.
    if state.startswith("Z") or str(RUNTIME / "server.js") not in cmd:
        PIDFILE.unlink(missing_ok=True)
        return None
    return pid


def stop():
    if (ROOT / ".runtime/run.lock").exists():
        raise ValueError("A test owns run.lock; refusing to stop backend during measurement")
    pid = owned_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
        for _ in range(50):
            try:
                os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                pass
            if not owned_pid():
                break
            time.sleep(.1)
        else:
            raise ValueError("Managed backend did not stop; inspect PID before retrying")
    PIDFILE.unlink(missing_ok=True)


def prepare(cfg):
    database = RUNTIME / "database.sqlite"
    # Only the isolated path is writable by this helper.
    if database.resolve() == (Path(cfg["project"]) / "backend/database.sqlite").resolve():
        raise ValueError("Refusing original database")
    with sqlite3.connect(database, timeout=10) as db:
        db.row_factory = sqlite3.Row
        required = {"id", "name", "email", "password", "role", "login_attempts", "locked_until", "shipping_address"}
        if not required.issubset({r[1] for r in db.execute("PRAGMA table_info(users)")}):
            raise ValueError("User schema changed")
        products = db.execute("SELECT id,name,price FROM products ORDER BY id").fetchall()
        if not products:
            raise ValueError("No seeded products")
        snapshot = {str(r["id"]): dict(r) for r in products}
        records = []
        for i in range(cfg["accounts"]):
            email, password = f"hw05.vu{i + 1:04d}@example.test", f"Hw05VU{i + 1:04d}!"
            address = f"{i + 1} Nguyen Trai, Quan 5, TP.HCM"
            found = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchall()
            if len(found) > 1:
                raise ValueError(f"Duplicate seeded identity {email}")
            if found:
                db.execute("UPDATE users SET password=?,login_attempts=0,locked_until=NULL,shipping_address=?,role='user' WHERE id=?", (password, address, found[0][0]))
            else:
                db.execute("INSERT INTO users(name,email,password,role,shipping_address) VALUES(?,?,?,'user',?)", (f"HW05 VU {i + 1}", email, password, address))
            product = products[i % len(products)]
            records.append(dict(email=email, password=password, keyword=product["name"], productId=product["id"], quantity=1, shippingAddress=address))
        for item in records:
            verified = db.execute("SELECT password,login_attempts,locked_until FROM users WHERE email=?", (item["email"],)).fetchone()
            if verified[0] != item["password"] or verified[1] != 0 or verified[2] is not None:
                raise ValueError("Credential/lockout verification failed")
    csvpath = ROOT / "data/e2e_test_data.csv"
    with csvpath.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "password", "keyword", "productId", "quantity", "shippingAddress"])
        writer.writeheader(); writer.writerows(records)
    (ROOT / "data/seed_snapshot.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    event("data_prepared", rows=len(records), database=str(database), stock_restore="N/A: no stock column in this SUT")
    print(f"Verified {len(records)} independent test accounts and CSV rows against isolated SQLite seed.")


def reset(cfg):
    if (ROOT / ".runtime/run.lock").exists():
        raise ValueError("A test owns run.lock; do not reset during measurement")
    stop()
    copy_backend(cfg)
    if not (RUNTIME / "node_modules/express").exists():
        raise ValueError("Run python3 scripts/perf.py install first")
    # Require the chosen port to be free; never replace an existing SUT/service.
    for attempt in range(10):
        try:
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                probe.bind(("127.0.0.1", cfg["port"]))
            break
        except OSError:
            if attempt == 9:
                raise
            time.sleep(.2)
    with (ROOT / ".runtime/backend.log").open("a") as log:
        process = subprocess.Popen(["node", str(RUNTIME / "server.js")], cwd=RUNTIME, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
    PIDFILE.write_text(str(process.pid))
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise ValueError("Backend exited; see .runtime/backend.log")
            try:
                with urllib.request.urlopen(cfg["base_url"] + "/api/products", timeout=1) as response:
                    products = json.loads(response.read())
                with sqlite3.connect(RUNTIME / "database.sqlite") as db:
                    users = db.execute("SELECT count(*) FROM users").fetchone()[0]
                if len(products) >= 5 and users >= 2:
                    break
            except (OSError, ValueError, sqlite3.Error):
                pass
            time.sleep(.1)
        else:
            raise ValueError("Seed readiness timed out")
        prepare(cfg)
    except Exception:
        stop()
        raise
    event("reset", backend_pid=process.pid, effects="isolated DB reseeded; RAM cart cleared; login unlocked; test orders removed")
    print(f"Backend PID {process.pid} ready at {cfg['base_url']}; original DB untouched. Stock: N/A.")


def monitor(pid, path, finished):
    with path.open("w", newline="") as f:
        writer = csv.writer(f); writer.writerow(["timestamp_utc", "backend_pid", "cpu_percent", "rss_kib"])
        while not finished.is_set():
            process = subprocess.run(["ps", "-p", str(pid), "-o", "%cpu=,rss="], capture_output=True, text=True)
            values = process.stdout.split()
            if len(values) == 2:
                writer.writerow([now(), pid, *values]); f.flush()
            finished.wait(1)


def run_one(cfg, scenario, smoke=False, pause=False):
    verify_source(cfg)
    actual_date = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y%m%d")
    if not smoke and cfg["date"] != actual_date:
        raise ValueError("Test-plan date differs from actual local run date; bootstrap a fresh workspace")
    pid = owned_pid()
    if not pid:
        raise ValueError("Managed backend missing: run ./scripts/reset_db.sh")
    if not (ROOT / "data/e2e_test_data.csv").exists():
        raise ValueError("Missing verified CSV: reset first")
    if scenario == "Stress":
        dep = json.loads((ROOT / "data/dependencies.json").read_text())
        if hashlib.sha256((ROOT / "scripts/lib/vendor/k6-reporter.js").read_bytes()).hexdigest() != dep["sha256"]:
            raise ValueError("Reporter checksum changed: reinstall/review")
    prefix = f"Smoke_{scenario}" if smoke else scenario
    raw = ROOT / f"raw_logs/{cfg['student_id']}_{prefix}_raw.csv"
    summary = ROOT / f"raw_logs/{prefix}_summary.json"
    manifest = ROOT / f"raw_logs/{prefix}_run.json"
    resource = ROOT / f"evidence/{prefix}_resources.csv"
    if any(p.exists() for p in [raw, summary, manifest, resource]):
        raise ValueError("Run artifacts already exist; archive them/use a fresh workspace instead of overwriting evidence")
    report_dir = ROOT / (f"reports/smoke/{scenario.lower()}" if smoke else f"reports/{scenario.lower()}")
    report_dir.mkdir(parents=True, exist_ok=True)
    names = {"Load": "load_dashboard.html", "Stress": "stress_summary.html", "Spike": "spike_breakdown.html", "Soak": "soak_dashboard.html"}
    report = report_dir / names[scenario]
    script = ROOT / f"scripts/{cfg['student_id']}_{scenario}_{cfg['date']}.js"
    env = dict(os.environ, BASE_URL=cfg["base_url"], SCENARIO_TYPE=scenario, SMOKE="1" if smoke else "0", REPORT_PATH=str(report),
               K6_CSV_TIME_FORMAT="unix_milli", K6_WEB_DASHBOARD="true" if scenario in ("Load", "Soak") else "false",
               K6_WEB_DASHBOARD_PORT="-1", K6_WEB_DASHBOARD_PERIOD="1s",
               K6_WEB_DASHBOARD_EXPORT=str(report) if scenario in ("Load", "Soak") else "")
    command = ["k6", "run", "--out", f"csv={raw}", "--summary-export", str(summary), str(script)]
    print(f"\n{prefix}: arrange Terminal + Activity Monitor in ONE frame; select backend PID {pid}.", flush=True)
    print("Expected previous deployment hostname: Thuys-MacBook-Air; record actual hostname, never substitute it.", flush=True)
    print("Record your Vietnamese narration; capture a screenshot DURING the run. Total unlisted demo >=6 min.", flush=True)
    if pause:
        input("Press Enter when screen/video capture is ready: ")
    lock = ROOT / ".runtime/run.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode()); os.close(fd)
    started = now()
    finished = threading.Event()
    thread = threading.Thread(target=monitor, args=(pid, resource, finished), daemon=True)
    thread.start()
    returncode = -1
    try:
        returncode = subprocess.run(command, cwd=ROOT, env=env).returncode
    finally:
        finished.set(); thread.join(timeout=5)
        data = dict(scenario=scenario, smoke=smoke, started_at=started, ended_at=now(), exit_code=returncode,
                    command=command, base_url=cfg["base_url"], backend_pid=pid, hostname=platform.node(),
                    environment={key: env.get(key) for key in ["PEAK_VUS", "LOAD_VUS", "SOAK_VUS", "SOAK_SECONDS", "THINK_SECONDS", "P95_MS", "ERROR_RATE"]},
                    source_sha256=cfg["source_sha256"], raw_csv_sha256=hashlib.sha256(raw.read_bytes()).hexdigest() if raw.exists() else None,
                    input_csv_sha256=hashlib.sha256((ROOT / "data/e2e_test_data.csv").read_bytes()).hexdigest(),
                    test_plan_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
                    shared_library_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "scripts/lib").glob("*.js")},
                    k6_version=subprocess.check_output(["k6", "version"], text=True).strip(), report=str(report),
                    interpretation="99 = threshold breach; retained as measured failure, not a pass")
        manifest.write_text(json.dumps(data, indent=2) + "\n")
        lock.unlink()
    event("run_finished", scenario=prefix, exit_code=returncode)
    try:
        if raw.exists():
            subprocess.run([sys.executable, str(ROOT / "scripts/analyze_raw.py"), str(raw), "--output-prefix", str(ROOT / f"analysis/{prefix}")], check=True)
        print("REMINDER: attach DURING-run screenshot; write human review; create a separate scoped Git commit.")
    finally:
        if scenario in ("Stress", "Spike"):
            print("Resetting isolated backend after Stress/Spike, including any locked accounts and RAM carts.")
            reset(cfg)
    if not summary.exists() or (not smoke and not report.exists()):
        raise ValueError("Missing report/summary output; inspect k6 errors")
    if smoke and not report.exists():
        print("Smoke is shorter than dashboard aggregation: HTML may be skipped; full Load/Soak still require HTML.")
    return returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ["install", "reset", "stop"]:
        sub.add_parser(name)
    run = sub.add_parser("run")
    run.add_argument("scenario", choices=["Load", "Stress", "Spike", "Soak", "all"])
    run.add_argument("--smoke", action="store_true")
    run.add_argument("--pause-for-evidence", action="store_true")
    args = parser.parse_args()
    try:
        cfg = config()
        if args.action == "install": install(cfg)
        elif args.action == "reset": reset(cfg)
        elif args.action == "stop": stop()
        elif args.scenario == "all":
            if args.smoke: raise ValueError("Smoke individual scenarios to keep evidence labels explicit")
            reset(cfg)
            code = run_one(cfg, "Load", smoke=True, pause=args.pause_for_evidence)
            if code: return code
            exitcode = 0
            for scenario in ["Load", "Stress", "Spike", "Soak"]:
                reset(cfg)
                code = run_one(cfg, scenario, pause=args.pause_for_evidence)
                if code not in (0, 99): return code
                exitcode = max(exitcode, code)
            return exitcode
        else:
            return run_one(cfg, args.scenario, args.smoke, args.pause_for_evidence)
    except (OSError, ValueError, subprocess.CalledProcessError, sqlite3.Error) as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
