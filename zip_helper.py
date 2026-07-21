"""
Zoho Catalyst Deployment ZIP Builder
=====================================
Creates two clean deployment archives for Zoho Catalyst AppSail:

  backend.zip  — Python FastAPI app (without venv/cache) + datasets/ bundled inside
  frontend.zip — Next.js app (without node_modules/cache) with .next build included

Run from the project root (CrimeRakshak-main/):
    python zip_helper.py
"""
import os
import zipfile
from pathlib import Path

# Directories/files to always skip when traversing
ALWAYS_SKIP_DIRS = {".git", "__pycache__", ".next"}  # .next handled separately
ALWAYS_SKIP_FILES = {".env", ".env.local", ".env.production", ".DS_Store"}


def add_tree_to_zip(zipf: zipfile.ZipFile, src_dir: Path, arc_prefix: str,
                    exclude_dirs: set, exclude_files: set = None):
    """Recursively add all files under src_dir into zipf at arc_prefix/..."""
    if exclude_files is None:
        exclude_files = set()

    for root, dirs, files in os.walk(src_dir):
        # Prune excluded directories in-place (prevents os.walk from descending)
        dirs[:] = [d for d in dirs if d not in exclude_dirs and d not in ALWAYS_SKIP_DIRS]

        for filename in files:
            if filename in exclude_files or filename in ALWAYS_SKIP_FILES:
                continue

            file_path = Path(root) / filename
            # Arc path = prefix + relative path from src_dir
            rel = file_path.relative_to(src_dir)
            arcname = str(Path(arc_prefix) / rel) if arc_prefix else str(rel)

            try:
                zipf.write(file_path, arcname)
            except Exception as e:
                print(f"  ⚠  Skipped {arcname}: {e}")


# ── Backend ───────────────────────────────────────────────────────────────────

def build_backend_zip():
    print("=" * 60)
    print("Building backend.zip ...")
    print("=" * 60)

    output = "backend.zip"
    backend_dir = Path("backend")
    datasets_dir = Path("datasets")   # root-level datasets folder

    BACKEND_EXCLUDE_DIRS = {"venv", ".venv", "__pycache__", "exports", ".git"}
    BACKEND_EXCLUDE_FILES = {"crime_stats.duckdb", ".env"}

    count = 0
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add everything from backend/ (excluding venv, duckdb, .env etc.)
        print(f"  Adding backend/ source files ...")
        for root, dirs, files in os.walk(backend_dir):
            dirs[:] = [d for d in dirs if d not in BACKEND_EXCLUDE_DIRS]
            for filename in files:
                if filename in BACKEND_EXCLUDE_FILES or filename in ALWAYS_SKIP_FILES:
                    continue
                file_path = Path(root) / filename
                arcname = str(file_path.relative_to(backend_dir))
                try:
                    zipf.write(file_path, arcname)
                    count += 1
                except Exception as e:
                    print(f"  ⚠  Skipped {arcname}: {e}")

        # 2. Bundle datasets/ from the project root into the zip as "datasets/"
        #    This is CRITICAL — on Catalyst the backend can only read files
        #    within its own zip; ../datasets does NOT exist on the server.
        if datasets_dir.exists():
            print(f"  Bundling datasets/ folder ({sum(1 for _ in datasets_dir.rglob('*') if _.is_file())} files) ...")
            for file_path in datasets_dir.rglob("*"):
                if file_path.is_file():
                    arcname = "datasets/" + str(file_path.relative_to(datasets_dir))
                    try:
                        zipf.write(file_path, arcname)
                        count += 1
                    except Exception as e:
                        print(f"  ⚠  Skipped {arcname}: {e}")
        else:
            print("  ⚠  WARNING: datasets/ folder not found at project root!")
            print("      The AI chat and analytics features will NOT work on Catalyst.")

    size_mb = Path(output).stat().st_size / 1_048_576
    print(f"✔  Created {output} ({size_mb:.1f} MB, {count} files)")


# ── Frontend ──────────────────────────────────────────────────────────────────

def build_frontend_zip():
    print()
    print("=" * 60)
    print("Building frontend.zip ...")
    print("=" * 60)

    output = "frontend.zip"
    frontend_dir = Path("frontend")
    next_dir = frontend_dir / ".next"

    # Directories to exclude at every level
    FRONTEND_EXCLUDE_DIRS = {"node_modules", ".git"}

    count = 0
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add all regular frontend files (NOT .next — handled separately)
        print("  Adding frontend source files ...")
        for root, dirs, files in os.walk(frontend_dir):
            # Skip node_modules, .git, and defer .next to step 2
            dirs[:] = [
                d for d in dirs
                if d not in FRONTEND_EXCLUDE_DIRS and d != ".next"
            ]
            for filename in files:
                if filename in ALWAYS_SKIP_FILES:
                    continue
                file_path = Path(root) / filename
                arcname = str(file_path.relative_to(frontend_dir))
                try:
                    zipf.write(file_path, arcname)
                    count += 1
                except Exception as e:
                    print(f"  ⚠  Skipped {arcname}: {e}")

        # 2. Add .next/ but skip the cache directory (avoids file locks & huge size)
        if next_dir.exists():
            print("  Adding .next/ build output (skipping cache/) ...")
            for root, dirs, files in os.walk(next_dir):
                # Skip the cache directory anywhere in the .next tree
                dirs[:] = [d for d in dirs if d != "cache"]
                for filename in files:
                    file_path = Path(root) / filename
                    arcname = str(file_path.relative_to(frontend_dir))
                    try:
                        zipf.write(file_path, arcname)
                        count += 1
                    except Exception as e:
                        print(f"  ⚠  Skipped {arcname}: {e}")
        else:
            print("  ⚠  WARNING: .next/ build output not found!")
            print("      Run 'cd frontend && npm run build' first!")

    size_mb = Path(output).stat().st_size / 1_048_576
    print(f"✔  Created {output} ({size_mb:.1f} MB, {count} files)")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_backend_zip()
    build_frontend_zip()

    print()
    print("=" * 60)
    print("Done! Next steps:")
    print("  1. Upload backend.zip  → Catalyst Console → AppSail → crimerakshak-api")
    print("  2. Upload frontend.zip → Catalyst Console → AppSail → crimerakshak-web")
    print("  3. Set environment variables in the Catalyst Console for each AppSail")
    print("=" * 60)
