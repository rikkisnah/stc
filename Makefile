.PHONY: help test test-get_tickets test-normalize_tickets fmt lint

help:
	@echo "Targets:"
	@echo "  test                 Run all tests (explicit file list)"
	@echo "  test_get_tickets      Run get_tickets unit tests"
	@echo "  test_normalize_tickets Run normalize_tickets unit tests"

test:
	uv run pytest --cov=scripts --cov-report=term-missing -q scripts/test_get_tickets.py scripts/test_normalize_tickets.py

test-get_tickets:
	uv run pytest --cov=scripts/get_tickets.py --cov-report=term-missing -q scripts/test_get_tickets.py

test-normalize_tickets:
	uv run pytest -q scripts/test_normalize_tickets.py
