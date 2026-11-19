#!/usr/bin/env python3
"""Presence/structure preflight; never certifies screenshots, narration or human review."""
import csv
import json
import re
import sys
from pathlib import Path
from analyze_raw import analyze

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / "perf.config.json").read_text())
    missing = []
    def require(relative):
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(relative)
            return False
        return True
    for path in ["README.md", "reports/main-report.md", "reports/main-report.pdf", "audit/ai-audit.md", "audit/ai-audit.pdf",
                 "audit/ai-critique.md", "audit/ai-critique.pdf", "evidence/git-log.txt", "evidence/hardware.txt",
                 "evidence/hardware.png", "analysis/ai-verification.md", "reports/continuous-performance.md", "evidence/links.json"]:
        require(path)
    csvpath = ROOT / "data/e2e_test_data.csv"
    if require("data/e2e_test_data.csv"):
        with csvpath.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if len(rows) < 40 or len({r.get("email") for r in rows}) != len(rows):
            missing.append("CSV needs >=40 unique independent accounts")
    for scenario, report in [("Load", "load/load_dashboard.html"), ("Stress", "stress/stress_summary.html"), ("Spike", "spike/spike_breakdown.html"), ("Soak", "soak/soak_dashboard.html")]:
        require(f"scripts/{cfg['student_id']}_{scenario}_{cfg['date']}.js")
        raw = f"raw_logs/{cfg['student_id']}_{scenario}_raw.csv"
        if require(raw):
            try:
                result = analyze(ROOT / raw)
                if not {"login", "search", "detail", "cart", "checkout"}.issubset(result["endpoints"]):
                    missing.append(f"{raw}: missing one or more E2E endpoints")
                if scenario == "Soak" and result["window_seconds"] < 600:
                    missing.append("Actual Soak measurement window shorter than600 seconds")
            except ValueError as exc: missing.append(f"{raw}: {exc}")
        require(f"raw_logs/{scenario}_summary.json")
        run = f"raw_logs/{scenario}_run.json"
        if require(run):
            data = json.loads((ROOT / run).read_text())
            if data.get("smoke") or data.get("exit_code") not in (0, 99):
                missing.append(f"{run}: incomplete run or smoke cannot replace scenario evidence")
            if scenario == "Soak":
                settings = data.get("environment", {})
                seconds = int(settings.get("SOAK_SECONDS") or 600)
                if not 600 <= seconds <= 900: missing.append("Soak sustained duration must be 600..900 seconds")
        require(f"reports/{report}")
        require(f"evidence/{scenario}_resources.csv")
        require(f"evidence/{scenario}_screen.png")
    critique = ROOT / "audit/ai-critique.md"
    if critique.exists():
        # Count prose only; headings excluded. Human must verify intended language word count.
        prose = " ".join(x for x in critique.read_text().splitlines() if not x.startswith("#"))
        words = len(prose.split())
        if not 200 <= words <= 300: missing.append(f"AI Critique word count: {words}; required 200..300")
    links = ROOT / "evidence/links.json"
    if links.exists():
        data = json.loads(links.read_text())
        if not re.match(r"https://github.com/[^/]+/[^/]+", data.get("public_repository", "")):
            missing.append("Public repository URL")
        if not data.get("demo_youtube") or float(data.get("demo_total_seconds", 0)) < 360:
            missing.append("Unlisted YouTube demo >=360 seconds")
        if not data.get("skill_demo_youtube"): missing.append("Skill end-to-end demonstration URL")
        if not data.get("k6_raw_format_confirmation"): missing.append("Confirm with TA: native k6 CSV accepted in place of literal .jtl")
    for item in missing: print(f"MISSING/INVALID: {item}")
    print("MANUAL REVIEW: complete audit history; actual 200–300-word critique; human corrections; screenshots tool+backend monitor in one frame;")
    print("own Vietnamese voice; unlisted video visibility; >=6 minutes; skill demonstration; hostname matches previous deployments;")
    print("workflow unique in group; public repo accessible; genuine GitHub Issues/screenshots if found; no fabricated AI errors/evidence;")
    print("PDF visual QA; measured stable threshold with RPS+RAM; baseline and false alarms in proposal; final ZIP contents and Moodle deadline.")
    print("Self-assessment: Load30 + Stress20 + Spike20 + AI10 + Continuous10 + Skill10 =100.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
