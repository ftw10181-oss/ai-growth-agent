# Evaluation System

This directory turns AI Growth Agent quality from an impression into a repeatable product process.

## Contents

- `cases.json` — 12 fixed briefs across AI hardware, SaaS, consumer apps, creator tools, developer platforms, and industrial AI
- `rubric.md` — five-dimension human scoring rubric plus hard contract gates
- `user-testing-guide.md` — five-participant moderated comparison plan
- `results/baseline-scorecard.csv` — reusable blank scorecard
- `results/baseline-v0.1/` — reviewed live baseline, raw outputs, run metadata, report, and completed scorecard
- `check_outputs.py` — offline contract and claim-risk checks for saved run outputs

## Evaluation loop

```text
Fixed briefs → Run prompt version → Contract checks → Blind human scoring
      ↑                                                    ↓
Regression set ← Record failures ← Revise prompt and schema
```

## Run contract checks

Save one public API response per case as `<case-id>.json`, then run:

```bash
python evals/check_outputs.py evals/results/runs/<run-name>
```

Ad-hoc generated run directories are ignored by Git until a reviewed baseline is intentionally selected for publication. The reviewed V0.1 baseline is committed as portfolio evidence.

## Integrity rules

- Never invent user-test or evaluation results.
- Always report sample size and denominator.
- Preserve failed cases; they are regression inputs, not embarrassing noise.
- Keep prompt version, workflow version, model, date, and scoring method with every published baseline.
- Separate automated contract checks from human judgments about usefulness.
