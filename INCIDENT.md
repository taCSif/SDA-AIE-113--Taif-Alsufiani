# Incident: GitHub token committed to `configs/settings.example.env`

- **Date:** 2026-09-22
- **Severity:** Low (drill exercise, fake credential; contained before it
  reached this repository's shared history)
- **Status:** Resolved

## Summary

While wiring `FRAUD_GITHUB_TOKEN` into `Settings` as a `SecretStr`, the
drill scenario is: a developer pastes a real-looking GitHub personal
access token (`ghp_...`) directly into `configs/settings.example.env`
"for local testing" and commits it. `settings.example.env` is a
template meant to be copied to a git-ignored `.env` — real values
should never land in the tracked copy.

This repository (`taCSif/SDA-AIE-113--Taif-Alsufiani`) is **public on
GitHub**, where push protection and secret scanning are active by
default — pushing a commit containing a token-shaped string is either
blocked outright or immediately flagged. So the leak-and-detect part of
this drill was run once, deliberately, in a disposable local sandbox
clone of this exact codebase (never pushed anywhere), to prove the
detection and cleanup mechanics for real before touching the shared
repo at all. Only the already-remediated result — the fix below — was
ever committed here.

## Detection (sandbox run)

`gitleaks detect` against the sandbox clone's history, right after the
planted-token commit landed there:

```
$ docker run --rm -v "$(pwd -W)":/repo -w /repo zricethezav/gitleaks:latest \
    detect --source=/repo -v --redact

Finding:     FRAUD_GITHUB_TOKEN=REDACTED
Secret:      REDACTED
RuleID:      github-pat
Entropy:     4.815311
File:        configs/settings.example.env
Line:        5
Commit:      3ebf096c6ac7a0a2f2d0b1b3b116206dcceb3092
...
leaks found: 1
```

Caught immediately by gitleaks' built-in `github-pat` rule, which
matches the `ghp_` + 36-character token shape.

## Response

1. **Rotate first, always — before touching history.** A commit's
   existence isn't what makes a leaked credential dangerous; a token is
   compromised the moment it's written to disk in a git object, because
   it may already have been scraped by a CI runner, a fork, a clone, or
   a secrets scanner before anyone notices. Rewriting history does not
   retroactively un-expose it. In a real incident the very first action
   — before any git surgery — is to revoke the token at the source
   (github.com/settings/tokens) and issue a new one. This token was a
   drill fixture, not a real credential, so there was nothing to revoke
   upstream; had it been real, revocation would have happened here,
   first, before step 2.
2. **Clean the history.** The sandbox clone was local-only, so the
   safest and simplest fix there was to make the leak commit never have
   existed rather than bury it under a revert: `git reset --soft
   HEAD~1` un-committed it (staging its changes), the token line was
   removed, and the fix was committed in its place — `git log` shows no
   trace of the value, confirmed by a clean re-scan. **This repository
   never had the leak commit at all**: only that already-clean end
   state was ported over and committed here. (Had a real secret ever
   reached a *shared, already-pushed* history — this repo, or the
   sandbox if it had a remote — `git filter-repo`/BFG plus a
   coordinated force-push and a notice to every clone owner would be
   required instead of a simple reset; force-pushing a public,
   graded repo is exactly the kind of action that needs a human
   decision first, which is the other reason the drill stayed in the
   sandbox.)
3. **Fix via env, not code.** The token is read exclusively through
   `Settings.github_token: SecretStr`, sourced from the
   `FRAUD_GITHUB_TOKEN` environment variable
   ([config.py](src/fraud_service/config.py)) — never hardcoded, never
   given a literal default. `configs/settings.example.env` keeps the
   variable name documented but commented out with a placeholder, so
   the template stays useful without ever holding a real value.
4. **Verified masking.** Even if a real token is set and something logs
   it by mistake, `logging_setup.mask_secrets`
   ([logging_setup.py](src/fraud_service/logging_setup.py)) redacts it
   before it reaches stdout — by field name (`token`, `password`,
   `secret`, `api_key`, `authorization`) and by shape (`ghp_...` and
   similar patterns), even mid-sentence in a free-text message. Proven
   live through the real configured pipeline (not just the unit test)
   with a fake token: both `log.info("...", token=...)` and a token
   embedded in a free-text message came back as `***MASKED***`, never
   the raw value. See `tests/unit/test_logging_setup.py` and
   `tests/unit/test_config.py` (`test_github_token_is_masked_in_repr`)
   for the permanent regression coverage.
5. **Re-scanned.** `gitleaks detect` against the sandbox's cleaned
   history reports `no leaks found`; this repository was never exposed
   in the first place.

## Prevention

- `SecretStr` + `mask_secrets` are defense in depth, not the primary
  control — the primary control is that a filled-in `.env` never gets
  staged in the first place (`.env` is already git-ignored;
  `settings.example.env` stays a template with no real values).
- GitHub's own push protection on this public repo is a real backstop
  too, but it shouldn't be the *only* one — it only fires at push time,
  not at commit time, and only for patterns it recognizes.
- Consider adding a `gitleaks detect` step to CI
  (`.github/workflows/ci.yml`) and/or a local pre-commit hook, so a
  future slip is caught before the commit even lands, not just before
  it's shared.
