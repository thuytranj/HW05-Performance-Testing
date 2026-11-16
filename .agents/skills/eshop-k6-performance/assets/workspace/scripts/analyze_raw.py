#!/usr/bin/env python3
"""Analyze granular k6 CSV only; stdlib, exact Type-7 quantiles, explicit window."""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def quantile(sorted_values, q):
    if not sorted_values:
        return None
    position = (len(sorted_values) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (position - low)


def stats(values):
    values = sorted(values)
    if not values:
        return {"samples": 0}
    return {"samples": len(values), "min_ms": values[0], "avg_ms": math.fsum(values) / len(values),
            "med_ms": quantile(values, .5), "p90_ms": quantile(values, .9),
            "p95_ms": quantile(values, .95), "p99_ms": quantile(values, .99), "max_ms": values[-1]}


def analyze(path, duration=None, from_seconds=None, to_seconds=None):
    path = Path(path)
    selected_window = None
    if from_seconds is not None or to_seconds is not None:
        if duration is not None or from_seconds is None or to_seconds is None or not 0 <= from_seconds < to_seconds:
            raise ValueError("Window filtering requires both offsets 0<=from<to and no duration override")
        with path.open(encoding="utf-8-sig", newline="") as f:
            anchors = [(row["metric_name"], float(row["metric_value"])) for row in csv.DictReader(f)
                       if row.get("metric_name") in ("run_start_ms", "run_end_ms")]
        starts = [v for name, v in anchors if name == "run_start_ms"]
        ends = [v for name, v in anchors if name == "run_end_ms"]
        if not starts or not ends:
            raise ValueError("Missing measurement window gauges for offset filtering")
        origin = min(starts)
        if origin + to_seconds * 1000 > max(ends):
            raise ValueError("Requested window extends past actual run end")
        selected_window = (origin + from_seconds * 1000, origin + to_seconds * 1000)
        duration = to_seconds - from_seconds
    metrics = defaultdict(list)
    endpoints = defaultdict(lambda: defaultdict(list))
    status_counts = Counter()
    rows = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not {"metric_name", "metric_value", "timestamp"}.issubset(reader.fieldnames or []):
            raise ValueError("Expected granular k6 CSV; summary JSON is not raw evidence")
        for line, row in enumerate(reader, 2):
            rows += 1
            metric = row.get("metric_name")
            if selected_window:
                try:
                    timestamp = float(row["timestamp"])
                except (ValueError, TypeError) as exc:
                    raise ValueError("Window filtering requires numeric unix_milli timestamps from runner") from exc
                if timestamp < 100000000000:
                    raise ValueError("Window filtering requires K6_CSV_TIME_FORMAT=unix_milli")
                if not selected_window[0] <= timestamp < selected_window[1]:
                    continue
            try:
                value = float(row["metric_value"])
                if not math.isfinite(value):
                    raise ValueError("non-finite")
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"Invalid CSV value at line {line}") from exc
            if metric in {"http_req_duration", "http_req_failed", "http_reqs", "flow_duration_ms", "flow_success",
                          "flow_completed", "flow_attempts", "run_start_ms", "run_end_ms"}:
                metrics[metric].append(value)
            if metric in {"http_req_duration", "http_req_failed", "http_reqs"}:
                endpoint = row.get("name") or row.get("url") or "unlabelled"
                endpoints[endpoint][metric].append(value)
                if metric == "http_reqs":
                    status_counts[row.get("status") or "0"] += int(value)
                    endpoints[endpoint]["statuses"].append((row.get("status") or "0", int(value)))

    if duration is None:
        if not metrics["run_start_ms"] or not metrics["run_end_ms"]:
            raise ValueError("Missing measurement window: provide run_start_ms/run_end_ms or --duration-seconds")
        duration = (max(metrics["run_end_ms"]) - min(metrics["run_start_ms"])) / 1000
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Measurement window must be positive seconds")
    if not metrics["http_req_duration"]:
        raise ValueError("No HTTP duration samples; empty/non-HTTP log cannot establish performance")

    def http_result(bucket):
        n = len(bucket["http_req_duration"])
        count = math.fsum(bucket["http_reqs"])
        failures = bucket["http_req_failed"]
        if n != count or n != len(failures):
            raise ValueError(f"HTTP metric count mismatch: durations={n}, requests={count}, failure samples={len(failures)}")
        if any(x not in (0, 1) for x in failures):
            raise ValueError("http_req_failed must contain 0/1 observations")
        return dict(stats(bucket["http_req_duration"]), requests=int(count), rps=count / duration,
                    error_rate=math.fsum(failures) / n)

    overall = http_result(metrics)
    overall["status_counts"] = dict(sorted(status_counts.items()))
    per_endpoint = {}
    for endpoint, bucket in sorted(endpoints.items()):
        item = http_result(bucket)
        counts = Counter()
        for code, count in bucket["statuses"]:
            counts[code] += count
        item["status_counts"] = dict(sorted(counts.items()))
        per_endpoint[endpoint] = item
    for key in ["flow_attempts", "flow_completed", "flow_success", "flow_duration_ms"]:
        if not selected_window and not metrics[key]:
            raise ValueError(f"Missing flow metric {key}: HTTP samples alone cannot establish E2E evidence")
    for key in ["flow_attempts", "flow_completed"]:
        if any(x < 0 or not x.is_integer() for x in metrics[key]):
            raise ValueError(f"Invalid flow counter {key}")
    if any(x not in (0, 1) for x in metrics["flow_success"]):
        raise ValueError("flow_success requires 0/1 observations")
    flow = stats(metrics["flow_duration_ms"])
    attempts = math.fsum(metrics["flow_attempts"])
    completed = math.fsum(metrics["flow_completed"])
    observed = len(metrics["flow_success"])
    outcome_mismatch = len(metrics["flow_duration_ms"]) != observed or completed != math.fsum(metrics["flow_success"])
    if not selected_window and (outcome_mismatch or attempts < observed):
        raise ValueError("Inconsistent flow counts: duration/outcome/completion/attempt evidence does not agree")
    flow.update(attempts=int(attempts), completed=int(completed), observed_outcomes=observed,
                boundary_observations_mismatch=bool(selected_window and outcome_mismatch),
                interrupted_attempts=None if selected_window else max(0, int(attempts) - observed), attempts_per_second=attempts / duration,
                completed_per_second=completed / duration,
                error_rate=(observed - math.fsum(metrics["flow_success"])) / observed if observed else None)
    return {"source": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "csv_rows": rows, "window_seconds": duration, "window_offsets_seconds": [from_seconds, to_seconds] if selected_window else None,
            "method": "Type-7 linear quantiles; ms; RPS uses declared common measurement window; error rates are fractions",
            "http_overall": overall, "endpoints": per_endpoint, "flow": flow}


def markdown(result):
    columns = ["min_ms", "avg_ms", "med_ms", "p90_ms", "p95_ms", "p99_ms", "max_ms", "rps", "error_rate"]
    output = ["# Raw CSV analysis", "", f"Source: `{result['source']}`", f"SHA256: `{result['sha256']}`",
              f"Window: {result['window_seconds']:.3f} seconds. {result['method']}", "",
              "| Scope | Samples | " + " | ".join(columns) + " |", "|---|---:" + "|---:" * len(columns) + "|"]
    for name, item in [("HTTP overall (request-weighted)", result["http_overall"]), *result["endpoints"].items()]:
        output.append(f"| {name} | {item['samples']} | " + " | ".join(f"{item[x]:.6f}" for x in columns) + " |")
    output += ["", "## End-to-end flow", "", "```json", json.dumps(result["flow"], indent=2), "```", "",
               "Flow duration includes inter-step think-time, excludes trailing pacing; failed attempts are included.",
               "Completed/s is successful checkout throughput, not HTTP RPS. Interrupted attempts have no final latency/outcome.",
               "Percentiles are computed from individual samples, never by averaging endpoint percentiles.",
               "Low sample counts limit percentile interpretation; thresholds remain hypotheses until measured."]
    return "\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--duration-seconds", type=float, help="Only when raw log lacks window gauges; document source of duration")
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--from-seconds", type=float, help="Window start offset from setup gauge (inclusive)")
    parser.add_argument("--to-seconds", type=float, help="Window end offset from setup gauge (exclusive)")
    args = parser.parse_args()
    try:
        result = analyze(args.csv, args.duration_seconds, args.from_seconds, args.to_seconds)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Analysis refused: {exc}\n")
    prefix = args.output_prefix or args.csv.with_suffix("")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    prefix.with_suffix(".analysis.md").write_text(markdown(result))
    print(f"Analysis: {prefix}.analysis.json / .analysis.md")


if __name__ == "__main__":
    main()
