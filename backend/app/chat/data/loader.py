"""Load the curated KSP crime CSV datasets into an on-disk DuckDB database.

The CSVs are *aggregate* statistics (district × crime-head × period counts).
Each curated file becomes one clean DuckDB table with snake_cased columns and
numeric measure columns coerced to integers. Column *labels* (the original
human-readable headers) are preserved in the generated schema card so the LLM
can map natural-language questions to columns.

Run as a module to (re)build the database:

    python -m app.chat.data.loader
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Dataset:
    """A curated CSV mapped to a DuckDB table."""

    table: str
    filename: str
    description: str
    # Columns that hold non-numeric identifiers (district, crime head, …).
    # Everything else is treated as an integer measure and coerced.
    key_columns: tuple[str, ...]


# ── Curated catalog ──────────────────────────────────────────────────────
# Only clean, well-formed files are included. The two multi-header review
# workbooks are intentionally excluded until they are flattened.
CATALOG: tuple[Dataset, ...] = (
    Dataset(
        table="district_crime_matrix",
        filename="02_district_wise_reported_cases.csv",
        description=(
            "Reported cases per district broken down by crime type "
            "(murder, dacoity, robbery, theft, cyber crime, rape, POCSO, "
            "NDPS, etc.). One row per district; each crime type is a column."
        ),
        key_columns=("district",),
    ),
    Dataset(
        table="district_major_heads_yearly",
        filename="district_wise_major_heads_yearly.csv",
        description=(
            "Yearly count of major crime heads per district/unit "
            "(murder, rape, robbery, burglary, cyber crime, POCSO, motor "
            "accidents, cruelty by husband, etc.)."
        ),
        key_columns=("district_units",),
    ),
    Dataset(
        table="crime_review_summary",
        filename="01_crime_review_summary.csv",
        description=(
            "State-level crime counts by crime head and category, comparing "
            "January 2026, December 2025 and January 2025."
        ),
        key_columns=("crime_head", "category"),
    ),
    Dataset(
        table="crimes_against_women",
        filename="09_crime_against_women.csv",
        description=(
            "Crimes against women by crime head, with current-year-to-date, "
            "previous-year same-month, previous-month and current-month "
            "(Jan 2026) counts."
        ),
        key_columns=("heads_of_crime",),
    ),
    Dataset(
        table="crimes_against_children",
        filename="10_crime_against_children.csv",
        description=(
            "Crimes against children by crime head, with year-to-date and "
            "monthly comparison counts (Jan 2026)."
        ),
        key_columns=("heads_of_crime",),
    ),
    Dataset(
        table="crimes_against_sc_st",
        filename="11_crime_against_sc_st.csv",
        description=(
            "Crimes against SC/ST communities by crime head, with year-to-date "
            "and monthly comparison counts (Jan 2026)."
        ),
        key_columns=("heads_of_crime",),
    ),
    Dataset(
        table="sakala_disposals",
        filename="04_sakala_district_receipts_disposals.csv",
        description=(
            "Sakala (citizen service) receipts, disposals and pendency after "
            "due date per district."
        ),
        key_columns=("district",),
    ),
    Dataset(
        table="esign_fir",
        filename="06_esign_fir_jan2026.csv",
        description=(
            "FIRs registered vs FIRs e-signed per police unit for Jan 2026, "
            "with completion percentage."
        ),
        key_columns=("unit_name",),
    ),
    Dataset(
        table="esign_chargesheet",
        filename="07_esign_chargesheet_jan2026.csv",
        description=(
            "Chargesheets registered vs e-signed per police unit for Jan 2026, "
            "with completion percentage."
        ),
        key_columns=("unit_name",),
    ),
)


def _snake(name: str) -> str:
    """Normalize a CSV header into a safe snake_case column name."""
    name = name.replace("﻿", "").strip()
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name or "col"


def _load_frame(dataset: Dataset, datasets_dir: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Read + clean one CSV. Returns the frame and a {clean: original} label map."""
    path = datasets_dir / dataset.filename
    df = pd.read_csv(path, encoding="utf-8-sig")

    original = list(df.columns)
    clean = [_snake(c) for c in original]
    # De-duplicate collisions deterministically.
    seen: dict[str, int] = {}
    deduped: list[str] = []
    for c in clean:
        if c in seen:
            seen[c] += 1
            deduped.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            deduped.append(c)
    label_map = dict(zip(deduped, original))
    df.columns = deduped

    # Drop obvious serial-number columns; they add noise for the LLM.
    for junk in ("sl_no", "sl_no_", "s_no", "sl_no_1"):
        if junk in df.columns:
            df = df.drop(columns=[junk])
            label_map.pop(junk, None)

    # Coerce measure columns (everything that isn't a declared key) to numbers.
    for col in df.columns:
        if col in dataset.key_columns:
            df[col] = df[col].astype("string").str.strip()
            continue
        cleaned = (
            df[col].astype("string").str.replace(",", "", regex=False).str.strip()
        )
        num = pd.to_numeric(cleaned, errors="coerce")
        # Keep as text only if coercion wiped out most values (truly textual col).
        if num.notna().mean() >= 0.5:
            df[col] = num
        else:
            df[col] = df[col].astype("string").str.strip()

    return df, label_map


# Synthetic case-level tables (generated by app.chat.data.case_generator).
# These power the network graph, financial-crime module, forecasting panel
# and case-level chat queries. Loaded verbatim — their headers are already
# clean snake_case.
SYNTHETIC_TABLES: tuple[tuple[str, str], ...] = (
    ("cases", "cases.csv"),
    ("case_people", "case_people.csv"),
    ("case_accounts", "case_accounts.csv"),
    ("case_transactions", "case_transactions.csv"),
)


def _load_synthetic(con: duckdb.DuckDBPyConnection, base: Path) -> list[str]:
    synth_dir = base / "synthetic_cases"
    if not synth_dir.exists() or not (synth_dir / "case_people.csv").exists():
        try:
            from app.chat.data.case_generator import generate
            logger.info("Synthetic dataset missing — auto-generating synthetic cases into %s...", synth_dir)
            generate(out_dir=synth_dir)
        except Exception as e:
            logger.error("Failed to auto-generate synthetic cases: %s", e)

    loaded: list[str] = []
    for table, filename in SYNTHETIC_TABLES:
        path = synth_dir / filename
        if not path.exists():
            logger.warning("Synthetic file missing, skipping: %s", path)
            continue
        frame = pd.read_csv(path)
        con.register("_staging", frame)
        con.execute(f'DROP TABLE IF EXISTS "{table}"')
        con.execute(f'CREATE TABLE "{table}" AS SELECT * FROM _staging')
        con.unregister("_staging")
        loaded.append(table)
        logger.info("Loaded %s -> table %s (%d rows)", filename, table, len(frame))
    return loaded


def build_database(datasets_dir: str | None = None, duckdb_path: str | None = None) -> dict[str, dict[str, str]]:
    """(Re)build the DuckDB database from the curated catalog.

    Returns a mapping ``{table: {clean_col: original_label}}`` used by the
    schema-card generator.
    """
    base = Path(datasets_dir or settings.DATASETS_DIR)
    db_path = duckdb_path or settings.DUCKDB_PATH
    labels: dict[str, dict[str, str]] = {}

    try:
        # Try read-write mode (default)
        con = duckdb.connect(db_path)
        is_read_only = False
    except Exception as e:
        # If read-write fails (e.g. read-only filesystem), fallback to read-only mode
        logger.warning("Could not connect to DuckDB in read-write mode. Attempting read-only mode... Details: %s", e)
        try:
            con = duckdb.connect(db_path, read_only=True)
            is_read_only = True
        except Exception as read_err:
            logger.error("Failed to connect to DuckDB even in read-only mode: %s", read_err)
            raise

    try:
        if is_read_only:
            # If read-only, we don't try to drop/rebuild tables.
            # Instead, we just read columns from existing tables so schema-card generation works.
            logger.info("DuckDB is in read-only mode. Skipping database rebuild and reading existing schema.")
            try:
                # Query tables from duckdb
                tables_res = con.execute("SHOW TABLES").fetchall()
                for (table_name,) in tables_res:
                    cols_res = con.execute(f"DESCRIBE {table_name}").fetchall()
                    # cols_res: [(column_name, column_type, null, key, default, extra), ...]
                    col_map = {}
                    for row in cols_res:
                        col_name = row[0]
                        col_map[col_name] = col_name  # In read-only fallback, use column name as label
                    labels[table_name] = col_map
            except Exception as schema_err:
                logger.error("Failed to read existing schema from read-only DuckDB: %s", schema_err)
        else:
            # Normal build path
            for ds in CATALOG:
                try:
                    frame, label_map = _load_frame(ds, base)
                except FileNotFoundError:
                    logger.warning("Dataset file missing, skipping: %s", ds.filename)
                    continue
                con.register("_staging", frame)
                con.execute(f'DROP TABLE IF EXISTS "{ds.table}"')
                con.execute(f'CREATE TABLE "{ds.table}" AS SELECT * FROM _staging')
                con.unregister("_staging")
                labels[ds.table] = label_map
                logger.info("Loaded %s -> table %s (%d rows)", ds.filename, ds.table, len(frame))

            for table in _load_synthetic(con, base):
                labels[table] = {}
    finally:
        con.close()

    return labels


if __name__ == "__main__":
    result = build_database()
    print(f"Built {settings.DUCKDB_PATH} with {len(result)} tables:")
    for table in result:
        print(f"  - {table}")
