#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$SCRIPT_DIR/../evidence"
OUTPUT="$SCRIPT_DIR/../evidence/hardware.txt"
if [[ -e "$OUTPUT" ]]; then
  echo 'Hardware evidence already exists; archive it before collecting again.' >&2
  exit 1
fi
{
  date -u '+%Y-%m-%dT%H:%M:%SZ'
  hostname
  uname -a
  if [[ "$(uname -s)" == Darwin ]]; then
    system_profiler SPHardwareDataType SPSoftwareDataType
    sysctl hw.memsize hw.ncpu
  else
    command -v lscpu >/dev/null && lscpu
    command -v free >/dev/null && free -h
  fi
  k6 version
  node --version
  python3 --version
} > "$OUTPUT"
echo "Collected actual hardware in $OUTPUT."
echo 'Manually capture hardware screenshot and complete the spec table; do not invent Thuys-MacBook-Air hostname.'
