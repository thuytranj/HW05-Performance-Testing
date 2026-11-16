#!/usr/bin/env python3
"""Summarize real backend ps resource samples; no inference that a memory leak exists."""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    with args.csv.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        parser.exit(1, "No real backend resource samples\n")
    rss = [float(r["rss_kib"]) for r in rows]
    cpu = [float(r["cpu_percent"]) for r in rows]
    duration = (datetime.fromisoformat(rows[-1]["timestamp_utc"]) - datetime.fromisoformat(rows[0]["timestamp_utc"])).total_seconds()
    result = dict(source=str(args.csv.resolve()), samples=len(rows), sample_span_seconds=duration,
                  peak_rss_mib=max(rss) / 1024, first_rss_mib=rss[0] / 1024, last_rss_mib=rss[-1] / 1024,
                  net_rss_change_mib=(rss[-1] - rss[0]) / 1024, max_ps_cpu_percent=max(cpu),
                  interpretation="ps CPU is platform process average, RSS is sampled resident memory; growth alone does not prove a leak")
    target = args.csv.with_suffix(".analysis.json")
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
