# Adapter, measurement and validation notes

## Boundaries

This package supports the checked-in monolithic Express/sqlite3 EShop revision. It does not implement a speculative universal route parser. Bootstrap extracts endpoint/port/lockout facts from source, verifies expected request/auth signatures, records source hashes and stops for unsupported layouts or stock schema. Agent must inspect routes/controllers/schemas and update adapter when the repository differs. Runtime verifies hashes before reset/run.

Generated artifacts live in a separate performance workspace. Source code and original database are read-only to helpers. Runtime copies server/database/package+lock, changes only PORT and loopback bind, records those changes. Startup executes original destructive seed against the copied database, then Python sqlite3 adds 40+ deterministic test users. Seeded products are read from the actual copied database. Reset restarts only owned Node process, clearing in-memory carts and isolated orders; no process kill by port/name and no source DB truncate.

Password values are synthetic fixture credentials, not real accounts. data/e2e_test_data.csv belongs with test plans/data in the public submission. Dependency/runtime directories are ignored in generated workspace; keep dependency URL/checksum and source hashes. Install explicitly downloads the pinned reporter and MIT license; re-fetch with the same command before reusing generated workspace on another machine.

## Measurements

- Closed-model VUs preserve independent account identity across sequential iterations. `__VU - 1` has no modulo fallback. Multi-process/distributed tests need explicit account partitions and are unsupported as-is.
- HTTP request duration is k6 sending+waiting+receiving, excluding connection setup; do not call it browser page-load time. Flow wall time includes inter-step think-time, excludes final pacing; early failures shorten failed-flow duration.
- `flow_attempts`, `flow_completed`, `flow_success`, `flow_duration_ms` distinguish attempts, completed checkouts and outcome rate. A graceful-stop interruption can leave an attempted flow without final observation; analyzer exposes that gap.
- Setup/teardown Gauge observations mark the common window, including ramp/down and graceful completion. This is whole-run throughput, not sustained-plateau RPS. Use analyzer --from-seconds/--to-seconds on runner unix_milli logs to compare plateau/recovery/soak windows. Metrics are attributed by observation/completion time; a boundary-crossing flow's start and outcome can lie in different windows, so interrupted_attempts is N/A for slices. Separately emitted flow metrics can straddle a millisecond boundary: window slices expose boundary_observations_mismatch instead of certifying count equality. Whole-run counts remain strict. Use analyze_resources.py for sampled RSS/CPU summaries. Never average p95s across windows.
- Exact Type-7 interpolation sorts individual durations. Mean is `math.fsum/n`. Rate uses 0..1. One sample is numerically definable but inadequate to characterize a tail.
- Status histogram in Spike HTML uses dynamically named HTTP status checks under groups; k6 combines these across VUs. It does not rely on module-global counters (VU VMs do not share mutable JS state). This captures unexpected status codes as well as common errors. Group latency comes from five dedicated Trend metrics.
- `http_req_failed` captures configured expectedStatuses200/201 including network failure. A200 malformed/business-invalid response fails checks/flow outcome even if HTTP failure rate is0. Analyzer validates matching HTTP duration/request/failure sample counts and refuses truncated data.
- `ps %cpu` is process CPU use as reported by ps (typically lifetime average), not a profiler's instantaneous utilization. RSS is KiB, not bytes; report peak/trend and platform limits. Resource CSV cannot replace required same-frame screenshots/video.
- Default stress is a VU ramp; it does not prove maximum offered RPS independently of latency. Describe self-throttling and additional runs when necessary. Soak verifies a candidate sustained point, not automatically the absolute endurance threshold.
- No browser rendering and no real external payment gateway are involved; checkout is this SUT's order creation API.

## Review and run helper validation

From project root:

```bash
python3 -m unittest discover -s .agents/skills/eshop-k6-performance/tests -v
python3 .agents/skills/eshop-k6-performance/scripts/bootstrap.py --project . --output /tmp/eshop-validation --port 31367
cd /tmp/eshop-validation
python3 scripts/perf.py install
./scripts/reset_db.sh
./scripts/run.sh Load --smoke
./scripts/run.sh Stress --smoke
./scripts/run.sh Spike --smoke
python3 scripts/perf.py stop
```

Validation smoke is tool/package validation, not homework Load/Stress/Spike/Soak execution. Never include synthetic unit-test fixtures as submission evidence. Keep temporary validation artifacts outside the student's performance workspace. Full homework video, actual screenshots, soak and human critiques remain student work.

## Authoritative references

- Assignment PDF in project docs is the grading authority.
- [k6 granular CSV output and timestamp options](https://grafana.com/docs/k6/latest/results-output/real-time/csv/)
- [k6 built-in dashboard and HTML export](https://grafana.com/docs/k6/latest/results-output/web-dashboard/)
- [k6 handleSummary aggregation and output](https://grafana.com/docs/k6/latest/results-output/end-of-test/custom-summary/)
- [SharedArray init context and VU isolation](https://grafana.com/docs/k6/latest/javascript-api/k6-data/sharedarray/)
- [benc-uk/k6-reporter usage, themes and version pinning](https://github.com/benc-uk/k6-reporter)
- [Antigravity workspace skill locations and invocation](https://antigravity.google/docs/skills)

These helpers are newly authored for HW05; upstream reporter is fetched with its license rather than copied into this skill. No upstream skill text is bundled as this student's work.

## Authoring validation (2026-11-16)

- Python stdlib unit tests:9 passed (quantiles/rates, time windows, missing/truncated evidence, external DB path rejection, discovery facts, audit review preservation).
- Skill Creator quick_validate: passed; Python compile and Bash syntax checks passed.
- Actual isolated EShop at127.0.0.1:31367, k6 v2.1.0, Node v22.17.1:40 fixture accounts prepared; Load/Stress/Spike smoke each completed1 VU/1 iteration with5 HTTP200 responses and successful checkout.
- Stress reporter3.0.4 produced tabbed HTML; Spike custom HTML contained all5 groups and exact status200 count5. Built-in dashboard export separately validated with a4-second single-flow diagnostic (a normal sub-second smoke legitimately skips dashboard export).
- Test artifacts stayed under /tmp; no full homework stress/spike/soak, screenshots, video, AI critique or submission was completed by this validation. Original backend tracked files and database showed no Git diff. Do not reuse these smoke measurements as a hardware threshold.
