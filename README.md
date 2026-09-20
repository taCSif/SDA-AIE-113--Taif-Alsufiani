# Raqib Fraud Detection Service — Lab 1 (SDA-AIE-113)

**Trainee:** Taif Alsufiani — [@taCSif](https://github.com/taCSif)
**Lab:** 1 — Refactor the Notebook into a Clean Package
**Status:** complete — `make run-batch` green, `make lint` clean, 7 tests passing

## What this is

My solution for Lab 1. The legacy exploration notebook
(`notebooks/fraud_exploration.ipynb` — six deliberate `# SMELL` defects)
is refactored into a clean-architecture package under `src/fraud_service/`,
with dependencies pointing inward only: `domain` imports nothing but
stdlib + pydantic, and `adapters/sklearn_model.py` is the only module
allowed to touch sklearn or joblib.

The untouched starting point is preserved on the `lab1-start` branch, so
the whole refactor is reviewable as one diff:
[`lab1-start...main`](../../compare/lab1-start...main)

### Note on the model artifact

The shipped `models/fraud_model.joblib` was pickled by scikit-learn 1.8.0
and cannot predict under the 1.7.2 installed on this machine —
`predict_proba` raises `AttributeError: 'LogisticRegression' object has
no attribute 'multi_class'`. The notebook's `except Exception` (SMELL 6)
swallowed that failure and reported a clean run scoring 100% `allow` at
probability 0.0. The artifact was regenerated with
`scripts/generate_baseline_assets.py`; that script is deterministic, so
`data/transactions_sample.csv` is unchanged.

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
python -m fraud_service.batch
Loaded model version v3.2.0 in 6.40s
Scored 5000 transactions in 22.30s -> scored.csv  (block: 55, review: 199, allow: 4746)

$ make lint
ruff check src tests
All checks passed!

$ make test
7 passed
```

`to_features()` was verified bit-for-bit against the notebook's Cell 3
across all 5,000 rows (0 differing elements, 0 decision mismatches).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: fraud_service` | Package not installed | `pip install -e .` |
| Circular import domain ⇄ service | An entity imports the scorer | Dependencies point inward only |
| Different scores vs notebook | Feature logic drifted during the move | Diff `to_features()` output against notebook Cell 4 for a few sample rows |
| Notebook scores 100% `allow`, all probabilities `0.0` | `models/fraud_model.joblib` was pickled by a newer scikit-learn than the one installed; `predict_proba` raises `AttributeError: 'LogisticRegression' object has no attribute 'multi_class'`, and SMELL 6 swallows it | Regenerate the artifact against your local sklearn: `python scripts/generate_baseline_assets.py` (deterministic — the CSV comes out byte-identical) |
| `requires a different Python` on install | `requires-python` floor above your interpreter | The course spec targets Python 3.12+; this checkout is pinned to `>=3.11` to match the lab machine. Raise it once 3.12 is available. |
