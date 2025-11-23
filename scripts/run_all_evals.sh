#!/usr/bin/env bash
set -euo pipefail

python -m evals.run_evals --suite golden
python -m evals.run_evals --suite regression
python -m evals.run_evals --suite red_team
