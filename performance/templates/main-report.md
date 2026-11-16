# HW05 — EShop k6 Performance Testing

Student ID: 23120367. Actual date: [YYYYMMDD]. Workflow uniqueness in group: [student confirmation].

## Environment and API discovery

Reference reports/api_discovery.md, source hashes, runtime adaptation and actual hardware table.
Base URL / port: [measured configuration]. Native backend or isolated backend: [explain].
Hardware: hostname, model, CPU cores, RAM, OS, node/k6 versions, backend PID; attach hardware.png.
This SUT initializes/reseeds at startup; carts are in RAM and are not cleared at checkout; no inventory column.
Lockout expected in assignment: 3 failed logins. Actual source: +2 per wrong password, threshold>=3, 180000ms.
Document source-derived behavior separately from a runtime reproduction; do not claim a reproduced bug without a reproduction.

## Test design and AI review

Same flow in every plan: login → search → detail → cart → checkout. Explain three endpoint groups.
CSV source, independent accounts, parsing, actual seed verification, stock N/A, reset isolation and steps.
Table: scenario / executor / VUs / stages / think-time / thresholds / justification.
Defaults are initial hypotheses, not measured hardware capacity. Attach actual human corrections and why AI missed them.
Three distinct views: Load built-in dashboard; Stress k6-reporter tabbed summary; Spike custom group/status HTML.

## Results and resources

For each Load/Stress/Spike: exact command, actual filename/date, start/end, commit, raw CSV SHA256,
summary JSON, HTML, backend CPU/RSS, screenshot showing tool+monitor, HTTP metrics by endpoint,
HTTP overall metrics, flow latency, successful checkout/s, HTTP error rate and flow error rate.
Retain failing runs. Exit99 = threshold breach; explain without relabeling it a pass.
Mention CSV vs literal JMeter .jtl discrepancy and TA confirmation; never rename CSV to .jtl.

## Endurance / soak threshold

Sustained load 10–15 minutes: VUs, sustained seconds, resource observations, stable RPS and RAM ceiling.
Define stable (p95/error/memory behavior) before declaring a threshold; distinguish stress ceiling from sustained verified load.
One passing level proves only that level. Use fresh workspaces for additional levels, never overwrite raw evidence.
Present stable/unstable bracket and observed limitations. Cart accumulation may cause memory growth; do not hide it by resetting mid-run.

## AI analysis and misinterpretation hunt

Link analysis/ai-verification.md, actual first AI output, correct raw values and optimization feasibility table.
Critique must be human-authored; do not fabricate AI errors when none are found.

## Bugs and performance issues

Actual reproductions, screenshot, environment, expected/actual behavior, GitHub Issue URL; explicitly state none found if applicable.

## Conclusion and Continuous Performance Testing

Include reports/continuous-performance.md flowchart and cost/false-alarm discussion.

## Demonstration and Agent Skill

Unlisted video URLs/timestamps: total>=6 minutes, own Vietnamese voice, tool+monitor in one frame.
Show skill invocation through a complete endpoint-group workflow and resulting artifacts.
Include custom skill files and attribution for any upstream references/dependencies.

## Mandatory appendices

AI Audit Report (tool/model, interaction date/time/timezone, prompt, final user-visible response per interaction, human review).
Exclude internal reasoning, progress updates and tool traces from the AI Audit; preserve test raw logs separately.
AI Critique: one actual 200–300-word paragraph written by the student, errors/bias/incompleteness, why missed, collaboration lesson.
Main report / Audit / Critique each Markdown+PDF, visually verified. Git commit log and referenced links.
