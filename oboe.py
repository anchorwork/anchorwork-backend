import shutil
from pathlib import Path
import difflib
import datetime
import subprocess
import logging

LOGFILE = Path("oboe_patch_log.txt")

def _timestamp():
    return datetime.datetime.now().isoformat(timespec='seconds')

def log_patch(action, filename, patch, diff, result):
    with open(LOGFILE, "a", encoding="utf-8") as logf:
        logf.write(
            f"[{_timestamp()}] {action} on {filename}\n"
            f"Patch instructions:\n{patch}\n"
            f"Diff preview:\n{diff}\n"
            f"Result: {result}\n"
            f"{'-'*40}\n"
        )

def make_backup(filepath):
    fp = Path(filepath)
    backup = fp.with_suffix(fp.suffix + f".bak.{_timestamp().replace(':','_')}")
    shutil.copyfile(fp, backup)
    return str(backup)

def show_diff(before, after):
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    return ''.join(difflib.unified_diff(before_lines, after_lines, fromfile='before', tofile='after'))

def git_commit(filepath, message):
    try:
        subprocess.run(["git", "add", str(filepath)], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        return "Committed to git."
    except Exception as e:
        return f"Git commit failed: {e}"

def apply_patch_to_content(content, patch_instructions):
    """
    This is the part you can make as advanced as you like.
    For now: If patch_instructions contains a literal string replacement (FROM >> TO), do it.
    Expand to support regex, GPT-generated edits, code block replacement, etc.
    """
    import re
    # Example: "REPLACE: old_line >> new_line"
    match = re.match(r"REPLACE:\s*(.+?)\s*>>\s*(.+)", patch_instructions, re.DOTALL)
    if match:
        before, after = match.groups()
        return content.replace(before, after)
    # Or, if patch_instructions is "APPEND: text", append
    if patch_instructions.startswith("APPEND:"):
        return content + "\n" + patch_instructions[len("APPEND:"):].strip()
    # Or, just insert as comment at top
    return "# Oboe Patch Instruction:\n# " + patch_instructions + "\n" + content

def edit_file(patch_instructions, filename=None, require_approval=True, git=True):
    """
    Safely applies an agent-proposed code patch.
    - Makes a backup first.
    - Shows a diff preview before applying.
    - Optionally requests approval from user (if running in interactive mode).
    - Logs every action.
    - Optionally commits to git.
    """
    if not filename:
        result = f"[Oboe] No filename specified. Patch simulated:\n{patch_instructions}"
        log_patch("Simulate", "NONE", patch_instructions, diff="", result=result)
        return result

    file_path = Path(filename)
    if not file_path.exists():
        result = f"[Oboe] ERROR: {filename} not found."
        log_patch("Fail", filename, patch_instructions, diff="", result=result)
        return result

    # Read before
    before = file_path.read_text(encoding="utf-8")
    # Propose new content
    new_content = apply_patch_to_content(before, patch_instructions)
    diff = show_diff(before, new_content)

    # Preview diff and ask approval if requested
    if require_approval:
        print(f"\n[Oboe] --- PATCH PREVIEW for {filename} ---")
        print(diff)
        user_input = input("[Oboe] Apply this patch? (yes/no): ").strip().lower()
        if user_input not in {"yes", "y"}:
            result = "[Oboe] Patch aborted by user."
            log_patch("Abort", filename, patch_instructions, diff, result)
            return result

    # Backup before write
    backup = make_backup(filename)
    # Write patch
    file_path.write_text(new_content, encoding="utf-8")
    result = f"[Oboe] Patch applied to {filename} with backup at {backup}."
    if git:
        git_result = git_commit(filename, f"Oboe patch: {patch_instructions[:60]}")
        result += f"\n{git_result}"

    log_patch("Edit", filename, patch_instructions, diff, result)
    return result

def rollback(filename):
    """
    Rollback to the most recent backup for a file.
    """
    fp = Path(filename)
    backups = sorted(fp.parent.glob(fp.stem + fp.suffix + ".bak.*"))
    if not backups:
        return f"No backup found for {filename}."
    latest = backups[-1]
    shutil.copyfile(latest, fp)
    return f"Rolled back {filename} to backup {latest}."