# Raw CSV analysis

Source: `/Users/thuytran/Workspace/HW05-Performance-Testing/performance/raw_logs/23120367_Smoke_Load_raw.csv`
SHA256: `6593cea9380fb93e7e05f515a1d340b71b733d9dfdcdc7f5319ffa5d14cb48d0`
Window: 0.018 seconds. Type-7 linear quantiles; ms; RPS uses declared common measurement window; error rates are fractions

| Scope | Samples | min_ms | avg_ms | med_ms | p90_ms | p95_ms | p99_ms | max_ms | rps | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HTTP overall (request-weighted) | 5 | 0.733000 | 2.948600 | 1.533000 | 6.660400 | 8.263200 | 9.545440 | 9.866000 | 277.777778 | 0.000000 |
| cart | 1 | 1.533000 | 1.533000 | 1.533000 | 1.533000 | 1.533000 | 1.533000 | 1.533000 | 55.555556 | 0.000000 |
| checkout | 1 | 1.852000 | 1.852000 | 1.852000 | 1.852000 | 1.852000 | 1.852000 | 1.852000 | 55.555556 | 0.000000 |
| detail | 1 | 0.733000 | 0.733000 | 0.733000 | 0.733000 | 0.733000 | 0.733000 | 0.733000 | 55.555556 | 0.000000 |
| login | 1 | 9.866000 | 9.866000 | 9.866000 | 9.866000 | 9.866000 | 9.866000 | 9.866000 | 55.555556 | 0.000000 |
| search | 1 | 0.759000 | 0.759000 | 0.759000 | 0.759000 | 0.759000 | 0.759000 | 0.759000 | 55.555556 | 0.000000 |

## End-to-end flow

```json
{
  "samples": 1,
  "min_ms": 17.0,
  "avg_ms": 17.0,
  "med_ms": 17.0,
  "p90_ms": 17.0,
  "p95_ms": 17.0,
  "p99_ms": 17.0,
  "max_ms": 17.0,
  "attempts": 1,
  "completed": 1,
  "observed_outcomes": 1,
  "boundary_observations_mismatch": false,
  "interrupted_attempts": 0,
  "attempts_per_second": 55.55555555555556,
  "completed_per_second": 55.55555555555556,
  "error_rate": 0.0
}
```

Flow duration includes inter-step think-time, excludes trailing pacing; failed attempts are included.
Completed/s is successful checkout throughput, not HTTP RPS. Interrupted attempts have no final latency/outcome.
Percentiles are computed from individual samples, never by averaging endpoint percentiles.
Low sample counts limit percentile interpretation; thresholds remain hypotheses until measured.
