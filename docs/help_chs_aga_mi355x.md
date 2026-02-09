# Help CHS in AGA4 (GPUv6/MI355x)

_IC1 ticket-readiness assessment converted from PDF on 2026-02-07._

## 1. Overview

We reviewed how well CHS technicians can execute the MI355x repair tickets they receive. For each ticket pattern we captured:

- **Category & ticket example**
- **Current instructions** (from the ticket/runbook)
- **Issues blocking CHS**
- **Runbook status** (actionable & CHS-approved?)
- **Recommended fixes** for the authoring teams

## 2. Ticket-level findings

| # | Category | Example ticket(s) | Current guidance | Issues for CHS | Actionable? | CHS runbook? | Recommended fixes |
|---|----------|-------------------|------------------|----------------|-------------|---------------|-------------------|
| 1 | Card management | [DO-2614127](https://jira-sd.mc1.oracleiaas.com/browse/DO-2614127?filter=381507), [DO-2616398](https://jira-sd.mc1.oracleiaas.com/browse/DO-2616398?filter=381507) | Runbook link is embedded in description | Duplicate of row 4; SmartNIC wipe troubleshooting without DHCP offer info | No | No | Remove HoPS dependency; provide CHS-specific smartnic wipe instructions |
| 2 | Open problems | [DO-2605626](https://jira-sd.mc1.oracleiaas.com/browse/DO-2605626) | DCO ticket runbook + ARO runbook links | Mixed ticket formats, multiple runbooks, missing physical tasks, BMP-825375 was HoPS proxy not TRS | No | No | Define ownership, ensure TRS-generated runbooks exist, avoid HoPS proxy dependency |
| 3 | Card IP mismatch | [DO-2625147](https://jira-sd.mc1.oracleiaas.com/browse/DO-2625147) | “Check cross-cabling; SmartNIC FPF253714F4 should be invisible.” | Ticket expected CHS to diagnose mapping; lacked endpoint detail | No | No | Tickets must include both endpoints and explicit swap instructions |
| 4 | Smartnic ROT wipe / DHCP failures | [DO-2616171](https://jira-sd.mc1.oracleiaas.com/browse/DO-2616171), [DO-2614127](https://jira-sd.mc1.oracleiaas.com/browse/DO-2614127), [DO-2616398](https://jira-sd.mc1.oracleiaas.com/browse/DO-2616398) | Reseat smartnics, inspect cabling, power drain, check ROT serials; runbook links in DevOps (CRDMGMT) | Tickets call for triage (ILOM OPs, TOR checks) and lack serial/elevation mapping. Linked runbooks are not CHS-approved. | No | No | Provide CHS-published recipe focused on physical work only. |
| 5 | Fix open problems | [DO-2616570](https://jira-sd.mc1.oracleiaas.com/browse/DO-2616570), [DO-2622675](https://jira-sd.mc1.oracleiaas.com/browse/DO-2622675) | Open problem list with FMS link | Same deficiencies as row 3 (missing endpoints, unclear action). | No | No | Align with row 3 guidance (explicit physical steps, endpoints). |
| 6 | Cable replacement | [DO-2569753](https://jira-sd.mc1.oracleiaas.com/browse/DO-2569753) | Ticket requests troubleshooting plus a list of reference docs and Grafana links | Overloads techs with historical/diagnostic work; conflicting “request cable” vs “troubleshoot” instructions. | No | No | Provide only the necessary endpoints and a single CHS runbook. |
| 7 | Link down from CPV health check | [DO-2616924](https://jira-sd.mc1.oracleiaas.com/browse/DO-2616924) | Identify down link, list open problems | CPV tickets mix OS output with physical info; require CHS to translate host/TN context. | No | No | Automate CPV tickets with TRS/GRT recipes; include physical port mapping. |
| 8 | Health check v2 | [DO-2625265](https://jira-sd.mc1.oracleiaas.com/browse/DO-2625265) | “Verify CDFP mapping” | Request is vague about what failed; no physical request or mapping. | No | No | CPV must state the expected mapping and explicit action. |
| 9 | Power shelf inspection | [DO-2571809](https://jira-sd.mc1.oracleiaas.com/browse/DO-2571809) | “Check RU41 power shelf; PS1 failed.” | Ticket auto-created by CHS; unclear monitoring ownership. | No | No | Identify owner (Pulse/DCICM) and automate detection. |
| 10 | Network connection correction | [DO-2600701](https://jira-sd.mc1.oracleiaas.com/browse/DO-2600701) | “Correct cabling per topology between hostnames.” | Host-only identifiers; unclear “correct connection” action. | No | No | Provide serial/elevation endpoints and precise action (reseat vs replace). |
| 11 | Cable validation failures | [DO-2612700](https://jira-sd.mc1.oracleiaas.com/browse/DO-2612700) | Links flagged as empty/mis-cabled during CPV | Summary contradicts description; lacks physical mapping and CHS runbook. | No | No | Include serial/elevation, expected switch ports, and approved recipe. |
| 12 | RDMA link unstable | [DO-2616078](https://jira-sd.mc1.oracleiaas.com/browse/DO-2616078) | Replace specified cables, verify link, power cycle if needed | Instructions mix physical swap with ticket triage/history tasks; relies on hostnames. | No | No | Provide physical identifiers, remove history-analysis steps, publish CHS runbook. |
| 13 | Reseat / replace PSU | [DO-2599694](https://jira-sd.mc1.oracleiaas.com/browse/DO-2599694) | TRS ticket with links and special instructions | Clear action plan but unclear closure steps; mentions RHS escalation. | Yes | Yes | Update TRS template to clarify resolution/validation flow and align with RHS. |

## 3. Systemic gaps & recommendations

### Open problem hygiene

- 1,052 active open problems; 827 labeled `GENERIC_OPEN_PROBLEMS` without GRT-aligned recipes.
- Tickets often originate from TRS, CPV, HoPS, or other teams with inconsistent formatting and ownership.
- Recommended actions:
  - Route each open problem to the correct owning org early in NPI.
  - Enforce recipe-driven ticket cuts via TRS/HOPS/CPV tooling.
  - Gate CHS handoff on a published, prescriptive runbook.

### Ticket authoring quality

- Human-authored tickets (225 recent) frequently expect CHS to debug software/logical issues.
- CPV/HoPS tooling can embed TRS/GRT output to auto-fill serials, elevations, and exact port pairs.
- Suggested automations:
  - Extend SMG_SRE Triage Tool to auto-populate physical actions.
  - Require end-to-end port mappings before CHS assignment for networking tickets.
  - Block “spurious fault” tickets to CHS unless ILOM noise is filtered first.

### Training & documentation

- CHS lacks approved runbooks for most MI355x networking/SmartNIC cases.
- Recommendations:
  - DCSO to publish CHS-authorized runbooks per failure mode (SmartNIC wipe, CPV link-down, cable validation).
  - Provide TRS/CPV onboarding focused on differentiating terminating vs non-terminating repairs.
  - Share FMS/FMA handling docs only after mapping them to clear physical steps.

### Monitoring ownership

- Power shelf alarms (e.g., RU41) originated from CHS floor walks; remote monitoring unclear.
- Assign owners (Pulse, DCICM, etc.) and automate detection/ticket creation outside CHS.

## 4. AGA4 ticket volume snapshot

- Last 30 days: 909 tickets total; 17061 all-time.
- Key categories (last 30):
  - `AGA-CPV`: 145
  - `LINK_DOWN`: 69
  - `owner:Networking`: 136
  - `SMG_SRE_TRIAGE_TOOL`: 111
  - `Open Problems`: 71
  - `RDMA`: 34
  - `Smartnic wipe unable to find DHCP offer`: 2
  - Numerous smaller buckets (cable check, swap GPU, sanitization, RHS action plan, etc.).

## 5. Next steps

1. **Publish runbooks:** DCSO + service teams create CHS-approved procedures for each failure signature above.
2. **Ticket templates:** Update TRS/CPV/HoPS tooling to force serial/elevation/port data and explicit physical requests.
3. **Automation:** Ensure CPV root-cause tickets auto-include link endpoints and leverage GRT recipes.
4. **Training:** Schedule TRS/CPV ticket-handling refreshers for CHS technicians, including non-terminating repair guidelines.
