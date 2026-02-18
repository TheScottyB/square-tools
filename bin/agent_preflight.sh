#!/usr/bin/env bash

# Runtime preflight gate for Square tooling.
# Contract: agent_preflight.sh --operation <op> --mode <mode> --runtime <id>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$(cd "$SCRIPT_DIR/../runtime" && pwd)"

OPERATION=""
MODE="${SQUARE_RUNTIME_MODE:-}"
RUNTIME_ID="${SQUARE_RUNTIME_ID:-local_cli}"
QUIET=1

usage() {
  cat <<'USAGE'
Usage: agent_preflight.sh --operation <op> [--mode <mode>] [--runtime <id>] [--verbose]

Options:
  --operation <op>   Operation id from runtime/operation_policy.json (required)
  --mode <mode>      Runtime mode: WEB_SAFE | LOCAL_STANDARD | LOCAL_PRIVILEGED
  --runtime <id>     Runtime profile id from runtime/runtime_profiles.json
  --verbose          Print success output (default quiet)
  --quiet            Suppress success output (default)
  -h, --help         Show this help

Exit codes:
  0  Allowed
  20 Unknown runtime/profile/mode
  21 Missing required capability
  22 Operation forbidden by mode/policy
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --operation)
      OPERATION="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      shift 2
      ;;
    --runtime)
      RUNTIME_ID="$2"
      shift 2
      ;;
    --verbose)
      QUIET=0
      shift
      ;;
    --quiet)
      QUIET=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 22
      ;;
  esac
done

if [[ -z "$OPERATION" ]]; then
  echo "Preflight error: --operation is required" >&2
  usage >&2
  exit 22
fi

CAPABILITY_FILE="$RUNTIME_DIR/capability_matrix.json"
PROFILE_FILE="$RUNTIME_DIR/runtime_profiles.json"
POLICY_FILE="$RUNTIME_DIR/operation_policy.json"

if [[ ! -f "$CAPABILITY_FILE" || ! -f "$PROFILE_FILE" || ! -f "$POLICY_FILE" ]]; then
  echo "Preflight error: runtime contract files are missing under $RUNTIME_DIR" >&2
  exit 20
fi

python3 - "$CAPABILITY_FILE" "$PROFILE_FILE" "$POLICY_FILE" "$OPERATION" "$MODE" "$RUNTIME_ID" "$QUIET" <<'PY'
import json
import sys
from typing import Any, Dict

capability_file, profile_file, policy_file, operation, requested_mode, runtime_id, quiet_flag = sys.argv[1:8]
quiet = quiet_flag == "1"

with open(capability_file, "r", encoding="utf-8") as f:
    capability_matrix = json.load(f)
with open(profile_file, "r", encoding="utf-8") as f:
    runtime_profiles = json.load(f)
with open(policy_file, "r", encoding="utf-8") as f:
    operation_policy = json.load(f)

modes: Dict[str, Any] = capability_matrix.get("modes", {})
profiles = {p["id"]: p for p in runtime_profiles.get("profiles", [])}
ops = {entry["operation"]: entry for entry in operation_policy.get("operations", [])}

mode_rank = {
    "WEB_SAFE": 0,
    "LOCAL_STANDARD": 1,
    "LOCAL_PRIVILEGED": 2,
}

if runtime_id not in profiles:
    print(f"Preflight denied: unknown runtime profile '{runtime_id}'", file=sys.stderr)
    sys.exit(20)

profile = profiles[runtime_id]
mode = requested_mode or profile.get("default_mode")
if mode not in mode_rank:
    print(f"Preflight denied: unknown mode '{mode}'", file=sys.stderr)
    sys.exit(20)

allowed_modes = set(profile.get("allowed_modes", []))
if mode not in allowed_modes:
    print(
        f"Preflight denied: mode '{mode}' is not allowed for runtime '{runtime_id}'",
        file=sys.stderr,
    )
    sys.exit(22)

if mode not in modes:
    print(f"Preflight denied: capability matrix missing mode '{mode}'", file=sys.stderr)
    sys.exit(20)

if operation not in ops:
    print(f"Preflight denied: unknown operation '{operation}'", file=sys.stderr)
    sys.exit(22)

policy = ops[operation]
required_mode = policy.get("required_mode", "WEB_SAFE")
if required_mode not in mode_rank:
    print(
        f"Preflight denied: policy for '{operation}' has invalid required_mode '{required_mode}'",
        file=sys.stderr,
    )
    sys.exit(20)

if mode_rank[mode] < mode_rank[required_mode]:
    reason = policy.get("deny_reason", "Operation not allowed in current mode")
    print(
        (
            f"Preflight denied: operation '{operation}' requires {required_mode}, "
            f"but current mode is {mode}. {reason}"
        ),
        file=sys.stderr,
    )
    sys.exit(22)

capabilities = modes[mode].get("capabilities", {})
required_capabilities = policy.get("required_capabilities", [])
missing = [c for c in required_capabilities if not capabilities.get(c, False)]

if missing:
    print(
        (
            f"Preflight denied: operation '{operation}' missing capabilities "
            f"for mode {mode}: {', '.join(missing)}"
        ),
        file=sys.stderr,
    )
    sys.exit(21)

if not quiet:
    print(
        (
            f"Preflight OK: operation={operation} runtime={runtime_id} "
            f"mode={mode}"
        )
    )

sys.exit(0)
PY
