SHELL := /usr/bin/env bash

.PHONY: dev test build deploy-akash fmt lint

export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

fmt:
	black app || true
	isort app || true
	golangci-lint run ./gofr/... || true

lint:
	flake8 app || true
	golangci-lint run ./gofr/... || true

dev:
	docker compose --profile cpu up --build

test:
	pytest -q
	cd gofr && go test ./...

build:
	docker build -t legal-simplifier-flask:local -f Dockerfile .
	docker build -t legal-simplifier-gofr:local -f gofr/Dockerfile gofr

deploy-akash:
	@echo "Use akash.yaml with Akash Console or akash CLI. Refer README for steps."
