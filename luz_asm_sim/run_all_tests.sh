#!/bin/bash
set -eu
set -o pipefail

PYTHONPATH=. python -m unittest discover -s tests_unit
PYTHONPATH=. python tests_full/run_full_tests.py tests_full
