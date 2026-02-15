Task:
  Review `tickets-consolidated.csv`, identify miscategorized tickets, and update `rule-engine.csv` only when a new rule is needed.

  Inputs:
  - `tickets-consolidated.csv`
  - Normalized ticket JSONs under `scripts/normalized-tickets/`

  Process:
  1. Scan `tickets-consolidated.csv` and select tickets marked as `incorrect` or `needs-review`.
  2. For each selected ticket, check `Human Comments` first:
     - If comments clearly suggest a rule pattern/category, use that guidance.
     - If comments are missing or unclear, inspect the normalized ticket JSON (summary, description, comments) to determine the best `Failure Category` and `Category`.
     - Do not skip tickets just because `Human Comments` is empty.
  3. Check whether an existing rule already covers the correct categorization.
  4. Add a new rule to `rule-engine.csv` only if no existing rule reliably covers the ticket.
  5. Each new rule must include:
     - precise `Rule Pattern`
     - correct `Match Field`
     - correct `Failure Category`
     - correct `Category` (do not set `unknown` if an existing rule already maps that `Failure Category` to a concrete `Category`)
     - sensible `Priority` and `Confidence`
  5.1 Category consistency rule:
     - If your proposed `Failure Category` already appears in existing rules with a non-`unknown` `Category`, reuse that same `Category`.
     - Use `unknown` only when evidence is insufficient and no reliable mapping exists.
  6. Avoid duplicate or overly broad rules; prefer patterns that minimize false positives.
  7. Prioritize tickets that are not yet human-audited when deciding where to add new rules.

  Output:
  - Tickets reviewed
  - Tickets corrected
  - Rules added (`RuleID`, pattern, match field, failure category, category)
  - Brief reason for each added rule
  
  RESPONSE FORMAT (STRICT):
  Return ONLY valid JSON. Do not include markdown, prose, bullet lists, or code fences.
  Use this exact top-level shape:
  {
    "proposals": [
      {
        "Ticket": "<ticket key>",
        "Rule Pattern": "<regex>",
        "Match Field": "summary|description|comments|summary+description|description+comments|summary+comments|summary+description+comments",
        "Failure Category": "<failure category>",
        "Category": "<category>",
        "Priority": 80,
        "Confidence": 1
      }
    ]
  }
