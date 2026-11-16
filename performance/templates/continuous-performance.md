# Continuous Performance Testing proposal — G9.6

Adapt this model to the SUT; this is a proposal, not evidence of a deployed CI pipeline.

```mermaid
flowchart TD
    A[Commit or pull request] --> B{Backend or test change?}
    B -->|No| C[Record skip reason]
    B -->|Yes| D[Start isolated SUT and deterministic seed]
    D --> E[Smoke and baseline load test]
    E --> F{Valid comparable run?}
    F -->|No| G[Flag infrastructure or data failure]
    F -->|Yes| H[Compare endpoint p95 and error rate with baseline]
    H --> I{Budget or regression exceeded?}
    I -->|No| J[Publish raw logs reports and resource evidence]
    I -->|Yes| K[Repeat under same conditions and flag regression]
    K --> J
    L[Nightly or scheduled] --> M[Stress Spike and 10 to 15 minute soak]
    M --> J
```

Define commit selection (routes/controllers/db/schema/dependencies/test changes); schedule expensive tests separately.
Define baseline commit, comparable runner/OS/hardware, seed, pacing, resource contention and warm/cold cache.
Propose a relative p95 regression budget plus absolute latency/error budget; justify numerical choices.
Require enough observations and repeatability; a rerun does not erase the original failure.
Discuss noisy shared CI runners, small sample p95, flaky upstreams, false alarms and triage.
Compare cost of every-commit full performance suite vs smoke/load on relevant commits and heavier scheduled runs.
Retain raw CSV, summary, reports, source/config hashes and environment metadata for every run.
Keep baseline promotion explicit; never automatically bless a regression by replacing baseline with latest run.
