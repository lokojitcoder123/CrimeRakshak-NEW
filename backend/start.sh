#!/bin/bash
set -e

pip3 install --no-cache-dir -r requirements.txt

# ── Pre-build DuckDB so the network/full endpoint works on first request ──
# On Render the .duckdb file is excluded from git (see .gitignore) and must
# be generated at deploy time from the bundled datasets/ folder.
echo "[start.sh] Building DuckDB from datasets + generating synthetic cases..."
python3 - <<'PYEOF'
import os, sys

# Resolve DATASETS_DIR: if the env var points to a path that doesn't exist
# relative to cwd, fall back to the sibling 'datasets' folder at the repo root.
datasets_env = os.environ.get("DATASETS_DIR", "datasets")
if not os.path.isabs(datasets_env):
    cwd_path = os.path.join(os.getcwd(), datasets_env)
    # Also try one level up (repo root), which is how local dev is configured
    parent_path = os.path.join(os.path.dirname(os.getcwd()), datasets_env.lstrip("./").lstrip("../"))
    if os.path.isdir(cwd_path):
        resolved = cwd_path
    elif os.path.isdir(os.path.join(os.getcwd(), "..", "datasets")):
        resolved = os.path.normpath(os.path.join(os.getcwd(), "..", "datasets"))
    else:
        resolved = cwd_path  # best effort
else:
    resolved = datasets_env

print(f"[init] DATASETS_DIR resolved to: {resolved}", flush=True)
os.environ["DATASETS_DIR"] = resolved

# Generate synthetic CSVs if missing
synth_dir = os.path.join(resolved, "synthetic_cases")
if not os.path.isdir(synth_dir) or not os.path.exists(os.path.join(synth_dir, "case_people.csv")):
    print("[init] Generating synthetic case dataset...", flush=True)
    try:
        from pathlib import Path
        from app.chat.data.case_generator import generate
        generate(out_dir=Path(synth_dir))
        print("[init] Synthetic cases generated.", flush=True)
    except Exception as e:
        print(f"[init] WARNING: Could not generate synthetic cases: {e}", flush=True)
else:
    print("[init] Synthetic cases already present, skipping generation.", flush=True)

# Build / refresh DuckDB
duckdb_path = os.environ.get("DUCKDB_PATH", "crime_stats.duckdb")
print(f"[init] Building DuckDB at: {duckdb_path}", flush=True)
try:
    from app.chat.data.loader import build_database
    result = build_database(datasets_dir=resolved, duckdb_path=duckdb_path)
    print(f"[init] DuckDB built with tables: {list(result.keys())}", flush=True)
except Exception as e:
    print(f"[init] WARNING: DuckDB build failed: {e}", flush=True)
PYEOF

echo "[start.sh] Starting CrimeRakshak API server..."
python3 run.py
