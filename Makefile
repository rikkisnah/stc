.PHONY: help test test-get_tickets test-normalize_tickets test-get_tickets_cli test-rule_engine_categorize test-run_training run-training run-training-inline test-csv_jql_transform ui-e2e-setup ui-quick ui-e2e ui-clean-cache ui-runtime-smoke ui-verify test-ml_classifier test-ml_train ml-train ml-categorize sync-agent-guides check-agent-guides clean fmt lint

PROMPT ?= prompts/update-rule-engine-prompt.md
CODEX_TIMEOUT ?= 180
PROMPT_TEXT ?=
COV_FAIL_UNDER ?= 100
UI_SMOKE_PORT ?= 3017
UI_SMOKE_TIMEOUT ?= 120
UI_SMOKE_MODE ?= dev

help:
	@echo "Targets:"
	@echo "  test                    Run all tests"
	@echo "  test-get_tickets        Run get_tickets unit tests"
	@echo "  test-normalize_tickets  Run normalize_tickets unit tests"
	@echo "  test-get_tickets_cli    Run get_tickets CLI integration tests"
	@echo "  test-run_training       Run run_training.py unit tests"
	@echo "  ui-e2e-setup            Install wireframe-ui deps and Playwright Chromium"
	@echo "  ui-quick                Fast UX checks (unit tests + typecheck)"
	@echo "  ui-e2e                  Run wireframe-ui Playwright hydration E2E test"
	@echo "  ui-clean-cache          Remove wireframe-ui Next.js and Playwright caches"
	@echo "  ui-runtime-smoke        Start Next server and fail on runtime/chunk errors (UI_SMOKE_MODE=dev|start)"
	@echo "  ui-verify               Enforced UI gate (unit + types + build + runtime smoke + e2e)"
	@echo "  run-training            Run run_training.py Step 1"
	@echo "  run-training-inline     Run run_training.py with inline --prompt"
	@echo "  test-ml_classifier      Run ml_classifier unit tests"
	@echo "  test-ml_train           Run ml_train unit tests"
	@echo "  ml-train                Train local ML classifier"
	@echo "  ml-categorize           Categorize tickets with ML fallback"
	@echo "  sync-agent-guides       Copy AGENTS.md into CLAUDE.md"
	@echo "  check-agent-guides      Check AGENTS.md and CLAUDE.md are in sync"
	@echo "  clean                   Remove zip archives, tickets-json/, and normalized-tickets/"

test:
	uv run pytest --cov=scripts --cov-report=term-missing --cov-fail-under=$(COV_FAIL_UNDER) -q scripts/tests/

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
	cd wireframe-ui && npx playwright install chromium

ui-quick:
	cd wireframe-ui && npm test -- --runTestsByPath __tests__/page.test.tsx
	cd wireframe-ui && npx tsc --noEmit

ui-e2e: ui-e2e-setup
	cd wireframe-ui && npm run test:e2e

ui-clean-cache:
	rm -rf wireframe-ui/.next
	rm -rf wireframe-ui/test-results
	rm -rf wireframe-ui/playwright-report

ui-runtime-smoke:
	@set -eu; \
	HTML_FILE=$$(mktemp /tmp/stc-ui-smoke-XXXX.html); \
	LOG_FILE=$$(mktemp /tmp/stc-ui-dev-XXXX.log); \
	PORT=$(UI_SMOKE_PORT); \
	MODE=$(UI_SMOKE_MODE); \
	TIMEOUT=$(UI_SMOKE_TIMEOUT); \
	cd wireframe-ui; \
	if [ "$$MODE" = "dev" ]; then \
		rm -rf .next; \
		npm run dev -- --port $$PORT >$$LOG_FILE 2>&1 & \
	elif [ "$$MODE" = "start" ]; then \
		npm run start -- --port $$PORT >$$LOG_FILE 2>&1 & \
	else \
		echo "ui-runtime-smoke: unsupported UI_SMOKE_MODE=$$MODE (use dev or start)"; \
		exit 1; \
	fi; \
	DEV_PID=$$!; \
	trap 'kill $$DEV_PID >/dev/null 2>&1 || true; wait $$DEV_PID >/dev/null 2>&1 || true; rm -f $$HTML_FILE $$LOG_FILE' EXIT INT TERM; \
	READY=0; \
	for i in $$(seq 1 $$TIMEOUT); do \
		if ! kill -0 $$DEV_PID >/dev/null 2>&1; then \
			echo "ui-runtime-smoke: $$MODE server exited before readiness check completed"; \
			tail -n 120 $$LOG_FILE || true; \
			exit 1; \
		fi; \
		if curl -fsS --connect-timeout 1 --max-time 1 "http://127.0.0.1:$$PORT" >$$HTML_FILE 2>/dev/null; then READY=1; break; fi; \
		sleep 1; \
	done; \
	if [ "$$READY" -ne 1 ]; then \
		echo "ui-runtime-smoke: $$MODE server did not become ready on port $$PORT"; \
		tail -n 120 $$LOG_FILE || true; \
		exit 1; \
	fi; \
	if grep -Eiq "Runtime Error|Cannot find module|Module not found" $$HTML_FILE; then \
		echo "ui-runtime-smoke: runtime error detected in page HTML"; \
		sed -n '1,120p' $$HTML_FILE; \
		tail -n 120 $$LOG_FILE || true; \
		exit 1; \
	fi; \
	echo "ui-runtime-smoke: passed"

ui-verify: ui-e2e-setup
	cd wireframe-ui && npm test
	cd wireframe-ui && npx tsc --noEmit
	$(MAKE) ui-clean-cache
	cd wireframe-ui && npm run build
	$(MAKE) UI_SMOKE_MODE=start ui-runtime-smoke
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

sync-agent-guides:
	python3 scripts/sync_agents_claude.py

check-agent-guides:
	python3 scripts/sync_agents_claude.py --check

clean:
	rm -f scripts/*.zip
	rm -rf scripts/tickets-json/
	rm -rf scripts/normalized-tickets/
	rm -rf scripts/analysis/
