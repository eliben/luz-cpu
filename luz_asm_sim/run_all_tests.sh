#!/bin/bash
set -eu
set -o pipefail

PYTHONPATH=. python -m unittest discover -s tests_unit
