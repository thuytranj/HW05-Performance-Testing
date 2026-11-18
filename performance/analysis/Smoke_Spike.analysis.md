# Raw CSV analysis

Source: `/Users/thuytran/Workspace/HW05-Performance-Testing/performance/raw_logs/23120367_Smoke_Spike_raw.csv`
SHA256: `7548a7dcbcc35ab291f39f776b5ec64ba0c521e6cd0279116cae194c0940bc52`
Window: 0.084 seconds. Type-7 linear quantiles; ms; RPS uses declared common measurement window; error rates are fractions

| Scope | Samples | min_ms | avg_ms | med_ms | p90_ms | p95_ms | p99_ms | max_ms | rps | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HTTP overall (request-weighted) | 5 | 1.030000 | 14.974400 | 1.848000 | 41.980600 | 55.230800 | 65.830960 | 68.481000 | 59.523810 | 0.000000 |
| cart | 1 | 1.848000 | 1.848000 | 1.848000 | 1.848000 | 1.848000 | 1.848000 | 1.848000 | 11.904762 | 0.000000 |
| checkout | 1 | 2.230000 | 2.230000 | 2.230000 | 2.230000 | 2.230000 | 2.230000 | 2.230000 | 11.904762 | 0.000000 |
| detail | 1 | 1.283000 | 1.283000 | 1.283000 | 1.283000 | 1.283000 | 1.283000 | 1.283000 | 11.904762 | 0.000000 |
| login | 1 | 68.481000 | 68.481000 | 68.481000 | 68.481000 | 68.481000 | 68.481000 | 68.481000 | 11.904762 | 0.000000 |
| search | 1 | 1.030000 | 1.030000 | 1.030000 | 1.030000 | 1.030000 | 1.030000 | 1.030000 | 11.904762 | 0.000000 |

## End-to-end flow

```json
{
  "samples": 1,
  "min_ms": 82.0,
  "avg_ms": 82.0,
  "med_ms": 82.0,
  "p90_ms": 82.0,
  "p95_ms": 82.0,
  "p99_ms": 82.0,
  "max_ms": 82.0,
  "attempts": 1,
  "completed": 1,
  "observed_outcomes": 1,
  "boundary_observations_mismatch": false,
  "interrupted_attempts": 0,
  "attempts_per_second": 11.904761904761903,
  "completed_per_second": 11.904761904761903,
  "error_rate": 0.0
}
```

Flow duration includes inter-step think-time, excludes trailing pacing; failed attempts are included.
Completed/s is successful checkout throughput, not HTTP RPS. Interrupted attempts have no final latency/outcome.
Percentiles are computed from individual samples, never by averaging endpoint percentiles.
Low sample counts limit percentile interpretation; thresholds remain hypotheses until measured.
