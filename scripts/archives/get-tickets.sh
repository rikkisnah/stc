#!/usr/bin/env bash
# ai-generated script to fetch tickets from Jira
# Human assisted with formatting and error checking

usage() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Modes:"
  echo "  (no args)              Fetch all matching tickets"
  echo "  -Nd                    Relative: last N days (e.g. -2d, -7d, -30d)"
  echo "  START_DATE             From start date to now (YYYY-MM-DD)"
  echo "  START_DATE END_DATE    Date range (YYYY-MM-DD YYYY-MM-DD)"
  echo "  -t TICKET_KEY          Fetch a single ticket (e.g. -t DO-2639750)"
  echo "  -t URL                 Fetch a single ticket by URL"
  echo "                         (e.g. -t https://jira-sd.mc1.oracleiaas.com/browse/DO-2639750)"
  echo ""
  echo "Examples:"
  echo "  $0                     Fetch all tickets"
  echo "  $0 -2d                 Last 2 days"
  echo "  $0 2025-01-01          From 2025-01-01 to now"
  echo "  $0 2025-01-01 2025-01-31  Between two dates"
  echo "  $0 -t DO-2639750       Fetch single ticket"
  exit 1
}

JIRA_USER="rik.kisnah@oracle.com"
JIRA_TOKEN="Mjc1NTI2MDI3NzQzOmyKp+LlBsn9tMKSANBWk3gFXRHt"
BASE_URL="https://jira-sd.mc1.oracleiaas.com"

MODE="search"
TICKET_KEY=""
DATE_FILTER=""

if [ $# -ge 1 ] && [ "$1" = "-t" ]; then
  # Single ticket mode
  [ -z "$2" ] && usage
  TICKET_ARG="$2"
  # Extract ticket key from URL if needed (e.g. https://.../browse/DO-2639750)
  if [[ "$TICKET_ARG" =~ /browse/([A-Z]+-[0-9]+)$ ]]; then
    TICKET_KEY="${BASH_REMATCH[1]}"
  elif [[ "$TICKET_ARG" =~ ^[A-Z]+-[0-9]+$ ]]; then
    TICKET_KEY="$TICKET_ARG"
  else
    echo "Error: Invalid ticket key or URL: $TICKET_ARG" >&2
    usage
  fi
  MODE="single"
elif [ $# -eq 1 ]; then
  if [[ "$1" =~ ^-([0-9]+)d$ ]]; then
    DATE_FILTER=" AND created >= \"-${BASH_REMATCH[1]}d\""
    echo "Filtering: tickets created in the last ${BASH_REMATCH[1]} day(s)"
  elif [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    DATE_FILTER=" AND created >= \"$1\""
    echo "Filtering: tickets created from $1 to now"
  elif [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    usage
  else
    usage
  fi
elif [ $# -eq 2 ]; then
  if [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && [[ "$2" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    DATE_FILTER=" AND created >= \"$1\" AND created <= \"$2\""
    echo "Filtering: tickets created from $1 to $2"
  else
    usage
  fi
elif [ $# -gt 2 ]; then
  usage
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/tickets-json"
mkdir -p "$OUTPUT_DIR"

if [ "$MODE" = "single" ]; then
  # Fetch a single ticket by key
  echo "Fetching ticket ${TICKET_KEY}..."

  RESP=$(curl -s -G \
    -H "Authorization: Bearer ${JIRA_TOKEN}" \
    -H "Accept: application/json" \
    "${BASE_URL}/rest/api/2/issue/${TICKET_KEY}")

  # Check for errors
  ERROR=$(echo "$RESP" | jq -r '.errorMessages[0] // empty')
  if [ -n "$ERROR" ]; then
    echo "Error: $ERROR" >&2
    exit 1
  fi

  KEY=$(echo "$RESP" | jq -r '.key // empty')
  if [ -z "$KEY" ]; then
    echo "Error: Failed to parse response:" >&2
    echo "$RESP" | head -20 >&2
    exit 1
  fi

  echo "$RESP" | jq '.' > "$OUTPUT_DIR/${TICKET_KEY}.json"
  echo "Done. Saved to $OUTPUT_DIR/${TICKET_KEY}.json"

else
  # Search mode - fetch tickets via JQL
  JQL='(labels = GPU_V6_E6-IS_MI355X_S.01 OR "Rack Type" = GPU_MI355X_E6_R.01)
AND status != "Pending Part(s)"
AND (("Region / Domain" IN (aga.ad1, "AGA5 (AD)")
      OR "Region Affected" = AGA
      OR "Canonical AD" = aga.ad1
      OR Building = aga5)
     AND ("Rack Type" IN (GPU_MI355X_E6_R.02, GPU_MI355X_E6_R.01)
          OR labels IN (GPU_V6_E6-IS_MI355X_S.02, GPU_V6_E6-IS_MI355X_S.01, AGA-CPV))
     AND resolution = Resolved
     AND summary !~ "Master")
AND project = "DC Ops"
AND issuetype != "Service Request"
AND "Component / Item" NOT IN cascadeOption(10046, 10064)'"${DATE_FILTER}"

  ENCODED_JQL=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''${JQL}'''))")
  echo "JQL URL: ${BASE_URL}/issues/?jql=${ENCODED_JQL}"
  echo ""

  START_AT=0
  MAX_RESULTS=100
  TOTAL_FETCHED=0

  while :; do
    echo "Fetching tickets starting at ${START_AT}..."

    RESP=$(curl -s -G \
      -H "Authorization: Bearer ${JIRA_TOKEN}" \
      -H "Accept: application/json" \
      --data-urlencode "jql=${JQL}" \
      --data-urlencode "startAt=${START_AT}" \
      --data-urlencode "maxResults=${MAX_RESULTS}" \
      "${BASE_URL}/rest/api/2/search")

    COUNT=$(echo "$RESP" | jq '.issues | length')
    TOTAL=$(echo "$RESP" | jq '.total // empty')

    if [ -z "$COUNT" ] || [ "$COUNT" = "null" ]; then
      echo "Error: Failed to parse response:" >&2
      echo "$RESP" | head -20 >&2
      exit 1
    fi

    [ "$COUNT" -eq 0 ] && break

    TOTAL_FETCHED=$((TOTAL_FETCHED + COUNT))
    echo "  Got ${COUNT} tickets (${TOTAL_FETCHED}/${TOTAL} total)"

    echo "$RESP" | jq '.' > "$OUTPUT_DIR/page_${START_AT}.json"

    START_AT=$((START_AT + MAX_RESULTS))
  done

  echo "Done. Fetched ${TOTAL_FETCHED} tickets across $((START_AT / MAX_RESULTS)) pages."
fi
