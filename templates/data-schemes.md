## Data Schemas

### Rule Engine (`rule-engine.csv`)
| Field | Type | Description |
| --- | --- | --- |
| `Project Key` | string | Jira project key the rule applies to (`DO` or `HPC`). Rules only fire against tickets from the matching project. |
| `RuleID` | string | Unique identifier for the rule. |
| `Rule Pattern` | string | Regex or keyword pattern evaluated against ticket text. |
| `Match Field` | string | Ticket field to inspect (e.g., summary, description, labels). |
| `Failure Category` | string | Specific failure label assigned when the rule matches. |
| `Category` | string | Higher-level bucket for reporting/aggregation (e.g., CDFP, GPU, Networking). |
| `Priority` | int | Evaluation order; higher values run first. |
| `Confidence` | float | Confidence score (1.0 = human-confirmed, 0.7 = LLM-suggested). |
| `Created By` | string | Indicates whether a human or LLM authored the rule. |
| `Hit Count` | int | Lifetime count of matches, used to prune unused rules. |

### Tickets Categorized (`tickets-categorized.csv`)
| Field | Type | Description |
| --- | --- | --- |
| `Project Key` | string | Jira project key from the normalized ticket (for example `DO` or `HPC`). |
| `Ticket` | string | Jira ticket key. |
| `Ticket URL` | string | Direct Jira browse link for the ticket (for example `https://jira-sd.mc1.oracleiaas.com/browse/HPC-110273`). |
| `Ticket Description` | string | Concise ticket summary text used for audit readability. |
| `Status` | string | Current Jira workflow status. |
| `Created` | date | Timestamp when the ticket was opened. |
| `Age` | int | Days elapsed since creation. |
| `Runbook Present` | bool | Indicates whether a runbook exists for the category. |
| `Category of Issue` | string | Failure category assigned to the ticket. |
| `Category` | string | Higher-level bucket associated with the chosen rule; mirrors the rule-engine `Category`. |
| `Rules Used` | string | Comma-separated list of matching `RuleID` values (if any). |
| `Categorization Source` | string | Origin of the label: `rule` (regex match), `ml` (local ML classifier fallback), or `none` (uncategorized). |
| `LLM Confidence` | float | For `rule` rows, the highest matching rule confidence; for `ml` rows, the local classifier's predicted probability; empty for `none`. |
| `Human Audit for Accuracy` | string | Review state: `pending-review` (rule matched, confidence >= 0.5), `needs-review` (no match or confidence < 0.5), `correct` (human confirmed), `incorrect` (human rejected). |
| `Human Audit Guidance` | string | Inline reminder for auditors: `Before audit use pending-review or needs-review. After audit set correct or incorrect. For needs-review add Human Comments using: Expected Category of Issue <> / Expected Category <> / Reason <>.` |
| `Human Comments` | string | Supplemental notes captured during audit. |

### ML Training Data (`ml-training-data.csv`)
| Field | Type | Description |
| --- | --- | --- |
| `Ticket` | string | Jira ticket key (e.g. `DO-1234567`). |
| `Category of Issue` | string | Correct failure category label assigned by a human. |
| `Category` | string | Higher-level bucket (e.g. GPU, CDFP, SmartNIC). |
| `Label Source` | string | Who provided the label: `human` or `rule-verified`. |
| `Label Date` | date | ISO date when the label was assigned. |
| `Notes` | string | Optional notes from the labeler. |
