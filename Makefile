.PHONY: install run-batch lint test

install:
	pip install -e ".[dev,api]"

run-batch:
	python -m fraud_service.batch

lint:
	ruff check src tests

test:
	python -m pytest -v

serve:
	fastapi dev src/fraud_service/api/app.py
