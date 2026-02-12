.PHONY: help test test-get_tickets test-normalize_tickets test-get_tickets_cli test-rule_engine_categorize test-csv_jql_transform clean fmt lint

help:
	@echo "Targets:"
	@echo "  test                    Run all tests"
	@echo "  test-get_tickets        Run get_tickets unit tests"
	@echo "  test-normalize_tickets  Run normalize_tickets unit tests"
	@echo "  test-get_tickets_cli    Run get_tickets CLI integration tests"
	@echo "  clean                   Remove zip archives, tickets-json/, and normalized-tickets/"

test:
	uv run pytest --cov=scripts --cov-report=term-missing -q scripts/tests/

test-get_tickets:
	uv run pytest --cov=scripts --cov-report=term-missing -q scripts/tests/test_get_tickets.py

test-normalize_tickets:
	uv run pytest -q scripts/tests/test_normalize_tickets.py

test-get_tickets_cli:
	uv run pytest -q scripts/tests/test_get_tickets_cli.py

test-rule_engine_categorize:
	uv run pytest --cov=scripts --cov-report=term-missing -q scripts/tests/test_rule_engine_categorize.py

test-csv_jql_transform:
	uv run pytest --cov=scripts --cov-report=term-missing -q scripts/tests/test_csv_jql_transform.py

clean:
	rm -f scripts/*.zip
	rm -rf scripts/tickets-json/
	rm -rf scripts/normalized-tickets/
