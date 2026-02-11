# Plan: Configure `JIRA_TOKEN` loading in `scripts/get-tickets.py`

## Goal
Move the hard-coded `JIRA_TOKEN` constant into a configurable source so the script first attempts to read credentials from `config env.json`, while preserving the existing default token and warning when the config is missing.

## Steps
1. ✅ Inspect current token usage in `scripts/get-tickets.py` to understand header construction and where the constant is referenced.
2. Define the desired config format (e.g., `{ "jira_token": "..." }`) and determine the search path (likely repo root or `scripts/`).
3. Implement a helper that attempts to load `config env.json`, returning the `jira_token` value when present.
4. Emit a warning (stdout) if the config cannot be read or lacks the key, then fall back to the current default token `"REDACTED_BITBUCKET_PAT"`.
5. Update `make_headers()` (and any other token consumers) to use the helper-provided token rather than the global constant.
6. Verify the script still behaves identically when no config file exists and document the new config option within the script header comment or README as needed.
