"""TODO (Lab 4, Step 1 — ~10 min):
Fixtures shared by every test in this suite.

Write:
- ConstantModel — a test double standing in for sklearn (implements
  the same Model protocol as SklearnModel: just predict_proba).
- client_factory — builds a FastAPI app with the /predict scorer
  dependency overridden to inject a ConstantModel at whatever
  probability the test wants.
- real_model — loads the REAL model from disk exactly once for the
  whole test session (scope="session" — this is the single most
  important line in this file; without it, the behavioural suite
  reloads the model from disk on every test).
- sample_txn — a ready-made valid Transaction for tests to reuse.

See the Day 2 Lab Guide, Lab 4 Step 1, for the full suggested shape.
"""

# TODO: implement ConstantModel, client_factory, real_model, sample_txn.
