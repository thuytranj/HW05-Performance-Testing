# HW05 requirements traceability

Primary authority: project `docs/2026.HW05.Performance Testing_En.pdf`, 9 pages, sections below.
If source assignment changes, re-read it and update this matrix. User-selected defaults are not assignment mandates.

| Requirement | Source | Skill/tool or deliverable | Completion evidence |
|---|---|---|---|
| Individual; 10-hour estimate; Moodle deadline | §1 | Report identity, Moodle check | Actual student/date |
| AI-first, stepwise prompts, human review | §2, §6 Task1 | Audit + plan corrections | Complete actual interactions, actual edits |
| Text documentation | §2 | Markdown reports | Working process log |
| Auth/read/transactional groups; workflow unique in group | §5 | Discovery + shared five-step workflow | Source map + student uniqueness confirmation |
| Same E2E in Load/Stress/Spike | §6 Task1 | Three named wrappers, one lib/workflow.js | Actual run logs all five endpoints |
| CSV data-driven requests | §6 Task1 | data/e2e_test_data.csv | DB-verified accounts/product IDs |
| Realistic VUs/ramp/think-time, justification | §6 Task1 | makeOptions + report design table | Human explanation, measured tuning |
| Three distinct report views; no repeated type | §6 Task1 | dashboard / reporter / custom group-status HTML | Three actual HTML folders |
| StudentID_ScenarioType_YYYYMMDD | §6, §11 | bootstrap actual-date filenames | Files match run date |
| AI mistakes in plans and cause | §6 Task1 | Human review table | Original AI output + correction/commit |
| Execute all scenarios; screenshot tool and backend monitor together | §6 Task1 | run.sh reminders, resource CSV | Actual DURING-run screen per scenario |
| Hardware screenshot and spec table | §6 Task1 | collect_hardware.sh + manual screenshot | Actual CPU/RAM/OS/hostname, previous deployment match |
| Reset lockout between triggered Stress/Spike runs | §6 Task1 | reset_db.sh isolated restart/seed | events.jsonl + actual observed lockout/reset steps |
| Raw logs plus HTML folders | §6, §14 | Full native k6 CSV + summaries + HTML | Attach full logs, not only summaries; clarify literal .jtl with TA |
| Short soak 10–15min; numeric hardware threshold | §6 Task1 | Soak wrapper and raw/resource analysis | Actual 600–900sec sustained load, RPS/RSS/stability evidence |
| Unlisted video total>=6min, own Vietnamese narration | §6 Task1, §11 | Demo guide in SKILL | YouTube visibility/duration/voice; tool+monitor same frame |
| Genuine bugs/issues with screenshots if found | §6 Task1, §14 | Report issue links | Actual reproduction/issue/screenshots; no invented bugs |
| AI analyzes logs and suggests thresholds | §6 Task2 | Actual AI first analysis retained | Prompt/output referencing raw samples |
| Misinterpretation hunt with correct raw values | §6 Task2 | Four-column table | Raw filename/hash/metric/sample scope/value/explanation |
| Feasible vs hallucinated optimizations | §6 Task2 | Feasibility table | Source/schema/query-plan or experiment |
| Continuous model watches commits, chooses tests, flags p95 | §6 Task3 | continuous-performance.md | Flowchart and cost/false-alarm discussion |
| Reusable Agent Skill + full endpoint-group demo | §7 | This skill package | Skill included + actual demonstration video |
| Declare JMeter/k6, AI and monitor tools | §8, §9 | AI Audit/environment table | Real names and versions |
| Bloom G9.2/G9.3/G9.4/G9.6 | §3, §8 | Apply tests / analyze raw / human-AI review / continuous proposal | Trace concrete artifacts to levels |
| AI Audit mandatory appendix: tool, date/time, prompt, output | §9 | record_audit.py or direct Markdown | Markdown+PDF; prompt + final response per interaction, no internal reasoning/progress/tool traces; declare use |
| AI Critique one paragraph 200–300 words | §10 | Student-authored critique | Markdown+PDF; error/bias/incomplete, why, lesson |
| Real attributable evidence; hostname matches previous homework | §11 | Actual screenshots/raw/video/hardware | Manual authenticity check; never generated substitutes |
| New commit per procedure step; text log | §12 | Scoped commits when authorized | git log --date=iso-strict --pretty=fuller --stat |
| Random30% oral defense5–7min | §13 | Explain actual workflow/results | Student understands evidence |
| ZIP naming and self-assessed grade000..100 | §14 | README + packaging | Student chooses honest grade |
| Main report Markdown+PDF, public repo link, all data/plans/logs/reports | §14 | Report templates/check_submission.py | Actual complete zip with linked artifacts |
| README: assessment table/scenarios/groups/soak numbers/issues/video | §14 | templates/README.md | All measured fields filled |
| Load30 Stress20 Spike20 AI10 Continuous10 Skill10 | §15 | Self-assessment table | Student scoring backed by evidence |
| No late submissions; missing required doc0; copied work/prompts0 for both | §17 | Final manual check | Moodle on time, complete original work |

## User-specific choices vs assignment mandates

- User requires k6, student23120367, >=40 CSV rows, independent account/VU, specified three HTML mechanisms, macOS expected hostname Thuys-MacBook-Air, raw CSV + JSON summary, and seven phases. These strengthen/specify the assignment; do not describe account40 or those exact HTML paths as universal course requirements.
- The PDF encourages Agent Skills but allocates10 points to them. Supply this custom skill plus a real usage demo when aiming for that criterion.
- PDF permits k6 equivalent outputs yet literally requests .jtl logs. Preserve native k6 samples, disclose and seek TA clarification; fabricating JMeter format/evidence does not resolve ambiguity.
- Optional absence of latency-only performance issues is not penalized according to Task1; genuine error/crash/regression findings still belong in issues when found.
- No stated numeric minimum VUs/RPS or universal p95 budget. Parameter defaults need review and empirical tuning.
