"""Synthetic fixtures for validating helpers, not submission evidence."""
import csv
import importlib.util
import tempfile
import shutil
from unittest.mock import patch
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw = Path(self.tmp.name) / "synthetic.csv"
        self.tool = load("analysis", SKILL / "assets/workspace/scripts/analyze_raw.py")

    def write(self, rows):
        with self.raw.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["metric_name", "timestamp", "metric_value", "name", "status", "group", "extra_tags"])
            writer.writeheader()
            for metric, value, endpoint, status in rows:
                writer.writerow(dict(metric_name=metric, timestamp="1000", metric_value=value,
                                     name=endpoint, status=status, group="::login", extra_tags=""))

    def test_percentiles_rates_and_flow_are_distinct(self):
        rows = [("run_start_ms", 1000000, "", ""), ("run_end_ms", 1010000, "", "")]
        for latency, status in [(10, 200), (20, 200), (30, 200), (40, 500)]:
            rows += [("http_req_duration", latency, "login", status), ("http_reqs", 1, "login", status),
                     ("http_req_failed", int(status == 500), "login", status)]
        rows += [("flow_duration_ms", 900, "", ""), ("flow_duration_ms", 1100, "", ""),
                 ("flow_attempts", 2, "", ""), ("flow_success", 1, "", ""), ("flow_success", 0, "", ""),
                 ("flow_completed", 1, "", "")]
        self.write(rows)
        result = self.tool.analyze(self.raw)
        overall = result["http_overall"]
        self.assertAlmostEqual(overall["p95_ms"], 38.5)
        self.assertAlmostEqual(overall["p99_ms"], 39.7)
        self.assertEqual(overall["med_ms"], 25)
        self.assertEqual(overall["rps"], 0.4)
        self.assertEqual(overall["error_rate"], 0.25)
        self.assertEqual(result["flow"]["avg_ms"], 1000)
        self.assertEqual(result["flow"]["error_rate"], 0.5)
        self.assertEqual(result["flow"]["completed_per_second"], 0.1)
        self.assertEqual(overall["status_counts"], {"200": 3, "500": 1})

    def test_missing_window_cannot_invent_rps(self):
        self.write([("http_req_duration", 4, "login", 200), ("http_reqs", 1, "login", 200), ("http_req_failed", 0, "login", 200)])
        with self.assertRaisesRegex(ValueError, "window"):
            self.tool.analyze(self.raw)

    def test_summary_json_is_not_raw_csv(self):
        self.raw.write_text('{"metrics":{}}')
        with self.assertRaisesRegex(ValueError, "CSV"):
            self.tool.analyze(self.raw)

    def test_mismatched_metrics_rejected(self):
        self.write([("run_start_ms", 0, "", ""), ("run_end_ms", 1000, "", ""),
                    ("http_req_duration", 20, "login", 200), ("http_reqs", 2, "login", 200), ("http_req_failed", 0, "login", 200)])
        with self.assertRaisesRegex(ValueError, "count"):
            self.tool.analyze(self.raw)

    def test_http_only_log_cannot_prove_e2e(self):
        self.write([("run_start_ms", 0, "", ""), ("run_end_ms", 1000, "", ""),
                    ("http_req_duration", 20, "login", 200), ("http_reqs", 1, "login", 200), ("http_req_failed", 0, "login", 200)])
        with self.assertRaisesRegex(ValueError, "flow"):
            self.tool.analyze(self.raw)

    def test_time_window_uses_common_duration(self):
        origin = 1700000000000
        values = [("run_start_ms", origin, origin, "", ""), ("run_end_ms", origin + 10000, origin + 10000, "", "")]
        for offset, latency in [(1000, 100), (7000, 300)]:
            for name, value in [("http_req_duration", latency), ("http_reqs", 1), ("http_req_failed", 0),
                                ("flow_attempts", 1), ("flow_completed", 1), ("flow_success", 1), ("flow_duration_ms", 500)]:
                values.append((name, origin + offset, value, "login" if name.startswith("http_") else "", 200))
        with self.raw.open("w", newline="") as f:
            writer = csv.writer(f); writer.writerow(["metric_name", "timestamp", "metric_value", "name", "status"])
            writer.writerows(values)
        result = self.tool.analyze(self.raw, from_seconds=0, to_seconds=5)
        self.assertEqual(result["http_overall"]["samples"], 1)
        self.assertEqual(result["http_overall"]["rps"], .2)
        self.assertEqual(result["flow"]["completed_per_second"], .2)


class AuditTests(unittest.TestCase):
    def test_new_interaction_preserves_existing_human_review(self):
        tool = load("audit", SKILL / "assets/workspace/scripts/record_audit.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "audit").mkdir()
            report = root / "audit/ai-audit.md"
            report.write_text("# Prior interaction\nHuman correction: distinguish ms and s.\n")
            prompt, output = root / "prompt.txt", root / "output.txt"
            prompt.write_text("Synthetic test prompt"); output.write_text("Synthetic test output")
            args = ["audit", "--tool", "unit-test", "--at", "2026-11-16T10:00:00+07:00", "--prompt", str(prompt), "--output", str(output)]
            with patch.object(tool, "ROOT", root), patch("sys.argv", args):
                tool.main()
            self.assertIn("Human correction: distinguish ms and s.", report.read_text())
            self.assertIn("Synthetic test output", report.read_text())
            self.assertIn("### Final AI response", report.read_text())
            self.assertFalse((root / "audit/interactions").exists())
            self.assertFalse((root / "audit/interactions.jsonl").exists())


class DiscoveryTests(unittest.TestCase):
    def test_source_identifies_lockout_and_absent_stock(self):
        tool = load("bootstrap", SKILL / "scripts/bootstrap.py")
        result = tool.discover(Path.cwd())
        self.assertEqual(result["port"], 3000)
        self.assertEqual(result["lockout"]["increment"], 2)
        self.assertEqual(result["lockout"]["effective_wrong_attempts"], 2)
        self.assertFalse(result["stock_columns"])
        self.assertTrue(result["startup_reseeds"])
        self.assertEqual(len(result["endpoints"]), 5)

    def test_external_database_path_is_not_executed(self):
        tool = load("bootstrap", SKILL / "scripts/bootstrap.py")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "backend").mkdir()
            for name in ["server.js", "database.js", "package.json", "package-lock.json"]:
                shutil.copy2(Path.cwd() / "backend" / name, project / "backend" / name)
            path = project / "backend/database.js"
            path.write_text(path.read_text().replace("path.resolve(__dirname, 'database.sqlite')", "'/external/database.sqlite'"))
            with self.assertRaisesRegex(ValueError, "database path"):
                tool.discover(project)


if __name__ == "__main__":
    unittest.main()
