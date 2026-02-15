"""Tests for normalize_tickets.py"""

import importlib
import json
from pathlib import Path

import pytest

# Import hyphenated module
normalize_tickets = importlib.import_module("normalize_tickets")
archive_existing = normalize_tickets.archive_existing
clean_jira_text = normalize_tickets.clean_jira_text
extract_comments = normalize_tickets.extract_comments
extract_links = normalize_tickets.extract_links
extract_location = normalize_tickets.extract_location
extract_option_value = normalize_tickets.extract_option_value
extract_people = normalize_tickets.extract_people
extract_rack_serial = normalize_tickets.extract_rack_serial
extract_sla = normalize_tickets.extract_sla
extract_status = normalize_tickets.extract_status
extract_ticket = normalize_tickets.extract_ticket
filter_labels = normalize_tickets.filter_labels
is_noise_comment = normalize_tickets.is_noise_comment
normalize_issue = normalize_tickets.normalize_issue
normalize_json = normalize_tickets.normalize_json
process_file = normalize_tickets.process_file
trim_date = normalize_tickets.trim_date
load_tickets_file = normalize_tickets.load_tickets_file
collect_ticket_keys = normalize_tickets.collect_ticket_keys


# --- trim_date ---

class TestTrimDate:
    def test_full_jira_date(self):
        assert trim_date("2026-02-06T00:02:39.586+0000") == "2026-02-06T00:02:39Z"

    def test_iso_date(self):
        assert trim_date("2026-02-06T00:02:39+0000") == "2026-02-06T00:02:39Z"

    def test_none(self):
        assert trim_date(None) is None

    def test_empty(self):
        assert trim_date("") is None

    def test_already_trimmed(self):
        assert trim_date("2026-02-06T00:02:39Z") == "2026-02-06T00:02:39Z"


# --- clean_jira_text ---

class TestCleanJiraText:
    def test_removes_nbsp(self):
        assert clean_jira_text("Hello\u00a0world") == "Hello world"

    def test_normalizes_line_endings(self):
        assert clean_jira_text("line1\r\nline2") == "line1\nline2"

    def test_strips_whitespace(self):
        assert clean_jira_text("  hello  ") == "hello"

    def test_none(self):
        assert clean_jira_text(None) is None

    def test_empty(self):
        assert clean_jira_text("") is None

    def test_combined_basic(self):
        text = "Dear team\r\n\r\nHost failed on\u00a0Smartnic  "
        assert clean_jira_text(text) == "Dear team\n\nHost failed on Smartnic"

    def test_removes_replacement_char(self):
        assert clean_jira_text("host\ufffdname") == "hostname"

    def test_en_dash_to_hyphen(self):
        assert clean_jira_text("2026\u201302\u201307") == "2026-02-07"

    def test_ellipsis(self):
        assert clean_jira_text("wait\u2026") == "wait..."

    def test_strips_tqdm_blocks(self):
        text = "100%|\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588| 2/2 [00:02<00:00]"
        result = clean_jira_text(text)
        assert "\u2588" not in result
        assert "2/2" in result

    def test_strips_color_markup(self):
        text = "{color:#ff0000}Warning: host down{color}"
        assert clean_jira_text(text) == "Warning: host down"

    def test_strips_code_block(self):
        text = "Output:\n{code:java}\nsome data\n{code}\nEnd."
        result = clean_jira_text(text)
        assert "some data" in result
        assert "{code" not in result

    def test_strips_noformat(self):
        text = "{noformat}\nraw output\n{noformat}"
        result = clean_jira_text(text)
        assert "raw output" in result
        assert "{noformat}" not in result

    def test_strips_panel(self):
        text = "{panel:title=TRS|borderColor=red}\nAction needed\n{panel}"
        result = clean_jira_text(text)
        assert "Action needed" in result
        assert "{panel" not in result

    def test_strips_empty_bold(self):
        assert clean_jira_text("{*}{*}text") == "text"

    def test_jira_link_to_text(self):
        text = "[host page|https://hops.svc.ad1/ui/deviceview?serial=123]"
        assert clean_jira_text(text) == "host page"

    def test_strips_image_ref(self):
        assert clean_jira_text("See !screenshot.png! here") == "See  here"

    def test_strips_heading_markup(self):
        assert clean_jira_text("h3. Next Steps") == "Next Steps"

    def test_strips_horizontal_rule(self):
        text = "above\n----\nbelow"
        result = clean_jira_text(text)
        assert "----" not in result
        assert "above" in result
        assert "below" in result

    def test_forced_linebreak(self):
        assert clean_jira_text("line1\\\\line2") == "line1\nline2"

    def test_jira_table_row(self):
        text = "|*Serial*|2602XQ103J|"
        result = clean_jira_text(text)
        assert "Serial: 2602XQ103J" in result

    def test_collapses_blank_lines(self):
        text = "a\n\n\n\n\nb"
        assert clean_jira_text(text) == "a\n\nb"


# --- extract_option_value ---

class TestExtractOptionValue:
    def test_option_object(self):
        opt = {"self": "https://...", "value": "AGA", "id": "123", "disabled": False}
        assert extract_option_value(opt) == "AGA"

    def test_list_single_option(self):
        lst = [{"self": "https://...", "value": "AGA", "id": "123"}]
        assert extract_option_value(lst) == "AGA"

    def test_list_multiple_options(self):
        lst = [
            {"self": "https://...", "value": "AGA", "id": "1"},
            {"self": "https://...", "value": "PHX", "id": "2"},
        ]
        assert extract_option_value(lst) == ["AGA", "PHX"]

    def test_plain_string(self):
        assert extract_option_value("GPU_MI355X") == "GPU_MI355X"

    def test_plain_int(self):
        assert extract_option_value(42) == 42

    def test_none(self):
        assert extract_option_value(None) is None

    def test_dict_without_value(self):
        d = {"name": "test", "key": "val"}
        assert extract_option_value(d) is d


# --- extract_ticket ---

class TestExtractTicket:
    def test_full_issue(self):
        issue = {
            "id": "55487795",
            "key": "DO-2639750",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops", "id": "10209"},
                "issuetype": {"name": "Incident", "id": "10000"},
                "summary": "[NEW CAPACITY] 2541XK10FR | Check ROT connection ",
                "priority": {"name": "Medium", "id": "3"},
            },
        }
        result = extract_ticket(issue)
        assert result == {
            "id": "55487795",
            "key": "DO-2639750",
            "project": {"key": "DO", "name": "DC Ops"},
            "type": "Incident",
            "summary": "[NEW CAPACITY] 2541XK10FR | Check ROT connection",
            "priority": "Medium",
        }

    def test_missing_fields(self):
        issue = {"id": "1", "key": "DO-1", "fields": {}}
        result = extract_ticket(issue)
        assert result["project"] == {"key": None, "name": None}
        assert result["type"] is None
        assert result["priority"] is None


# --- extract_status ---

class TestExtractStatus:
    def test_resolved(self):
        fields = {
            "status": {"name": "Resolved", "id": "5"},
            "resolution": {"name": "Resolved", "id": "10603"},
            "created": "2026-02-06T00:02:39.586+0000",
            "resolutiondate": "2026-02-06T02:13:12.051+0000",
            "updated": "2026-02-06T02:13:12.298+0000",
        }
        result = extract_status(fields)
        assert result == {
            "current": "Resolved",
            "resolution": "Resolved",
            "created": "2026-02-06T00:02:39Z",
            "resolved": "2026-02-06T02:13:12Z",
            "updated": "2026-02-06T02:13:12Z",
        }

    def test_open_no_resolution(self):
        fields = {
            "status": {"name": "Open", "id": "1"},
            "resolution": None,
            "created": "2026-02-06T00:02:39.586+0000",
        }
        result = extract_status(fields)
        assert result["current"] == "Open"
        assert result["resolution"] is None
        assert result["resolved"] is None


# --- extract_people ---

class TestExtractPeople:
    def test_full(self):
        fields = {
            "assignee": {"displayName": "Greg Parker", "name": "greg@oracle.com"},
            "reporter": {"displayName": "Izamar Calderon", "name": "izamar@oracle.com"},
            "watches": {"watchCount": 5, "isWatching": False},
        }
        result = extract_people(fields)
        assert result == {
            "assignee": "Greg Parker",
            "reporter": "Izamar Calderon",
            "watchers": 5,
        }

    def test_null_assignee(self):
        fields = {
            "assignee": None,
            "reporter": {"displayName": "John"},
            "watches": {"watchCount": 1},
        }
        result = extract_people(fields)
        assert result["assignee"] is None
        assert result["reporter"] == "John"

    def test_missing_fields(self):
        result = extract_people({})
        assert result == {"assignee": None, "reporter": None, "watchers": None}


# --- extract_rack_serial ---

class TestExtractRackSerial:
    def test_found(self):
        labels = ["2541XK10FR", "RackSerial:2551ZA8062", "triage"]
        assert extract_rack_serial(labels) == "2551ZA8062"

    def test_not_found(self):
        labels = ["triage", "Compute"]
        assert extract_rack_serial(labels) is None

    def test_empty(self):
        assert extract_rack_serial([]) is None


# --- extract_location ---

class TestExtractLocation:
    def test_full(self):
        fields = {
            "customfield_14606": [{"self": "...", "value": "AGA", "id": "1"}],
            "customfield_12605": {"self": "...", "value": "aga.ad1", "id": "2"},
            "customfield_12604": {"self": "...", "value": "aga4", "id": "3"},
            "customfield_10602": "GPU_MI355X_E6_R.01",
            "customfield_10104": "2541XK10FR",
            "labels": ["RackSerial:2551ZA8062"],
        }
        result = extract_location(fields)
        assert result == {
            "region": "AGA",
            "availability_domain": "aga.ad1",
            "building": "aga4",
            "rack_type": "GPU_MI355X_E6_R.01",
            "host_serial": "2541XK10FR",
            "rack_serial": "2551ZA8062",
        }

    def test_missing_fields(self):
        result = extract_location({})
        assert result["region"] is None
        assert result["rack_serial"] is None


# --- filter_labels ---

class TestFilterLabels:
    def test_removes_noise_prefixes(self):
        labels = [
            "Compute", "building:aga4", "owner:Compute",
            "pd:P0_GPU", "RackSerial:123", "Realm:oc1",
            "Region:AGA", "TPEC-GPU-SEV2", "SPGXTAIL-8000",
        ]
        result = filter_labels(labels)
        assert result == ["Compute"]

    def test_removes_noise_exact(self):
        labels = ["triage", "ORTANO", "RegionChanged", "TPEC_UPDATED", "TRS_CUT"]
        result = filter_labels(labels)
        assert result == ["triage"]

    def test_keeps_useful(self):
        labels = [
            "2541XK10FR", "Architecture:E6", "AutoFilled", "Compute",
            "DeviceModel:GPU_V6_E6-IS_MI355X_S.01", "HOST_NOT_FOUND",
            "TRSTriage", "degree_2", "triage",
        ]
        result = filter_labels(labels)
        assert result == labels

    def test_empty(self):
        assert filter_labels([]) == []


# --- extract_links ---

class TestExtractLinks:
    def test_outward_link(self):
        fields = {
            "issuelinks": [{
                "id": "1",
                "type": {"name": "Blocks", "outward": "blocks", "inward": "is blocked by"},
                "outwardIssue": {
                    "key": "BMP-818559",
                    "fields": {
                        "summary": "Compute Final Provisioning",
                        "status": {"name": "Resolved"},
                    },
                },
            }],
        }
        result = extract_links(fields)
        assert len(result) == 1
        assert result[0] == {
            "key": "BMP-818559",
            "relation": "blocks",
            "status": "Resolved",
            "summary": "Compute Final Provisioning",
        }

    def test_inward_link(self):
        fields = {
            "issuelinks": [{
                "id": "2",
                "type": {"name": "Relates", "outward": "relates to", "inward": "relates to"},
                "inwardIssue": {
                    "key": "RPR-1441341",
                    "fields": {
                        "summary": "Problem Type:SMARTNIC",
                        "status": {"name": "Open"},
                    },
                },
            }],
        }
        result = extract_links(fields)
        assert result[0]["key"] == "RPR-1441341"
        assert result[0]["relation"] == "relates to"
        assert result[0]["status"] == "Open"

    def test_empty(self):
        assert extract_links({}) == []
        assert extract_links({"issuelinks": []}) == []


# --- extract_sla ---

class TestExtractSla:
    def test_completed_cycles(self):
        fields = {
            "customfield_10003": {
                "completedCycles": [{
                    "elapsedTime": {"millis": 865882, "friendly": "14m"},
                }],
            },
            "customfield_14710": {
                "completedCycles": [{
                    "elapsedTime": {"millis": 7832720, "friendly": "2h 10m"},
                }],
            },
        }
        result = extract_sla(fields)
        assert result == {
            "time_to_first_response": "14m",
            "time_to_resolve": "2h 10m",
        }

    def test_ongoing_cycle(self):
        fields = {
            "customfield_10003": {
                "completedCycles": [],
                "ongoingCycle": {
                    "elapsedTime": {"millis": 300000, "friendly": "5m"},
                },
            },
        }
        result = extract_sla(fields)
        assert result == {"time_to_first_response": "5m"}

    def test_no_sla(self):
        assert extract_sla({}) is None

    def test_empty_sla_fields(self):
        fields = {
            "customfield_10003": {"completedCycles": []},
            "customfield_14710": None,
        }
        assert extract_sla(fields) is None


# --- is_noise_comment ---

class TestIsNoiseComment:
    def test_ocean_notification(self):
        comment = {
            "author": {"name": "gear-jep-notifier"},
            "body": "Ocean Notification sent to:\n* Reece Harris via push",
        }
        assert is_noise_comment(comment) is True

    def test_updated_jira_status(self):
        comment = {
            "author": {"name": "gear-jep-notifier"},
            "body": "Updated Jira Status from Open to In Progress",
        }
        assert is_noise_comment(comment) is True

    def test_autocut_bot(self):
        comment = {
            "author": {"name": "jirasd-gear-rcp-autocut-ad1-us-saltlake-2"},
            "body": "Updating Handover ticket to severity 2",
        }
        assert is_noise_comment(comment) is True

    def test_human_comment(self):
        comment = {
            "author": {"name": "greg.p.parker@oracle.com", "displayName": "Greg Parker"},
            "body": "Got IP addresses for each smartNIC",
        }
        assert is_noise_comment(comment) is False

    def test_ocean_created_incident(self):
        comment = {
            "author": {"name": "gear-jep-notifier"},
            "body": "Ocean has created an incident for this issue.",
        }
        assert is_noise_comment(comment) is False

    def test_dces_automated_message(self):
        comment = {
            "author": {"name": "gear-dces-incmon-svc"},
            "body": "(Automated Message) 2541XK10FR worked on in 2 DO tickets",
        }
        assert is_noise_comment(comment) is False


# --- extract_comments ---

class TestExtractComments:
    def test_raw_format_with_filtering(self):
        fields = {
            "comment": {
                "comments": [
                    {
                        "id": "1",
                        "author": {"name": "gear-jep-notifier", "displayName": "JEP"},
                        "body": "Ocean has created an incident.",
                        "created": "2026-02-06T00:03:01.060+0000",
                    },
                    {
                        "id": "2",
                        "author": {"name": "gear-jep-notifier", "displayName": "JEP"},
                        "body": "Ocean Notification sent to:\n* Reece via push",
                        "created": "2026-02-06T00:03:06.000+0000",
                    },
                    {
                        "id": "3",
                        "author": {"name": "greg@oracle.com", "displayName": "Greg Parker"},
                        "body": "Fixed the issue.",
                        "created": "2026-02-06T02:12:57.418+0000",
                    },
                ],
                "total": 3,
            },
        }
        result = extract_comments(fields)
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[0]["author"] == "JEP"
        assert result[0]["created"] == "2026-02-06T00:03:01Z"
        assert result[1]["id"] == "3"
        assert result[1]["author"] == "Greg Parker"

    def test_list_format(self):
        """Handle already-flattened comment list."""
        fields = {
            "comment": [
                {
                    "id": "1",
                    "author": {"name": "john", "displayName": "John"},
                    "body": "Hello",
                    "created": "2026-01-01T00:00:00.000+0000",
                },
            ],
        }
        result = extract_comments(fields)
        assert len(result) == 1
        assert result[0]["author"] == "John"

    def test_empty(self):
        assert extract_comments({}) == []
        assert extract_comments({"comment": {"comments": []}}) == []

    def test_author_fallback_to_name(self):
        fields = {
            "comment": {
                "comments": [{
                    "id": "1",
                    "author": {"name": "john.doe"},
                    "body": "Test",
                    "created": "2026-01-01",
                }],
            },
        }
        result = extract_comments(fields)
        assert result[0]["author"] == "john.doe"


# --- normalize_issue ---

class TestNormalizeIssue:
    def test_full_issue(self):
        issue = {
            "id": "123",
            "self": "https://jira.example.com/rest/api/2/issue/123",
            "key": "DO-123",
            "expand": "...",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test ticket",
                "priority": {"name": "Medium"},
                "status": {"name": "Resolved"},
                "resolution": {"name": "Resolved"},
                "created": "2026-02-06T00:02:39.586+0000",
                "resolutiondate": "2026-02-06T02:13:12.051+0000",
                "updated": "2026-02-06T02:13:12.298+0000",
                "assignee": {"displayName": "Greg Parker"},
                "reporter": {"displayName": "Izamar Calderon"},
                "watches": {"watchCount": 5},
                "customfield_14606": [{"value": "AGA"}],
                "customfield_12605": {"value": "aga.ad1"},
                "customfield_12604": {"value": "aga4"},
                "customfield_10602": "GPU_MI355X_E6_R.01",
                "customfield_10104": "2541XK10FR",
                "labels": ["Compute", "RackSerial:2551ZA8062", "ORTANO"],
                "issuelinks": [],
                "description": "Test\u00a0description\r\n",
                "comment": {"comments": [], "total": 0},
            },
        }
        result = normalize_issue(issue)

        assert result["ticket"]["key"] == "DO-123"
        assert result["ticket"]["type"] == "Incident"
        assert result["status"]["current"] == "Resolved"
        assert result["status"]["created"] == "2026-02-06T00:02:39Z"
        assert result["people"]["assignee"] == "Greg Parker"
        assert result["location"]["region"] == "AGA"
        assert result["location"]["rack_serial"] == "2551ZA8062"
        assert result["labels"] == ["Compute"]
        assert "links" not in result  # empty links omitted
        assert result["description"] == "Test description"
        assert result["comments"] == []

    def test_no_fields(self):
        issue = {"id": "1", "key": "DO-1"}
        result = normalize_issue(issue)
        assert result["ticket"]["key"] == "DO-1"
        assert result["labels"] == []


# --- normalize_json ---

class TestNormalizeJson:
    def test_single_ticket(self):
        data = {
            "expand": "...",
            "key": "DO-1",
            "self": "https://...",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test",
                "priority": {"name": "High"},
                "status": {"name": "Open"},
                "labels": [],
                "comment": {"comments": []},
            },
        }
        result = normalize_json(data)
        assert "ticket" in result
        assert result["ticket"]["key"] == "DO-1"
        assert "expand" not in result
        assert "self" not in result

    def test_paginated(self):
        data = {
            "expand": "...",
            "startAt": 0,
            "maxResults": 100,
            "total": 1,
            "issues": [{
                "key": "DO-1",
                "fields": {
                    "project": {"key": "DO", "name": "DC Ops"},
                    "issuetype": {"name": "Incident"},
                    "summary": "Test",
                    "priority": {"name": "High"},
                    "status": {"name": "Open"},
                    "labels": [],
                    "comment": {"comments": []},
                },
            }],
        }
        result = normalize_json(data)
        assert "expand" not in result
        assert "startAt" not in result
        assert "maxResults" not in result
        assert result["total"] == 1
        assert result["issues"][0]["ticket"]["key"] == "DO-1"

    def test_unrecognized_format(self):
        data = {"something": "else"}
        assert normalize_json(data) == {"something": "else"}


# --- process_file ---

class TestProcessFile:
    def test_in_place(self, tmp_path):
        data = {
            "key": "DO-1",
            "id": "123",
            "self": "https://...",
            "expand": "...",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test ticket",
                "priority": {"name": "Medium"},
                "status": {"name": "Resolved"},
                "resolution": {"name": "Resolved"},
                "created": "2026-02-06T00:02:39.586+0000",
                "assignee": {"displayName": "Greg Parker"},
                "reporter": None,
                "labels": ["Compute", "ORTANO"],
                "description": "Hello\u00a0world",
                "comment": {"comments": [], "total": 0},
            },
        }
        f = tmp_path / "ticket.json"
        f.write_text(json.dumps(data))

        file_results = process_file(str(f), in_place=True)
        assert len(file_results) == 1
        out_path, orig, norm = file_results[0]

        result = json.loads(f.read_text())
        assert "ticket" in result
        assert result["ticket"]["key"] == "DO-1"
        assert result["labels"] == ["Compute"]
        assert result["description"] == "Hello world"
        assert result["people"]["assignee"] == "Greg Parker"
        assert result["people"]["reporter"] is None

    def test_output_dir(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        data = {
            "key": "DO-1",
            "id": "123",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test",
                "priority": {"name": "High"},
                "status": {"name": "Open"},
                "labels": [],
                "comment": {"comments": []},
            },
        }
        f = src / "ticket.json"
        f.write_text(json.dumps(data))

        file_results = process_file(str(f), output_dir=str(dst))
        assert len(file_results) == 1
        out_path, orig, norm = file_results[0]
        assert (dst / "ticket.json").exists()

        # Original unchanged
        original = json.loads(f.read_text())
        assert "fields" in original

    def test_size_reduction(self, tmp_path):
        data = {
            "key": "DO-1",
            "id": "123",
            "self": "https://very-long-url.example.com/rest/api/2/issue/12345",
            "expand": "operations,versionedRepresentations,editmeta",
            "fields": {
                "project": {"self": "...", "key": "DO", "name": "DC Ops", "avatarUrls": {}},
                "issuetype": {"self": "...", "name": "Incident", "iconUrl": "..."},
                "summary": "Test",
                "priority": {"self": "...", "name": "Medium", "iconUrl": "..."},
                "status": {"self": "...", "name": "Resolved", "iconUrl": "..."},
                "resolution": {"self": "...", "name": "Resolved"},
                "assignee": {
                    "self": "...", "displayName": "John", "avatarUrls": {},
                    "emailAddress": "j@x.com", "key": "USER1", "name": "john",
                },
                "reporter": {
                    "self": "...", "displayName": "Jane", "avatarUrls": {},
                    "emailAddress": "j@x.com", "key": "USER2", "name": "jane",
                },
                "watches": {"self": "...", "watchCount": 5},
                "votes": {"self": "...", "votes": 0},
                "worklog": {"worklogs": [], "total": 0},
                "created": "2026-02-06T00:02:39.586+0000",
                "customfield_10000": None,
                "customfield_10001": None,
                "labels": [],
                "comment": {"comments": [], "total": 0},
            },
        }
        f = tmp_path / "ticket.json"
        f.write_text(json.dumps(data))

        file_results = process_file(str(f), in_place=True)
        assert len(file_results) == 1
        _, orig, norm = file_results[0]
        assert norm < orig


# --- archive_existing ---

class TestArchiveExisting:
    def test_archives_with_force(self, tmp_path):
        out_dir = tmp_path / "cleaned"
        out_dir.mkdir()
        (out_dir / "page_0.json").write_text('{"issues": []}')
        (out_dir / "DO-123.json").write_text('{"key": "DO-123"}')

        archive_path = archive_existing(out_dir, force=True)

        assert archive_path is not None
        assert archive_path.endswith(".zip")
        assert Path(archive_path).exists()
        assert list(out_dir.glob("*.json")) == []

    def test_archives_with_user_yes(self, tmp_path, monkeypatch):
        out_dir = tmp_path / "cleaned"
        out_dir.mkdir()
        (out_dir / "page_0.json").write_text('{"issues": []}')

        monkeypatch.setattr("builtins.input", lambda _: "y")
        archive_path = archive_existing(out_dir)

        assert archive_path is not None
        assert list(out_dir.glob("*.json")) == []

    def test_aborts_with_user_no(self, tmp_path, monkeypatch):
        out_dir = tmp_path / "cleaned"
        out_dir.mkdir()
        (out_dir / "page_0.json").write_text('{"issues": []}')

        monkeypatch.setattr("builtins.input", lambda _: "n")
        with pytest.raises(SystemExit) as exc_info:
            archive_existing(out_dir)
        assert exc_info.value.code == 0
        assert len(list(out_dir.glob("*.json"))) == 1

    def test_no_json_files(self, tmp_path):
        out_dir = tmp_path / "cleaned"
        out_dir.mkdir()
        (out_dir / "readme.txt").write_text("not json")

        archive_path = archive_existing(out_dir)
        assert archive_path is None

    def test_dir_does_not_exist(self, tmp_path):
        out_dir = tmp_path / "nonexistent"
        archive_path = archive_existing(out_dir)
        assert archive_path is None


# --- extract_links edge cases ---

class TestExtractLinksEdgeCases:
    def test_skips_link_without_outward_or_inward(self):
        fields = {"issuelinks": [{"id": "1", "type": {"name": "Relates"}}]}
        assert extract_links(fields) == []


# --- extract_comments edge cases ---

class TestExtractCommentsEdgeCases:
    def test_non_dict_non_list_comment_field(self):
        assert extract_comments({"comment": "unexpected_string"}) == []

    def test_string_author(self):
        fields = {
            "comment": {
                "comments": [{
                    "id": "1",
                    "author": "plainuser",
                    "body": "hello",
                    "created": "2026-01-01T00:00:00.000+0000",
                }],
            },
        }
        result = extract_comments(fields)
        assert len(result) == 1
        assert result[0]["author"] == "plainuser"


# --- normalize_issue edge cases ---

class TestNormalizeIssueEdgeCases:
    def test_issue_with_links(self):
        issue = {
            "key": "DO-1", "id": "1",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test", "priority": {"name": "High"},
                "status": {"name": "Open"}, "labels": [],
                "comment": {"comments": []},
                "issuelinks": [{
                    "type": {"name": "Blocks", "outward": "blocks"},
                    "outwardIssue": {
                        "key": "DO-2",
                        "fields": {"summary": "Other", "status": {"name": "Open"}},
                    },
                }],
            },
        }
        result = normalize_issue(issue)
        assert "links" in result
        assert result["links"][0]["key"] == "DO-2"

    def test_issue_with_sla(self):
        issue = {
            "key": "DO-1", "id": "1",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test", "priority": {"name": "High"},
                "status": {"name": "Open"}, "labels": [],
                "comment": {"comments": []},
                "customfield_10003": {
                    "completedCycles": [{"elapsedTime": {"friendly": "5m"}}],
                },
            },
        }
        result = normalize_issue(issue)
        assert "sla" in result
        assert result["sla"]["time_to_first_response"] == "5m"


# --- process_file edge cases ---

MINIMAL_ISSUE = {
    "key": "DO-1", "id": "1",
    "fields": {
        "project": {"key": "DO", "name": "DC Ops"},
        "issuetype": {"name": "Incident"},
        "summary": "Test", "priority": {"name": "High"},
        "status": {"name": "Open"}, "labels": [],
        "comment": {"comments": []},
    },
}


class TestProcessFileEdgeCases:
    def test_paginated_split_with_output_dir(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        issue2 = {**MINIMAL_ISSUE, "key": "DO-2", "id": "2"}
        data = {"issues": [MINIMAL_ISSUE, issue2], "total": 2}
        f = src / "page_0.json"
        f.write_text(json.dumps(data))

        results = process_file(str(f), output_dir=str(dst))
        assert len(results) == 2
        assert (dst / "DO-1.json").exists()
        assert (dst / "DO-2.json").exists()
        # First entry has original size, second has 0
        assert results[0][1] > 0
        assert results[1][1] == 0

    def test_paginated_split_without_output_dir(self, tmp_path):
        issue2 = {**MINIMAL_ISSUE, "key": "DO-2", "id": "2"}
        data = {"issues": [MINIMAL_ISSUE, issue2], "total": 2}
        f = tmp_path / "page_0.json"
        f.write_text(json.dumps(data))

        results = process_file(str(f))
        assert len(results) == 2
        assert (tmp_path / "DO-1.json").exists()
        assert (tmp_path / "DO-2.json").exists()

    def test_no_output_dir_no_in_place(self, tmp_path):
        f = tmp_path / "ticket.json"
        f.write_text(json.dumps(MINIMAL_ISSUE))

        results = process_file(str(f))
        assert len(results) == 1
        out_path = results[0][0]
        assert out_path == str(f)
        result = json.loads(f.read_text())
        assert "ticket" in result

    def test_paginated_split_respects_allowed_ticket_keys(self, tmp_path):
        issue2 = {**MINIMAL_ISSUE, "key": "DO-2", "id": "2"}
        data = {"issues": [MINIMAL_ISSUE, issue2], "total": 2}
        f = tmp_path / "page_0.json"
        f.write_text(json.dumps(data))

        dst = tmp_path / "dst"
        results = process_file(
            str(f),
            output_dir=str(dst),
            allowed_ticket_keys={"DO-2"},
        )
        assert len(results) == 1
        assert (dst / "DO-2.json").exists()
        assert not (dst / "DO-1.json").exists()

    def test_single_ticket_respects_allowed_ticket_keys(self, tmp_path):
        f = tmp_path / "DO-1.json"
        f.write_text(json.dumps({**MINIMAL_ISSUE, "key": "DO-1"}))

        dst = tmp_path / "dst"
        results = process_file(
            str(f),
            output_dir=str(dst),
            allowed_ticket_keys={"DO-2"},
        )
        assert results == []
        assert not (dst / "DO-1.json").exists()


# --- main() ---

class TestMain:
    def _write_ticket(self, path):
        path.write_text(json.dumps(MINIMAL_ISSUE))

    def test_explicit_files_in_place(self, tmp_path):
        f = tmp_path / "ticket.json"
        self._write_ticket(f)

        normalize_tickets.main(["--in-place", str(f)])

        result = json.loads(f.read_text())
        assert "ticket" in result

    def test_explicit_files_with_output_dir(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        f = src / "ticket.json"
        self._write_ticket(f)

        normalize_tickets.main(["-o", str(dst), "--date", "2026-01-15", str(f)])

        out_dir = dst / "2026-01-15"
        assert (out_dir / "ticket.json").exists()

    def test_default_input_dir(self, tmp_path, monkeypatch):
        input_dir = tmp_path / "tickets-json"
        input_dir.mkdir()
        self._write_ticket(input_dir / "ticket.json")

        output_dir = tmp_path / "normalized"
        monkeypatch.setattr(normalize_tickets, "DEFAULT_INPUT_DIR", input_dir)
        monkeypatch.setattr(normalize_tickets, "DEFAULT_OUTPUT_DIR", output_dir)

        normalize_tickets.main([])

        # Output dir should contain a date-stamped subdirectory
        date_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(date_dirs) == 1
        assert (date_dirs[0] / "ticket.json").exists()

    def test_no_files_exits(self, tmp_path, monkeypatch):
        empty_dir = tmp_path / "empty-input"
        empty_dir.mkdir()
        monkeypatch.setattr(normalize_tickets, "DEFAULT_INPUT_DIR", empty_dir)

        with pytest.raises(SystemExit) as exc_info:
            normalize_tickets.main([])
        assert exc_info.value.code == 1

    def test_invalid_date_format_exits(self, tmp_path):
        f = tmp_path / "ticket.json"
        self._write_ticket(f)

        with pytest.raises(SystemExit):
            normalize_tickets.main(["--date", "not-a-date", str(f)])

    def test_archive_existing_with_yes(self, tmp_path, monkeypatch):
        input_dir = tmp_path / "src"
        input_dir.mkdir()
        self._write_ticket(input_dir / "ticket.json")

        output_base = tmp_path / "out"
        monkeypatch.setattr(normalize_tickets, "DEFAULT_OUTPUT_DIR", output_base)

        # First run creates output
        normalize_tickets.main(["-o", str(output_base), "--date", "2026-01-01", str(input_dir / "ticket.json")])
        out_dir = output_base / "2026-01-01"
        assert (out_dir / "ticket.json").exists()

        # Second run with -y archives and overwrites
        normalize_tickets.main(["-y", "-o", str(output_base), "--date", "2026-01-01", str(input_dir / "ticket.json")])
        assert (out_dir / "ticket.json").exists()

    def test_paginated_input_shows_split_stats(self, tmp_path, capsys):
        issue2 = {**MINIMAL_ISSUE, "key": "DO-2", "id": "2"}
        data = {"issues": [MINIMAL_ISSUE, issue2], "total": 2}
        f = tmp_path / "page_0.json"
        f.write_text(json.dumps(data))

        output_dir = tmp_path / "out"
        normalize_tickets.main(["-o", str(output_dir), "--date", "2026-01-01", str(f)])

        out = capsys.readouterr().out
        assert "2 ticket(s)" in out


# --- load_tickets_file (normalize version) ---

class TestLoadTicketsFile:
    def test_simple_keys(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\nHPC-456\n")
        result = load_tickets_file(str(f))
        assert result == {"DO-123", "HPC-456"}

    def test_skips_blanks_and_comments(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("# comment\n\nDO-123\n  \n")
        result = load_tickets_file(str(f))
        assert result == {"DO-123"}

    def test_deduplicates(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("DO-123\nDO-123\n")
        result = load_tickets_file(str(f))
        assert result == {"DO-123"}

    def test_accepts_browse_urls(self, tmp_path):
        f = tmp_path / "tickets.txt"
        url = "https://jira-sd.mc1.oracleiaas.com/browse/DO-123"
        f.write_text(f"{url}\nHPC-456\n")
        result = load_tickets_file(str(f))
        assert result == {"DO-123", "HPC-456"}

    def test_invalid_key_exits(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("not-valid\n")
        with pytest.raises(SystemExit) as exc_info:
            load_tickets_file(str(f))
        assert exc_info.value.code == 1

    def test_empty_file_exits(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("\n# comment\n")
        with pytest.raises(SystemExit) as exc_info:
            load_tickets_file(str(f))
        assert exc_info.value.code == 1

    def test_missing_file_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            load_tickets_file("/nonexistent/tickets.txt")
        assert exc_info.value.code == 1

    def test_strips_whitespace(self, tmp_path):
        f = tmp_path / "tickets.txt"
        f.write_text("  DO-123  \n\tHPC-456\t\n")
        result = load_tickets_file(str(f))
        assert result == {"DO-123", "HPC-456"}


# --- main() --tickets-file ---

class TestMainTicketsFile:
    def _write_ticket(self, path, key="DO-1"):
        data = {
            "key": key, "id": "1",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test", "priority": {"name": "High"},
                "status": {"name": "Open"}, "labels": [],
                "comment": {"comments": []},
            },
        }
        path.write_text(json.dumps(data))

    def test_filters_to_matching_tickets(self, tmp_path, monkeypatch):
        input_dir = tmp_path / "tickets-json"
        input_dir.mkdir()
        self._write_ticket(input_dir / "DO-1.json", "DO-1")
        self._write_ticket(input_dir / "DO-2.json", "DO-2")
        self._write_ticket(input_dir / "DO-3.json", "DO-3")

        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-1\nDO-3\n")

        output_dir = tmp_path / "output"
        monkeypatch.setattr(normalize_tickets, "DEFAULT_INPUT_DIR", input_dir)
        monkeypatch.setattr(normalize_tickets, "DEFAULT_OUTPUT_DIR", output_dir)

        normalize_tickets.main(["--tickets-file", str(tickets_file)])

        date_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(date_dirs) == 1
        output_files = list(date_dirs[0].glob("*.json"))
        output_stems = {f.stem for f in output_files}
        assert output_stems == {"DO-1", "DO-3"}

    def test_no_matching_tickets_exits(self, tmp_path, monkeypatch):
        input_dir = tmp_path / "tickets-json"
        input_dir.mkdir()
        self._write_ticket(input_dir / "DO-1.json", "DO-1")

        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-999\n")

        monkeypatch.setattr(normalize_tickets, "DEFAULT_INPUT_DIR", input_dir)

        with pytest.raises(SystemExit) as exc_info:
            normalize_tickets.main(["--tickets-file", str(tickets_file)])
        assert exc_info.value.code == 1

    def test_tickets_file_with_explicit_files(self, tmp_path):
        self._write_ticket(tmp_path / "DO-1.json", "DO-1")
        self._write_ticket(tmp_path / "DO-2.json", "DO-2")

        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-1\n")

        output_dir = tmp_path / "output"
        normalize_tickets.main([
            "--tickets-file", str(tickets_file),
            "-o", str(output_dir),
            "--date", "2026-01-01",
            str(tmp_path / "DO-1.json"),
            str(tmp_path / "DO-2.json"),
        ])

        out_dir = output_dir / "2026-01-01"
        output_files = list(out_dir.glob("*.json"))
        assert len(output_files) == 1
        assert output_files[0].stem == "DO-1"

    def test_printed_filter_summary(self, tmp_path, monkeypatch, capsys):
        input_dir = tmp_path / "tickets-json"
        input_dir.mkdir()
        self._write_ticket(input_dir / "DO-1.json", "DO-1")

        tickets_file = tmp_path / "tickets.txt"
        tickets_file.write_text("DO-1\n")

        output_dir = tmp_path / "output"
        monkeypatch.setattr(normalize_tickets, "DEFAULT_INPUT_DIR", input_dir)
        monkeypatch.setattr(normalize_tickets, "DEFAULT_OUTPUT_DIR", output_dir)

        normalize_tickets.main(["--tickets-file", str(tickets_file)])
        out = capsys.readouterr().out
        assert "Filtered to 1 file(s)" in out


class TestMainInputDir:
    def _write_ticket(self, path, key="DO-1"):
        data = {
            "key": key, "id": "1",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test", "priority": {"name": "High"},
                "status": {"name": "Open"}, "labels": [],
                "comment": {"comments": []},
            },
        }
        path.write_text(json.dumps(data))

    def test_input_dir_is_used_when_no_explicit_files(self, tmp_path):
        input_dir = tmp_path / "custom-input"
        input_dir.mkdir()
        self._write_ticket(input_dir / "DO-1.json", "DO-1")

        output_dir = tmp_path / "output"
        normalize_tickets.main([
            "--input-dir", str(input_dir),
            "-o", str(output_dir),
            "--date", "2026-01-01",
        ])

        out_dir = output_dir / "2026-01-01"
        output_files = list(out_dir.glob("*.json"))
        assert len(output_files) == 1
        assert output_files[0].stem == "DO-1"

    def test_input_dir_missing_json_exits(self, tmp_path):
        empty_input_dir = tmp_path / "empty-input"
        empty_input_dir.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            normalize_tickets.main(["--input-dir", str(empty_input_dir)])
        assert exc_info.value.code == 1


class TestMainRandomSample:
    def _write_ticket(self, path, key):
        data = {
            "key": key, "id": "1",
            "fields": {
                "project": {"key": "DO", "name": "DC Ops"},
                "issuetype": {"name": "Incident"},
                "summary": "Test", "priority": {"name": "High"},
                "status": {"name": "Open"}, "labels": [],
                "comment": {"comments": []},
            },
        }
        path.write_text(json.dumps(data))

    def test_random_sample_selects_n_tickets_from_paginated_file(self, tmp_path, monkeypatch):
        input_dir = tmp_path / "tickets-json"
        input_dir.mkdir()
        issue1 = {**MINIMAL_ISSUE, "key": "DO-1", "id": "1"}
        issue2 = {**MINIMAL_ISSUE, "key": "DO-2", "id": "2"}
        issue3 = {**MINIMAL_ISSUE, "key": "DO-3", "id": "3"}
        paginated = {"issues": [issue1, issue2, issue3], "total": 3}
        (input_dir / "limited-tickets.json").write_text(json.dumps(paginated))

        output_dir = tmp_path / "output"

        def fake_sample(seq, n):
            assert n == 2
            return ["DO-3", "DO-1"]

        monkeypatch.setattr(normalize_tickets.random, "sample", fake_sample)
        normalize_tickets.main([
            "--input-dir", str(input_dir),
            "--random-sample", "2",
            "-o", str(output_dir),
            "--date", "2026-01-01",
        ])

        out_dir = output_dir / "2026-01-01"
        output_stems = {f.stem for f in out_dir.glob("*.json")}
        assert output_stems == {"DO-1", "DO-3"}

    def test_random_sample_rejects_non_positive(self, tmp_path):
        f = tmp_path / "ticket.json"
        self._write_ticket(f, "DO-1")
        with pytest.raises(SystemExit):
            normalize_tickets.main([str(f), "--random-sample", "0"])

    def test_random_sample_rejects_larger_than_available(self, tmp_path):
        input_dir = tmp_path / "tickets-json"
        input_dir.mkdir()
        issue1 = {**MINIMAL_ISSUE, "key": "DO-1", "id": "1"}
        issue2 = {**MINIMAL_ISSUE, "key": "DO-2", "id": "2"}
        paginated = {"issues": [issue1, issue2], "total": 2}
        (input_dir / "limited-tickets.json").write_text(json.dumps(paginated))

        with pytest.raises(SystemExit):
            normalize_tickets.main([
                "--input-dir", str(input_dir),
                "--random-sample", "3",
            ])


class TestCollectTicketKeys:
    def test_collects_from_single_and_paginated_files(self, tmp_path):
        single = tmp_path / "DO-1.json"
        single.write_text(json.dumps({**MINIMAL_ISSUE, "key": "DO-1"}))

        issue2 = {**MINIMAL_ISSUE, "key": "DO-2", "id": "2"}
        issue3 = {**MINIMAL_ISSUE, "key": "DO-3", "id": "3"}
        paginated = tmp_path / "page_0.json"
        paginated.write_text(json.dumps({"issues": [issue2, issue3], "total": 2}))

        keys = collect_ticket_keys([str(single), str(paginated)])
        assert keys == {"DO-1", "DO-2", "DO-3"}
