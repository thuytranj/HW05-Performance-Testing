# Raw CSV analysis

Source: `/Users/thuytran/Workspace/HW05-Performance-Testing/performance_250/raw_logs/23120367_Spike_raw.csv`
SHA256: `1c89c7a4cf73814ef1d3092447e30681e5bcbd4558f47b72c052368d0c6212cc`
Window: 135.780 seconds. Type-7 linear quantiles; ms; RPS uses declared common measurement window; error rates are fractions

| Scope | Samples | min_ms | avg_ms | med_ms | p90_ms | p95_ms | p99_ms | max_ms | rps | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HTTP overall (request-weighted) | 9185 | 0.320000 | 3.246591 | 2.531000 | 6.266600 | 7.900800 | 11.780280 | 47.968000 | 67.646192 | 0.000000 |
| cart | 1837 | 0.548000 | 2.649864 | 2.267000 | 4.489200 | 5.200600 | 7.023280 | 14.096000 | 13.529238 | 0.000000 |
| checkout | 1837 | 1.478000 | 5.279707 | 4.651000 | 8.518400 | 9.802400 | 14.993800 | 43.014000 | 13.529238 | 0.000000 |
| detail | 1837 | 0.330000 | 2.478458 | 1.704000 | 5.175800 | 6.925200 | 11.356160 | 45.565000 | 13.529238 | 0.000000 |
| login | 1837 | 0.701000 | 3.464375 | 2.715000 | 5.979600 | 7.587000 | 12.230000 | 47.968000 | 13.529238 | 0.000000 |
| search | 1837 | 0.320000 | 2.360550 | 1.672000 | 4.766400 | 6.270000 | 9.940240 | 34.259000 | 13.529238 | 0.000000 |

## End-to-end flow

```json
{
  "samples": 1837,
  "min_ms": 2366.0,
  "avg_ms": 4033.165487207403,
  "med_ms": 4038.0,
  "p90_ms": 4776.4,
  "p95_ms": 4957.999999999999,
  "p99_ms": 5329.639999999999,
  "max_ms": 5733.0,
  "attempts": 1837,
  "completed": 1837,
  "observed_outcomes": 1837,
  "boundary_observations_mismatch": false,
  "interrupted_attempts": 0,
  "attempts_per_second": 13.529238474002062,
  "completed_per_second": 13.529238474002062,
  "error_rate": 0.0
}
```

Flow duration includes inter-step think-time, excludes trailing pacing; failed attempts are included.
Completed/s is successful checkout throughput, not HTTP RPS. Interrupted attempts have no final latency/outcome.
Percentiles are computed from individual samples, never by averaging endpoint percentiles.
Low sample counts limit percentile interpretation; thresholds remain hypotheses until measured.
