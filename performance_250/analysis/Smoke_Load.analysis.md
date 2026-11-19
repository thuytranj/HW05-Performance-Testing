# Raw CSV analysis

Source: `/Users/thuytran/Workspace/HW05-Performance-Testing/performance_250/raw_logs/23120367_Smoke_Load_raw.csv`
SHA256: `d307abad1c53cb7a0f290d6f87e800b7c42033852c92e8b12f0531da3621d5b3`
Window: 0.022 seconds. Type-7 linear quantiles; ms; RPS uses declared common measurement window; error rates are fractions

| Scope | Samples | min_ms | avg_ms | med_ms | p90_ms | p95_ms | p99_ms | max_ms | rps | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HTTP overall (request-weighted) | 5 | 0.680000 | 2.886800 | 1.852000 | 6.297800 | 7.761400 | 8.932280 | 9.225000 | 227.272727 | 0.000000 |
| cart | 1 | 1.907000 | 1.907000 | 1.907000 | 1.907000 | 1.907000 | 1.907000 | 1.907000 | 45.454545 | 0.000000 |
| checkout | 1 | 1.852000 | 1.852000 | 1.852000 | 1.852000 | 1.852000 | 1.852000 | 1.852000 | 45.454545 | 0.000000 |
| detail | 1 | 0.770000 | 0.770000 | 0.770000 | 0.770000 | 0.770000 | 0.770000 | 0.770000 | 45.454545 | 0.000000 |
| login | 1 | 9.225000 | 9.225000 | 9.225000 | 9.225000 | 9.225000 | 9.225000 | 9.225000 | 45.454545 | 0.000000 |
| search | 1 | 0.680000 | 0.680000 | 0.680000 | 0.680000 | 0.680000 | 0.680000 | 0.680000 | 45.454545 | 0.000000 |

## End-to-end flow

```json
{
  "samples": 1,
  "min_ms": 19.0,
  "avg_ms": 19.0,
  "med_ms": 19.0,
  "p90_ms": 19.0,
  "p95_ms": 19.0,
  "p99_ms": 19.0,
  "max_ms": 19.0,
  "attempts": 1,
  "completed": 1,
  "observed_outcomes": 1,
  "boundary_observations_mismatch": false,
  "interrupted_attempts": 0,
  "attempts_per_second": 45.45454545454546,
  "completed_per_second": 45.45454545454546,
  "error_rate": 0.0
}
```

Flow duration includes inter-step think-time, excludes trailing pacing; failed attempts are included.
Completed/s is successful checkout throughput, not HTTP RPS. Interrupted attempts have no final latency/outcome.
Percentiles are computed from individual samples, never by averaging endpoint percentiles.
Low sample counts limit percentile interpretation; thresholds remain hypotheses until measured.
