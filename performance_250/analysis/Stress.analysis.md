# Raw CSV analysis

Source: `/Users/thuytran/Workspace/HW05-Performance-Testing/performance_250/raw_logs/23120367_Stress_raw.csv`
SHA256: `43283b655b6172410c6f5637e794e5d6bd81e57212964dd9b7eabb8cb1fa9878`
Window: 272.895 seconds. Type-7 linear quantiles; ms; RPS uses declared common measurement window; error rates are fractions

| Scope | Samples | min_ms | avg_ms | med_ms | p90_ms | p95_ms | p99_ms | max_ms | rps | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HTTP overall (request-weighted) | 44360 | 0.226000 | 3.562663 | 2.868000 | 6.956000 | 8.556100 | 12.379410 | 40.729000 | 162.553363 | 0.000000 |
| cart | 8872 | 0.435000 | 2.781846 | 2.448000 | 4.512800 | 5.310450 | 7.278120 | 32.188000 | 32.510673 | 0.000000 |
| checkout | 8872 | 1.095000 | 5.786240 | 5.208000 | 9.112900 | 10.624400 | 14.311740 | 40.729000 | 32.510673 | 0.000000 |
| detail | 8872 | 0.226000 | 2.562144 | 1.735000 | 5.550100 | 7.212700 | 11.184640 | 32.153000 | 32.510673 | 0.000000 |
| login | 8872 | 0.553000 | 4.175646 | 3.460000 | 7.351500 | 9.114400 | 13.010730 | 37.682000 | 32.510673 | 0.000000 |
| search | 8872 | 0.230000 | 2.507440 | 1.735500 | 5.296900 | 6.947950 | 10.906120 | 35.302000 | 32.510673 | 0.000000 |

## End-to-end flow

```json
{
  "samples": 8872,
  "min_ms": 2269.0,
  "avg_ms": 4022.6522768259692,
  "med_ms": 4023.0,
  "p90_ms": 4777.900000000001,
  "p95_ms": 4969.0,
  "p99_ms": 5309.579999999998,
  "max_ms": 5916.0,
  "attempts": 8872,
  "completed": 8872,
  "observed_outcomes": 8872,
  "boundary_observations_mismatch": false,
  "interrupted_attempts": 0,
  "attempts_per_second": 32.51067260301581,
  "completed_per_second": 32.51067260301581,
  "error_rate": 0.0
}
```

Flow duration includes inter-step think-time, excludes trailing pacing; failed attempts are included.
Completed/s is successful checkout throughput, not HTTP RPS. Interrupted attempts have no final latency/outcome.
Percentiles are computed from individual samples, never by averaging endpoint percentiles.
Low sample counts limit percentile interpretation; thresholds remain hypotheses until measured.
