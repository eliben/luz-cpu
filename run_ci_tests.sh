#!/bin/bash
# For Travis CI testing.
set -eu
set -o pipefail

cd luz_asm_sim
./run_all_tests.sh
