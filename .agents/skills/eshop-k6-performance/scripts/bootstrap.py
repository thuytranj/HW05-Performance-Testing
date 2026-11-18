#!/usr/bin/env python3
"""Discover this EShop revision and materialize an isolated HW05 workspace."""
import argparse
import hashlib
import json
import math
import re
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SKILL = Path(__file__).resolve().parents[1]


def discover(project):
    project = Path(project).resolve()
    server_path, database_path = project / "backend/server.js", project / "backend/database.js"
    server, database = server_path.read_text(), database_path.read_text()
    if not re.search(r"const dbPath\s*=\s*path\.resolve\(__dirname,\s*['\"]database\.sqlite['\"]\)\s*;", database):
        raise ValueError("Unsupported database path: isolation requires database.sqlite relative to copied __dirname")
    if len(re.findall(r"new sqlite3\.Database\(", database)) != 1 or not re.search(r"new sqlite3\.Database\(dbPath,", database):
        raise ValueError("Unsupported database connection: verify isolated path before executing destructive seed")
    port = re.search(r"const PORT\s*=\s*(\d+)\s*;", server)
    increment = re.search(r"user\.login_attempts\s*\+\s*(\d+)", server)
    threshold = re.search(r"newAttempts\s*>=\s*(\d+)", server)
    duration = re.search(r"Date\.now\(\)\s*\+\s*(\d+)", server)
    required = [('POST', '/api/login'), ('GET', '/api/products'), ('GET', '/api/products/:id'),
                ('POST', '/api/cart'), ('POST', '/api/checkout')]
    endpoints = []
    for method, uri in required:
        match = re.search(r'app\.' + method.lower() + r'\("' + re.escape(uri) + r'"', server)
        if not match:
            raise ValueError(f"Unsupported API revision: cannot verify {method} {uri}; review routes/controllers/schemas before adapting")
        endpoints.append(dict(method=method, uri=uri, source=f"backend/server.js:{server[:match.start()].count(chr(10)) + 1}"))
    checks = ['const { email, password } = req.body', 'const { total_amount, shipping_address } = req.body',
              'const searchQuery = req.query.search', 'userCarts[userId].push(req.body)',
              'res.json({ message: "Login successful", token, user })', 'orderId: this.lastID',
              'authHeader.split(" ")[1]', 'const userCarts = {}']
    if not all(x in server for x in checks) or not all([port, increment, threshold, duration]):
        raise ValueError("Unsupported API/body/auth/lockout revision; inspect source and update adapter, do not guess")
    product_schema = re.search(r"CREATE TABLE products\s*\((.*?)\)`", database, re.S)
    if not product_schema:
        raise ValueError("Cannot locate products schema")
    stock = re.findall(r"\b(stock\w*|inventory\w*)\b", product_schema.group(1), re.I)
    if stock:
        raise ValueError("Stock schema changed: implement and verify stock restore before running")
    return {"project": str(project), "port": int(port.group(1)), "base_url": f"http://127.0.0.1:{port.group(1)}",
            "endpoints": endpoints, "auth": {"response_field": "token", "transport": "Authorization: Bearer <token>", "cookie": False},
            "request_bodies": {"login": ["email", "password"], "cart": ["id", "name", "price", "quantity"],
                               "checkout": ["total_amount", "shipping_address"]},
            "lockout": {"increment": int(increment.group(1)), "threshold": int(threshold.group(1)),
                        "effective_wrong_attempts": math.ceil(int(threshold.group(1)) / int(increment.group(1))),
                        "duration_ms": int(duration.group(1))},
            "stock_columns": stock, "startup_reseeds": "DROP TABLE IF EXISTS users" in database and "initDatabase();" in database,
            "cart_storage": "process memory; no clear endpoint; checkout does not clear cart",
            "validation": "No separate validation schema for selected routes; cart appends arbitrary JSON; checkout trusts client total",
            "source_sha256": {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [server_path, database_path, project / 'backend/package.json', project / 'backend/package-lock.json']}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("performance"))
    parser.add_argument("--student-id", default="23120367")
    parser.add_argument("--date", help="Actual run date YYYYMMDD, default Asia/Ho_Chi_Minh today")
    parser.add_argument("--port", type=int, help="Isolated backend port, default discovered port")
    parser.add_argument("--accounts", type=int, default=40)
    args = parser.parse_args()
    if not re.fullmatch(r"\d+", args.student_id) or args.accounts < 40:
        parser.error("Student ID must be digits; accounts must be >=40")
    run_date = args.date or datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y%m%d")
    datetime.strptime(run_date, "%Y%m%d")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Output must be empty: archive prior runs or choose a fresh workspace")
    discovery = discover(args.project)
    port = args.port or discovery["port"]
    if not 1024 <= port <= 65535:
        parser.error("Choose a port in 1024..65535")
    shutil.copytree(SKILL / "assets/workspace", output, dirs_exist_ok=True)
    for directory in ["data", "raw_logs", "reports/load", "reports/stress", "reports/spike", "reports/soak", "evidence", "audit", "analysis", ".runtime/backend"]:
        (output / directory).mkdir(parents=True, exist_ok=True)
    metadata = dict(student_id=args.student_id, date=run_date, accounts=args.accounts, port=port,
                    base_url=f"http://127.0.0.1:{port}", project=str(args.project.resolve()), source_sha256=discovery["source_sha256"])
    (output / "perf.config.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (output / "data/api_discovery.json").write_text(json.dumps(discovery, indent=2, ensure_ascii=False) + "\n")
    (output / "reports/api_discovery.md").write_text(
        "# API Discovery\n\nSource-derived snapshot; re-discover after source changes.\n\n```json\n" +
        json.dumps(discovery, indent=2, ensure_ascii=False) + "\n```\n\n"
        "## Human review\n- [ ] Confirm workflow does not duplicate group members.\n"
        "- [ ] Compare expected three-fail lockout with effective source behavior.\n"
        "- [ ] Cart payload corroborated with api_specification.md/frontend; backend accepts arbitrary body.\n"
        "- [ ] Distinguish isolated-runtime changes (port/bind only) from SUT fixes.\n"
        "- [ ] SQLite has no inventory column: stock restoration is not applicable.\n")
    for scenario in ["Load", "Stress", "Spike", "Soak"]:
        imports = "import workflow, { makeOptions } from './lib/workflow.js';\n"
        tail = ""
        if scenario in ("Load", "Soak"):
            slug = scenario.lower()
            imports = (f"// Requires Built-in Web Dashboard env (set automatically by ./scripts/run.sh {scenario}):\n"
                       f"// K6_WEB_DASHBOARD=true K6_WEB_DASHBOARD_PORT=-1 K6_WEB_DASHBOARD_EXPORT=reports/{slug}/{slug}_dashboard.html\n"
                       + imports)
        elif scenario == "Stress":
            imports += "import { htmlReport } from './lib/vendor/k6-reporter.js';\nimport { formatConsoleSummary } from './lib/reports.js';\n"
            tail = ("\nexport function handleSummary(data) {\n"
                    "  return {\n"
                    "    stdout: formatConsoleSummary(data, 'EShop Stress'),\n"
                    "    [__ENV.REPORT_PATH || 'reports/stress/stress_summary.html']: htmlReport(data, { title: 'EShop Stress Summary', theme: 'classic' }),\n"
                    "  };\n}\n")
        elif scenario == "Spike":
            imports += "import { spikeReport, formatConsoleSummary } from './lib/reports.js';\n"
            tail = ("\nexport function handleSummary(data) {\n"
                    "  return {\n"
                    "    stdout: formatConsoleSummary(data, 'EShop Spike'),\n"
                    "    [__ENV.REPORT_PATH || 'reports/spike/spike_breakdown.html']: spikeReport(data),\n"
                    "  };\n}\n")
        text = (f"// Generated for HW05 on {datetime.now().astimezone().isoformat()}\n" + imports +
                f"export const options = makeOptions('{scenario}');\n" +
                "export { setup, teardown } from './lib/workflow.js';\nexport default workflow;\n" + tail)
        (output / f"scripts/{args.student_id}_{scenario}_{run_date}.js").write_text(text)
    for path in (output / "scripts").glob("*.sh"):
        path.chmod(0o755)
    (output / ".gitignore").write_text(".runtime/\nscripts/lib/vendor/\n__pycache__/\n")
    print(f"Workspace: {output}\nDiscovery: reports/api_discovery.md\nNext: cd {output}\npython3 scripts/perf.py install\n./scripts/reset_db.sh")


if __name__ == "__main__":
    main()
