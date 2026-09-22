# TypedDecide Agent Guide

## Project Map

- Public API and question invariants: [src/typedecide/types.py](src/typedecide/types.py).
- Lazy backend registry: [src/typedecide/registry.py](src/typedecide/registry.py); adapters live in [src/typedecide/backends](src/typedecide/backends).
- Package-owned benchmark fixture and validation: [src/typedecide/fixtures/test_cases.json](src/typedecide/fixtures/test_cases.json) and [src/typedecide/benchmark.py](src/typedecide/benchmark.py).

## Working Conventions

- Use `uv` for installation, execution, and tests.
- `noul` options are canonically ordered `false`, then `true`. A `score` rubric is ordered low-to-high; its option IDs are string indices and `Answer.score` is the probability-weighted index.
- Preserve all `Answer` invariants: option order is part of the cross-backend contract and probabilities must normalize to one.

## Fixtures And Benchmarks

- `test_cases.json` is runtime package data, not test-only data. Keep stable IDs, deterministic gold labels, and descriptive criteria.
- Benchmark outputs are immutable. Use a new path under `results/`; never overwrite an existing raw artifact.
- Generate comparison reports only from compatible complete artifacts with the same cases and repeat count. Do not compare hosted and local latency as hardware-equivalent.
- For benchmark fixtures, multi-backend runs, artifact merge/reporting, and interpretation, follow [benchmark-report](.agents/skills/benchmark-report/SKILL.md).

## Backend Notes

- Jev requires `TYPESAFE_API_KEY` in the environment. Never place credentials in source, fixtures, or result artifacts.
- SemIf has a pinned ML stack; prefer a dedicated environment when it conflicts with other extras.
- CLI device forwarding is backend-specific: Jev does not accept `device`; automatic Laya selection is represented by omitting `device`.
