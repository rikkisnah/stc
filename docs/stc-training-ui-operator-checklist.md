# STC Training UI Operator Checklist

Use this checklist for each UI-driven training pass.

1. Open the app and click `Train STC model`.
2. Select ticket source:
   - `JQL` (preferred), or
   - `Ticket IDs` (for targeted fixes).
3. Enter ticket input and set `Max tickets` based on run type:
   - Bootstrap/low-label runs: `Max tickets >= 20` (or lower `Min samples`)
   - Incremental tuning runs: `Max tickets = 5` (recommended per pass)
4. Set `Ticket resolution filter = Resolved only` (recommended for cleaner training labels).
5. Keep advanced defaults unless needed:
   - `Training data CSV = scripts/trained-data/ml-training-data.csv`
   - `Min samples = 20`
   - `Max review rows = 200`
   - Note: ML training checks total labeled samples (existing CSV + harvested labels), not just this run's ticket count.
6. Set phase toggles:
   - `Enable ML Training = ON`
   - `Enable ML Rule Generation = ON`
   - `Skip Human Audit #1 = OFF`
   - `Skip Human Audit #2 = OFF`
7. Click `OK` to start the run.
8. Monitor pipeline status, logs, elapsed time, and heartbeat.
9. At `Human Audit — Phase 1`:
   - review `tickets-categorized.csv`,
   - update only audit fields/comments per policy,
   - click `Save Changes`,
   - click `Continue Pipeline`.
10. At `Human Audit — Phase 2`:
    - repeat review/corrections,
    - click `Save Changes`,
    - click `Continue Pipeline`.
11. On completion, verify artifacts:
    - `tickets-categorized.csv`
    - `rule-engine.local.csv`
    - ML model/report/log files in the run output directory.
12. Open `/sessions` and record run details (run ID, batch, outcomes).
13. If outputs are audited and stable, go to `Promote to Golden`, load diff, and promote.
14. Run one regression pass on the same audited ticket set; promote only if results match expected audited output.
