.PHONY: help test test-get-tickets test-normalize-tickets fmt lint

help:
	@echo "Targets:"
	@echo "  test                 Run all tests (explicit file list)"
	@echo "  test-get-tickets      Run get-tickets unit tests"
	@echo "  test-normalize-tickets Run normalize-tickets unit tests"

test:
	uv run pytest -q scripts/test-get-tickets.py scripts/test-normalize-tickets.py

test-get-tickets:
	uv run pytest -q scripts/test-get-tickets.py

test-normalize-tickets:
	uv run pytest -q scripts/test-normalize-tickets.py

