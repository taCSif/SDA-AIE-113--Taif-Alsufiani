.PHONY: install run-batch lint test

install:
	pip install -e ".[dev,api]"

# TODO (Lab 1, step 4): implement src/fraud_service/batch.py first —
# it should read data/transactions_sample.csv, score every row through
# FraudScorer, and write scored.csv. Then this target will work.
run-batch:
	python -m fraud_service.batch

lint:
	ruff check src tests

test:
	pytest -v
