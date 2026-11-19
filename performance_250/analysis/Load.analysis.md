# Raw CSV analysis

Source: `/Users/thuytran/Workspace/HW05-Performance-Testing/performance_250/raw_logs/23120367_Load_raw.csv`
SHA256: `a78c552b144202b0d1082e67db7f977c24c7109e88f51f48209b521a9486f61e`
Window: 182.861 seconds. Type-7 linear quantiles; ms; RPS uses declared common measurement window; error rates are fractions

| Scope | Samples | min_ms | avg_ms | med_ms | p90_ms | p95_ms | p99_ms | max_ms | rps | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HTTP overall (request-weighted) | 1520 | 0.760000 | 3.801014 | 3.360000 | 6.370500 | 7.239200 | 8.827860 | 33.743000 | 8.312325 | 0.000000 |
| cart | 304 | 1.579000 | 3.670523 | 3.503000 | 4.639500 | 4.952500 | 6.522170 | 30.188000 | 1.662465 | 0.000000 |
| checkout | 304 | 3.086000 | 6.444628 | 6.177000 | 7.952700 | 8.605550 | 10.743560 | 32.365000 | 1.662465 | 0.000000 |
| detail | 304 | 0.865000 | 2.196882 | 2.025000 | 2.970400 | 3.441700 | 5.053520 | 7.570000 | 1.662465 | 0.000000 |
| login | 304 | 2.448000 | 4.416918 | 4.256000 | 5.509100 | 5.802150 | 8.176310 | 33.743000 | 1.662465 | 0.000000 |
| search | 304 | 0.760000 | 2.276122 | 2.202000 | 3.027200 | 3.528000 | 5.478480 | 7.386000 | 1.662465 | 0.000000 |

## End-to-end flow

```json
{
  "samples": 304,
  "min_ms": 2596.0,
  "avg_ms": 3997.9111842105262,
  "med_ms": 4023.0,
  "p90_ms": 4804.7,
  "p95_ms": 4973.65,
  "p99_ms": 5291.76,
  "max_ms": 5443.0,
  "attempts": 304,
  "completed": 304,
  "observed_outcomes": 304,
  "boundary_observations_mismatch": false,
  "interrupted_attempts": 0,
  "attempts_per_second": 1.6624649323803327,
  "completed_per_second": 1.6624649323803327,
  "error_rate": 0.0
}
```

Flow duration includes inter-step think-time, excludes trailing pacing; failed attempts are included.
Completed/s is successful checkout throughput, not HTTP RPS. Interrupted attempts have no final latency/outcome.
Percentiles are computed from individual samples, never by averaging endpoint percentiles.
Low sample counts limit percentile interpretation; thresholds remain hypotheses until measured.
