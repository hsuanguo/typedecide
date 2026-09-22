---
name: benchmark-report
description: "Use when: benchmarking typedecide backends, adding or reviewing benchmark fixtures, comparing Jev, this-that, SemIf, or Laya, merging run artifacts, or generating and validating Markdown and self-contained HTML benchmark reports."
argument-hint: "Benchmark target, backends, repeats, and report scope"
user-invocable: true
---

# TypedDecide Benchmark And Report

Run reproducible, fair typed-decision benchmarks for `typedecide` backends and produce auditable JSON, Markdown, and self-contained HTML reports.

## Scope

- Treat `src/typedecide/fixtures/test_cases.json` as package-owned benchmark data.
- Preserve existing artifacts. Every new live run uses a new output path.
- Use `uv` for all installation, tests, benchmark commands, and report generation.
- Keep API keys in environment variables. Never print, store, commit, or request them in chat.
- Do not claim broad model superiority from a small authored fixture suite.

## Before Running

1. Read `README.md`, `pyproject.toml`, `src/typedecide/cli.py`, and the relevant backend adapter.
1. Identify which backend extras are needed:
   - Jev: `uv sync --extra jev`; requires `TYPESAFE_API_KEY`.
   - this-that: `uv sync --extra thisthat`.
   - Laya: `uv sync --extra laya`.
   - SemIf: `uv sync --extra semif`; prefer a dedicated environment if its pinned ML stack conflicts with other backends.
1. Validate fixtures and offline behavior before any paid or model-loading run:

```bash
uv sync
uv run pytest -q
uv run typedecide-benchmark validate
```

1. Confirm all cases have deterministic gold labels derived from embedded state, policy, candidates, evidence, or rubric. Do not silently repair ambiguous cases after results are known.

## Fixture Design

For each benchmark case, include:

- Stable case ID and family.
- State as a string, JSON object, or JSON array.
- One strongly typed question: Choice, Noul, or Score.
- Descriptive, mutually distinguishable criteria.
- A gold option ID and tags such as `clear`, `negative`, `boundary`, or `no_match`.

Use stable option IDs. Put changing source text in descriptions or state, not in IDs.

For `noul`, preserve the canonical order `false`, then `true`. For `score`, order rubric levels from low to high. Include a no-match option for Choice when candidate coverage is incomplete.

## Fair Backend Mapping

Every backend must receive equivalent meaning:

- Choice: same option IDs and descriptions.
- Noul: same proposition and explicit true/false meanings.
- Score: same ordered rubric descriptions.
- State: preserve structured data where a backend supports it; only use deterministic serialization where text is required.

Keep native metadata but normalize all results into canonical option order, probability distribution, selected option, top probability, optional native confidence, expected score, latency, and usage.

Do not compare native confidence values across providers as though they share a definition. Compare full probability distributions and task outcomes instead.

## Run Strategy

1. Start with one smoke case per backend after offline validation.
1. Run each backend into a separate immutable artifact. Never overwrite an existing artifact.
1. Use a fixed repeat count for every backend. Five repeats are suitable for the project’s current 100-case exploratory suite.
1. Checkpoint after every case/backend/repeat so runs can resume without repeating paid API calls.
1. Record requested and resolved model versions, package versions, device, dtype, timestamps, token usage, latency, and failures.

Current single-backend command:

```bash
uv run typedecide-benchmark run \
  --backend <jev|thisthat|semif|laya> \
  --repeats 5 \
  --device cuda \
  --output results/<backend>-100.json
```

## Artifact Validation

Before merging or reporting, verify every artifact has:

- Completed status.
- The expected fixture count and identical fixture IDs/hashes across backends.
- The expected repeat count for every `(case_id, backend)` pair.
- No omitted errors or malformed distributions.
- Finite probabilities in `[0, 1]` that sum to one. Normalize documented rounded distributions, such as Laya’s four-decimal maps, before validation; retain the raw provider response separately if available.
- No credentials or request headers in JSON, Markdown, or HTML.

Keep model failures separate from invalid distribution-format failures. Diagnose adapter mapping before treating an invalid normalized response as a model error.

## Metrics

Compute and report:

- Accuracy with every attempted case in the denominator.
- Multiclass Brier score and negative log-likelihood, both lower-is-better.
- Mean absolute ordinal error for Score questions.
- Failure rate and invalid-probability rate.
- Per-family and per-primitive accuracy.
- Repeat probability standard deviation and label agreement.
- Selective accuracy and coverage at explicit top-probability thresholds.
- Mean, median, and p90 latency.
- Hosted token cost separately from local runtime; never fabricate a local dollar cost.

Keep comparisons honest: hosted round-trip latency and warmed local GPU latency are not hardware-equivalent.

## Merge And Report

Merge only compatible completed artifacts. Reject merge inputs that differ in fixture hashes/order, repeat count, or backend identity.

A complete report has:

1. Scope and caveats: authored fixture size, repeats, and non-generalization warning.
1. Overall metrics table for every backend.
1. Backend model/version/device metadata.
1. Per-family and per-primitive results.
1. Case-level mean probabilities, predicted option, gold option, and error marker.
1. Repeatability, coverage, latency, token usage, and cost.
1. Method notes explaining canonical mapping and backend-specific limitations.

Generate both:

- Markdown for code review and version control.
- Self-contained HTML for human review. It must include all case IDs, contain no external assets, and keep API keys absent.

Use the project's `typedecide-benchmark report` command whenever it is available. That command
must render structured artifact data directly into HTML elements: summary cards, metric tables,
family/primitive comparison bars, a complete case table, error highlighting, usage, and method
metadata. Do not convert Markdown into escaped text inside a `<pre>` block; doing so hides the
benchmark structure and makes long reports unreadable.

Use the project renderer in `src/typedecide/html_renderer.py` as the single visual source of
truth. Keep report generation driven by raw JSON and the project CLI; do not hand-fill metric
values or maintain a separate static HTML template. When building or repairing the renderer,
preserve its responsive layout, dense scan-friendly tables, per-backend colors, case-level error
highlighting, and self-contained CSS.

If the current CLI lacks merge or report commands, implement and test those capabilities before declaring the benchmark complete. Do not substitute manually edited tables for reproducible report generation.

## Completion Checks

Before calling the work complete:

```bash
uv lock --check
uv run pytest -q
uv run typedecide-benchmark validate
```

Then verify the final artifacts:

- All expected backends, cases, and repeats are present.
- Run count equals `unique_cases * backends * repeats`.
- All report tables derive from raw JSON, not copied numbers.
- Markdown and HTML have consistent aggregate results.
- HTML parses, contains every fixture ID, and has no external resources or secrets.
- HTML contains real report structure (`<table>`, case table rows, comparison bars, and error
  markers) and does not use `<pre>` as the primary report body.
- Explain disagreements by inspecting exact state, question, criteria, probabilities, and gold rule before making conclusions.

## Current Project Note

The package currently exposes `typedecide-benchmark validate` and `typedecide-benchmark run`. Merging and Markdown/HTML reporting remain migration work from the legacy `comparison/` harness. Add those commands to the standalone package before using this skill for a new all-backend published comparison.

## Skill Evaluation

Use [the bundled eval prompts](./evals/evals.json) when changing this skill. They cover a new
backend benchmark, raw-artifact reporting, and an ordinary non-benchmark task that should not
trigger this workflow. Run each prompt with and without the skill, then compare whether the skill
improves reproducibility, artifact safety, and report validation without expanding scope on the
negative case.
