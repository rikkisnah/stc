# JQL Files

This directory contains sample Jira Query Language (JQL) snippets that can be
used with `scripts/get-tickets.py`.

Usage:

```bash
uv run python scripts/get-tickets.py -a --jql-file scripts/jql/dc_ops_default.jql
```

Notes:
- The file should contain a valid JQL query.
- `scripts/get-tickets.py` appends resolution/date filters to the JQL you
  provide.

