# Raw CSV analysis

Source: `/Users/thuytran/Workspace/HW05-Performance-Testing/performance_250/raw_logs/23120367_Soak_raw.csv`
SHA256: `ec67cb4c41df587980a34759fa86ffd844c4cc14a95490452f235c728c23fec9`
Window: 605.298 seconds. Type-7 linear quantiles; ms; RPS uses declared common measurement window; error rates are fractions

| Scope | Samples | min_ms | avg_ms | med_ms | p90_ms | p95_ms | p99_ms | max_ms | rps | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HTTP overall (request-weighted) | 11975 | 0.447000 | 4.040476 | 3.533000 | 7.326200 | 8.182800 | 10.403080 | 35.247000 | 19.783644 | 0.000000 |
| cart | 2395 | 1.037000 | 3.650910 | 3.630000 | 4.719400 | 5.256400 | 6.995080 | 14.870000 | 3.956729 | 0.000000 |
| checkout | 2395 | 1.971000 | 7.024272 | 7.071000 | 8.814600 | 9.625900 | 11.984640 | 35.247000 | 3.956729 | 0.000000 |
| detail | 2395 | 0.447000 | 2.353265 | 2.115000 | 3.301600 | 4.404900 | 6.832340 | 26.405000 | 3.956729 | 0.000000 |
| login | 2395 | 1.442000 | 4.768126 | 4.557000 | 6.239000 | 7.480200 | 11.941920 | 25.245000 | 3.956729 | 0.000000 |
| search | 2395 | 0.646000 | 2.405809 | 2.136000 | 3.411600 | 4.665000 | 8.154540 | 24.978000 | 3.956729 | 0.000000 |

## End-to-end flow

```json
{
  "samples": 2395,
  "min_ms": 2124.0,
  "avg_ms": 4034.0951983298537,
  "med_ms": 4042.0,
  "p90_ms": 4746.2,
  "p95_ms": 4962.599999999999,
  "p99_ms": 5291.299999999999,
  "max_ms": 5657.0,
  "attempts": 2395,
  "completed": 2395,
  "observed_outcomes": 2395,
  "boundary_observations_mismatch": false,
  "interrupted_attempts": 0,
  "attempts_per_second": 3.956728751788375,
  "completed_per_second": 3.956728751788375,
  "error_rate": 0.0
}
```

Flow duration includes inter-step think-time, excludes trailing pacing; failed attempts are included.
Completed/s is successful checkout throughput, not HTTP RPS. Interrupted attempts have no final latency/outcome.
Percentiles are computed from individual samples, never by averaging endpoint percentiles.
Low sample counts limit percentile interpretation; thresholds remain hypotheses until measured.
