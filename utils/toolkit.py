"""utils/toolkit.py  –  helper arsenal for Anchorwork agents.

• WORK_DIR  → anchorwork/coder
• SRC_DIR   → anchorwork/coder/src
• REFS_DIR  → anchorwork/coder/references
"""

from pathlib import Path
import subprocess, sys, fnmatch, tempfile
import shutil
from typing import Optional

# ── folder constants ----------------------------------------------------
# Resolve anchorwork/coder no matter where this toolkit file lives.
from pathlib import Path

_cursor = Path(__file__).resolve()

# Walk up until we find a parent that CONTAINS a "coder" folder
WORK_DIR: Path | None = None
for parent in _cursor.parents:
    candidate = parent / "coder"
    if candidate.is_dir():
        WORK_DIR = candidate
        break

# Fallback: create coder/ next to the project root
if WORK_DIR is None:
    project_root = _cursor.parents[1]  # e.g., anchorwork/
    WORK_DIR = project_root / "coder"
    WORK_DIR.mkdir(parents=True, exist_ok=True)

SRC_DIR  = WORK_DIR / "src"
REFS_DIR = WORK_DIR / "references"
SRC_DIR.mkdir(parents=True, exist_ok=True)
REFS_DIR.mkdir(parents=True, exist_ok=True)

# ── basic file helpers --------------------------------------------------
def read_project_file(rel_path: str) -> str:
    """Read a file relative to the anchorwork/ project root."""
    return (WORK_DIR.parent / rel_path).read_text(encoding="utf-8")

def save_modified_file(rel_path: str, new_content: str) -> None:
    """Save a file relative to the anchorwork/ project root."""
    (WORK_DIR.parent / rel_path).write_text(new_content, encoding="utf-8")

# ------------------------------------------------------------------
def save_reference(name_or_path, content: str) -> str:
    """
    Write *content* to a file in coder/references. Always returns the
    absolute path so the caller can confirm the file location.
    """
    path = Path(name_or_path)
    if not path.is_absolute():
        path = REFS_DIR / path

    # DEBUG: print where we're writing
    print(f"[save_reference] Writing to {path}", flush=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    # DEBUG: confirm write size
    print(f"[save_reference] Wrote {len(content)} bytes → {path}", flush=True)
    return str(path)
# ------------------------------------------------------------------

# ── one-shot mirror (root → coder/src) ----------------------------------
EXCLUDE_PATTERNS = {
    ".git", ".venv", "env", ".mypy_cache", "__pycache__", "*.pyc",
    "data", "sandbox", "static"
}

def _should_exclude(path: Path) -> bool:
    """Determine if a path should be excluded from the mirror.

    Skips hidden files (starting with '.') and symlinks,
    as well as patterns in EXCLUDE_PATTERNS.
    """
    if path.name.startswith("."):
        return True
    if path.is_symlink():
        return True
    return any(fnmatch.fnmatch(path.name, pat) for pat in EXCLUDE_PATTERNS)

def mirror_source_once() -> None:
    """
    Copy the entire project tree (anchorwork/*) into anchorwork/coder/src/*.

    * Overwrites any existing files/folders in coder/src so the mirror is always fresh.
    * Skips items that match EXCLUDE_PATTERNS.
    * Result: anchorwork/coder/src will be a working mirror of your anchorwork project root.
    """
    root: Path = WORK_DIR.parent  # anchorwork/

    for item in root.iterdir():
        if _should_exclude(item):
            continue

        dest = SRC_DIR / item.name  # ← dest is defined **inside** the loop

        # remove stale copy first (if any) so we always mirror fresh content
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()

        # copy the source into coder/src/
        try:
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        except Exception as e:
            print(f"Error copying {item} to {dest}: {e}", file=sys.stderr)

# ── testing helpers -----------------------------------------------------
REPO_ROOT: Path = WORK_DIR.parent  # anchorwork/

def run_tests(_: str = "") -> str:
    """Run pytest in the anchorwork/ project root and return combined output."""
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                          cwd=REPO_ROOT, text=True, capture_output=True)
    return proc.stdout + proc.stderr

def summarize_diff(_: str = "") -> str:
    """Placeholder for a diff summarization helper."""
    return "diff helper placeholder"

def ensure_test_harness(route_paths: list[str]) -> None:
    """Autogenerate tests/test_routes.py if no tests exist yet.

    The tests are generated for the given list of route paths.
    """
    import textwrap

    test_dir = REPO_ROOT / "tests"
    if test_dir.exists():
        return
    test_dir.mkdir()
    with open(test_dir / "test_routes.py", "w", encoding="utf-8") as f:
        f.write("import httpx, main\napp = main.app\n\n")
        for p in route_paths:
            safe = p.strip('/').replace('/', '_') or "root"
            f.write(textwrap.dedent(f"""
                def test_{safe}():
                    with httpx.Client(app=app, base_url='http://test') as c:
                        r = c.get('{p}')
                    assert r.status_code < 500
            """))

# ── public toolbox ------------------------------------------------------
TOOLS = {
    "read_project_file":  read_project_file,
    "save_modified_file": save_modified_file,
    "save_reference":     save_reference,
    "run_tests":          run_tests,
    "summarize_diff":     summarize_diff,
    "mirror_source_once": mirror_source_once,
    "ensure_test_harness": ensure_test_harness,
}

# --- mirror freshness utility ------------------------------------------
import time

def ensure_project_mirror(force: bool = False) -> None:
    """
    Mirror the project into anchorwork/coder/src if the mirror is missing or outdated.

    Uses a '.last_mirror' timestamp file inside coder/src to track the last mirror time.
    Only re-mirrors if any top-level file/folder in the project root is newer than the last mirror,
    unless force=True, which always triggers a mirror.

    The intended project root is anchorwork/.
    """
    ts_path: Path = SRC_DIR / ".last_mirror"
    last_mirror: float = 0
    if ts_path.exists():
        try:
            last_mirror = float(ts_path.read_text().strip())
        except Exception:
            last_mirror = 0

    root: Path = WORK_DIR.parent
    need_mirror: bool = force
    if not force:
        for item in root.iterdir():
            if _should_exclude(item):
                continue
            # Check modification time of each top-level item
            if item.stat().st_mtime > last_mirror:
                need_mirror = True
                break

    if not SRC_DIR.exists() or need_mirror:
        mirror_source_once()
        ts_path.write_text(str(time.time()))

# Add ensure_project_mirror to TOOLS
TOOLS["ensure_project_mirror"] = ensure_project_mirror
