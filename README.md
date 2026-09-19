# Raqib Fraud Detection Service — Lab 1 Starter (SDA-AIE-113)

## What this is

This is the **starting point** for Lab 1 — "Refactor the Notebook into a
Clean Package." It is intentionally incomplete: the legacy notebook and
its data/model artifacts are here, and the `src/fraud_service/` package
layout is scaffolded with `TODO` stubs matching the target architecture
from `INSTRUCTOR_PACKAGE.md` (Module 1). This is NOT the reference
solution — you build that during the lab.

## Layout

```
fraud-service/
├── pyproject.toml            # deps + tool config (already filled in)
├── Makefile                  # make install / run-batch / lint / test
├── configs/settings.example.env
├── notebooks/
│   └── fraud_exploration.ipynb   # run this FIRST — the messy baseline (6 SMELLs)
├── data/
│   └── transactions_sample.csv   # 5,000 synthetic SAR transactions
├── models/
│   └── fraud_model.joblib        # {"pipeline": ..., "version": "v3.2.0"}
├── src/fraud_service/
│   ├── domain/
│   │   ├── entities.py       # TODO: Transaction, FeatureVector
│   │   └── policies.py       # TODO: decide()
│   ├── service/
│   │   ├── interfaces.py     # TODO: Model protocol
│   │   └── scorer.py         # TODO: FraudScorer
│   ├── adapters/
│   │   └── sklearn_model.py  # TODO: SklearnModel (only file allowed to import sklearn/joblib)
│   ├── config.py             # TODO: Settings (pydantic-settings)
│   └── batch.py              # TODO: composition root — wires everything together
└── tests/
    ├── unit/test_policies.py       # TODO once policies.py exists
    ├── integration/                # for Lab 2 (API tests)
    └── behavioural/                # for Lab 4
```

## Lab 1 — step by step (50 min)

1. **(5 min)** `jupyter notebook notebooks/fraud_exploration.ipynb` — run
   top to bottom, read the `# SMELL` comments.
2. **(10 min)** `pip install -e ".[dev,api]"` — installs this package in
   editable mode (src-layout: tests import the *installed* package, not
   the repo folder — this is what makes `pip install -e .` non-negotiable).
3. **(15 min)** Fill in `domain/entities.py`, `domain/policies.py`,
   `service/interfaces.py`, `service/scorer.py`, `adapters/sklearn_model.py`
   per the `TODO` blocks in each file.
4. **(10 min)** Fill in `batch.py`, then run `make run-batch`.
5. **(5 min)** `make lint` (ruff) — fix anything it flags.
6. **(5 min)** `git add -A && git commit -m "refactor: extract clean architecture layers from notebook"`

## Expected output

```
$ make run-batch
Loaded model version v3.2.0 in 0.7Xs
Scored 5000 transactions -> scored.csv  (block: ~35-55, review: ~200-230, allow: ~4730-4760)
$ make lint
All checks passed!
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: fraud_service` | Package not installed | `pip install -e .` |
| Circular import domain ⇄ service | An entity imports the scorer | Dependencies point inward only |
| Different scores vs notebook | Feature logic drifted during the move | Diff `to_features()` output against notebook Cell 4 for a few sample rows |
