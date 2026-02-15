.PHONY: help test test-get_tickets test-normalize_tickets test-get_tickets_cli test-rule_engine_categorize test-run_training run-training run-training-inline test-csv_jql_transform ui-e2e-setup ui-e2e test-ml_classifier test-ml_train ml-train ml-categorize clean fmt lint

PROMPT ?= prompts/update-rule-engine-prompt.md
CODEX_TIMEOUT ?= 180
PROMPT_TEXT ?=

help:
	@echo "Targets:"
	@echo "  test                    Run all tests"
	@echo "  test-get_tickets        Run get_tickets unit tests"
	@echo "  test-normalize_tickets  Run normalize_tickets unit tests"
	@echo "  test-get_tickets_cli    Run get_tickets CLI integration tests"
	@echo "  test-run_training       Run run_training.py unit tests"
	@echo "  ui-e2e-setup            Install wireframe-ui deps and Playwright Chromium"
	@echo "  ui-e2e                  Run wireframe-ui Playwright hydration E2E test"
	@echo "  run-training            Run run_training.py Step 1"
	@echo "  run-training-inline     Run run_training.py with inline --prompt"
	@echo "  test-ml_classifier      Run ml_classifier unit tests"
	@echo "  test-ml_train           Run ml_train unit tests"
	@echo "  ml-train                Train local ML classifier"
	@echo "  ml-categorize           Categorize tickets with ML fallback"
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

test-run_training:
	uv run pytest -q scripts/tests/test_run_training.py

run-training:
	uv run python scripts/run_training.py \
		--tickets-categorized scripts/analysis/tickets-categorized.csv \
		--rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
		--prompt-file $(PROMPT) \
		--codex-timeout $(CODEX_TIMEOUT)

run-training-inline:
	@if [ -z "$(PROMPT_TEXT)" ]; then \
		echo "Usage: make run-training-inline PROMPT_TEXT='your prompt text' [CODEX_TIMEOUT=SECONDS]"; \
		exit 1; \
	fi
	uv run python scripts/run_training.py \
		--tickets-categorized scripts/analysis/tickets-categorized.csv \
		--rules-engine-file scripts/trained-data/golden-rules-engine/rule-engine.csv \
		--prompt "$(PROMPT_TEXT)" \
		--codex-timeout $(CODEX_TIMEOUT)

test-csv_jql_transform:
	uv run pytest --cov=scripts --cov-report=term-missing -q scripts/tests/test_csv_jql_transform.py

ui-e2e-setup:
	cd wireframe-ui && npm install
	cd wireframe-ui && npm install -D @playwright/test
	cd wireframe-ui && npx playwright install chromium

ui-e2e: ui-e2e-setup
	cd wireframe-ui && npm run test:e2e

test-ml_classifier:
	uv run pytest --cov=ml_classifier --cov-report=term-missing -q scripts/tests/test_ml_classifier.py

test-ml_train:
	uv run pytest --cov=ml_train --cov-report=term-missing -q scripts/tests/test_ml_train.py

ml-train:
	@if [ ! -f scripts/trained-data/ml-training-data.csv ]; then \
		echo "Initializing training data from template..."; \
		cp templates/ml-training-data.csv scripts/trained-data/ml-training-data.csv; \
	fi
	uv run python scripts/ml_train.py \
		--training-data scripts/trained-data/ml-training-data.csv \
		--tickets-categorized scripts/analysis/tickets-categorized.csv \
		$(if $(wildcard scripts/normalized-tickets/),--tickets-dir scripts/normalized-tickets/$$(ls scripts/normalized-tickets/ | sort | tail -1))

ml-categorize:
	uv run python scripts/rule_engine_categorize.py \
		--ml-model scripts/trained-data/ml-model/classifier.joblib \
		--ml-category-map scripts/trained-data/ml-model/category_map.json

clean:
	rm -f scripts/*.zip
	rm -rf scripts/tickets-json/
	rm -rf scripts/normalized-tickets/
