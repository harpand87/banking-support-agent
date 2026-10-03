#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
"$SCRIPT_DIR/BankingSupportEvaluation"
printf '\nPress Return to close this window.'
read -r _ || true