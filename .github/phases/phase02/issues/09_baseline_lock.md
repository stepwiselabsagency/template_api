## 🎯 Goal
Create a locked baseline + inventory of Phase 01 so Phase 02 restructuring is safe.

## 📦 In Scope
- Add PHASE1 baseline doc listing current endpoints, scripts, invariants
- Add inventory doc explaining why major modules exist + deletion candidates
- Add `make verify-baseline` that runs fmt/lint/test and prints verifier guidance

## 🚫 Out of Scope
- No runtime behavior changes
- No route removal
- No refactor

## 📁 Deliverables
- backend/docs/PHASE1_BASELINE.md
- backend/docs/INVENTORY.md
- Makefile: verify-baseline

## ✅ Acceptance Criteria
- CI remains green
- No behavior changes
- Docs are LLM-friendly (explicit paths, exact truth)

## 🔍 Reviewer Validation
```bash
make fmt
make lint
make test
make precommit
make verify-baseline
