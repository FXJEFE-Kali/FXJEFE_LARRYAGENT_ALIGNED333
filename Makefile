# ============================================================================
# Agent Larry — Makefile
# ============================================================================
# Usage: make <target>
# ============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

# Docker image name
IMAGE := larry-agent:latest

# ── Help ────────────────────────────────────────────────────────────────────
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Local (no Docker) ──────────────────────────────────────────────────────
.PHONY: agent dashboard paths status test

agent: ## Launch agent CLI (local Python)
	./run_larry.sh agent

dashboard: ## Launch dashboard web UI (local Python)
	./run_larry.sh dashboard

paths: ## Print resolved project paths
	./run_larry.sh paths

status: ## Show running services, GPU, and Ollama status
	./run_larry.sh status

test: ## Run smoke tests
	python -m pytest tests/ -v --tb=short

# ── Docker ──────────────────────────────────────────────────────────────────
.PHONY: build up down gpu-test logs shell

build: ## Build the Docker image (multi-stage)
	docker build -t $(IMAGE) .

up: ## Start Ollama + agent (GPU-enabled, interactive)
	docker compose up -d ollama
	@echo "Waiting for Ollama to be healthy..."
	@docker compose exec ollama ollama list >/dev/null 2>&1 || sleep 5
	docker compose run --rm -it agent

down: ## Stop all services
	docker compose down

gpu-test: ## Verify GPU passthrough in Docker
	docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi

logs: ## Tail docker compose logs
	docker compose logs -f --tail=50

shell: ## Open a shell in the agent container
	docker compose run --rm -it --entrypoint /bin/bash agent

# ── Docker Profiles ─────────────────────────────────────────────────────────
.PHONY: up-tiny up-speed up-dashboard up-full

up-tiny: ## Start with TINY profile (MacBook M1, 8 GB)
	docker compose --profile tiny up -d ollama-tiny
	docker compose run --rm -it agent

up-speed: ## Start with SPEED profile (ThinkPad, 16 GB)
	docker compose --profile speed up -d ollama-speed
	docker compose run --rm -it agent

up-dashboard: ## Start dashboard web UI via Docker
	docker compose --profile dashboard up -d

up-full: ## Start all services (dashboard + telegram + n8n + postgres)
	docker compose --profile full up -d

# ── Model Management ───────────────────────────────────────────────────────
.PHONY: models-tiny models-speed models-accuracy

models-tiny: ## Pull models for TINY profile (M1 8 GB)
	ollama pull llama3.2:1b
	ollama pull qwen2.5-coder:1.5b
	ollama pull nomic-embed-text

models-speed: ## Pull models for SPEED profile (ThinkPad 16 GB)
	ollama pull llama3.2:3b
	ollama pull qwen2.5-coder:3b
	ollama pull nomic-embed-text

models-accuracy: ## Pull models for ACCURACY profile (Ubuntu 64 GB + RTX 4060)
	ollama pull qwen3-coder:30b
	ollama pull dolphin-mixtral:8x7b
	ollama pull qwen2.5:7b-instruct
	ollama pull nomic-embed-text

# ── USB Deploy ──────────────────────────────────────────────────────────────
.PHONY: deploy-usb

deploy-usb: ## Sync project to LocalLarry- and casper-rw USBs
	@echo "Syncing to LocalLarry-..."
	rsync -av --exclude-from=.dockerignore --exclude='.git/' \
		./ /media/linuxlarry/LocalLarry-/Agent-Larry/
	@echo "Syncing to casper-rw..."
	sudo rsync -av --exclude-from=.dockerignore --exclude='.git/' \
		./ /media/linuxlarry/casper-rw/upper/home/ubuntu/Agent-Larry/
	@echo "USB sync complete."

# ── Maintenance ─────────────────────────────────────────────────────────────
.PHONY: clean validate

clean: ## Remove __pycache__, .pyc, logs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf logs/*.log 2>/dev/null || true

validate: ## Validate configs and imports
	python -c "from larry_paths import BASE_DIR, __version__; print(f'larry_paths OK (v{__version__})')"
	python -c "from mcp_servers import registry; print(f'MCP servers: {len(registry)} loaded — {list(registry.keys())}')"
	docker compose config --quiet && echo "docker-compose.yml: valid"
