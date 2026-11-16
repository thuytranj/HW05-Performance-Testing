# AI verification and misinterpretation hunt

Record the AI's real first analysis BEFORE correcting it. Never invent an incorrect AI claim.
Raw files: [actual filenames]. SHA256 / analysis output: [actual references].
Units: latency milliseconds; rate fractions 0..1 (multiply by 100 for %); HTTP requests/s differs from successful checkouts/s.

| Chỉ số / Nhận định của AI | Giá trị trích xuất từ Raw CSV Log | Đánh giá (Chính xác / Sai lệch / Ảo giác) | Giải thích nguyên nhân kỹ thuật |
|---|---|---|---|
| [Trích nguyên nhận định thật] | [File, SHA256, metric, endpoint, số mẫu, cửa sổ đo, giá trị] | [Đánh giá sau khi tự kiểm tra] | [Cách tính / bằng chứng source] |

Review targets (questions, not fabricated findings):
- Does AI confuse avg, median and p95, or ms and seconds?
- Does it average endpoint p95s instead of recomputing the pooled distribution?
- Does it equate requests/s with users/s or checkout completions/s?
- Are HTTP failure rate, business-check failure rate and flow failure rate distinguished?
- Are missing observations/interruptions reported rather than interpreted as zero?
- Are stress ramp/recovery and soak steady-state metrics separated from whole-run averages?
- Does an optimization match actual SQLite/node-sqlite3 code, schema and query plan?

## Optimization feasibility (Task 2)

| Actual AI recommendation | Feasible / Hallucinated / Unverified | Source or experiment | Reasoning and trade-off |
|---|---|---|---|
| [Actual proposal] | [Classification] | [Code lines / EXPLAIN QUERY PLAN / measurement] | [Evidence-based reason] |

SQLite WAL is an option to evaluate, not a guaranteed fix. Connection-pool advice must fit sqlite3's actual single Database instance.
An index proposal needs query-plan evidence; this SUT searches LIKE '%keyword%', so do not assume a normal name index removes the scan.
No stock column exists in this revision; claiming stock depletion or a stock-index bottleneck is unsupported.

## Human review of generated plans (Task 1)

| Original AI choice | Human correction | Why AI missed it | Evidence / commit |
|---|---|---|---|
| [Actual parameter/assertion/data mistake] | [Actual fix] | [Prompt/model/endpoint characteristic] | [Link] |
