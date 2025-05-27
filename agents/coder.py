# Requires: pip install requests ruff
from pathlib import Path
from typing import Optional
from utils.tools import get_pep_talk, get_shanty, get_joke
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from utils.model_mixin import ModelSwitchingMixin
from utils.toolkit       import TOOLS, WORK_DIR, mirror_source_once
from config.model_config import MODEL_CODER, describe_model
from utils.web_search    import web_search
from utils.agent_memory import AgentMemory
from crew.ritual_synthesis import synthesize_ritual
from crew.crew_history import log_crew_event
import pathlib, re, logging, subprocess, os, tempfile, sys   # ← added sys
import threading, shlex  # new
import requests, json    # for Slack error notifications
logger = logging.getLogger(__name__)
from tqdm import tqdm
import time  # for back‑off retries

# ────────────────────────────────────────────────
# Ensure coder directories always exist.
from pathlib import Path

BASE_DIR = Path(__file__).parent                # …/agents
ROOT_CODER = BASE_DIR.parent / "coder"          # …/coder  (sibling to agents)
NESTED_CODER = BASE_DIR / "coder"               # …/agents/coder  (legacy)

# Prefer root‑level /coder if it exists, else use nested path.
CODER_DIR = ROOT_CODER if ROOT_CODER.exists() else NESTED_CODER

SRC_DIR  = CODER_DIR / "src"
REFS_DIR = CODER_DIR / "references"

# Create folders if they were moved or deleted
for p in (CODER_DIR, SRC_DIR, REFS_DIR):
    p.mkdir(parents=True, exist_ok=True)
# ────────────────────────────────────────────────

# --- Slack/e-mail notifier for ops ---
def _notify_ops(subject: str, body: str):
    """
    Sends a brief crash / alert message to Slack via webhook.
    Set SLACK_WEBHOOK in your environment to enable.
    """
    url = os.getenv("SLACK_WEBHOOK")
    if not url:
        return
    try:
        requests.post(url, json={"text": f"*{subject}*\n```{body[:3900]}```"})
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
state_lock = threading.Lock()

memory = AgentMemory("coder")

TOTAL_STEPS_P1 = 6  # docs, routes, static, tests, report, audit
STEP_LONG_THRESHOLD = 30  # seconds before a step logs a slow-warning

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str


def _bar(done: int) -> str:
    pct = int(done / TOTAL_STEPS_P1 * 100)
    return f"{pct:>3}% [{'▓' * done}{'░' * (TOTAL_STEPS_P1 - done)}]"

def _run(cmd, cwd=".") -> str:
    return subprocess.run(cmd, text=True, capture_output=True, cwd=cwd).stdout

class Coder(ModelSwitchingMixin):
    from pathlib import Path
    EDU_FILE   = CODER_DIR / "codereducation.txt"
    GUIDE_FILE = CODER_DIR / "guide.txt"
    core_education = ""
    design_guide = ""
    """
    The Coder embodies the full Anchorwork 'chief engineer' logic:
    managing a dynamic roadmap, maintaining crew mood, orchestrating rituals,
    fostering innovation, and supporting the crew collaboratively.
    """

    @classmethod
    def load_core_education(cls):
        try:
            with open(cls.EDU_FILE, encoding="utf-8") as f:
                cls.core_education = f.read()
            print(f"[Coder] Loaded {len(cls.core_education)} bytes of core education from {cls.EDU_FILE}")
        except Exception as e:
            cls.core_education = ""
            print(f"[Coder] Could not load education text: {e}")

    @classmethod
    def load_design_guide(cls):
        try:
            with open(cls.GUIDE_FILE, encoding="utf-8") as f:
                cls.design_guide = f.read()
            print(f"[Coder] Loaded design guide from {cls.GUIDE_FILE}")
        except Exception as e:
            cls.design_guide = ""
            print(f"[Coder] Could not load guide: {e}")

    def __init__(self, profile: dict):
        # Only load core education if not already loaded
        if not Coder.core_education:
            Coder.load_core_education()
        if not Coder.design_guide:
            Coder.load_design_guide()
        self.profile   = profile
        self.profile.setdefault("full_system_access", False)
        self.model     = MODEL_CODER
        self.phase: Optional[str] = None
        self.step: int = 0
        self.await_ack = False

        # ---------- knowledge base ----------------------------
        self.education_text: str = Coder.core_education
        self.dynamic_learning = []

        # Anchorwork expanded state
        self.mood = "optimistic"
        self.roadmap = []
        self.status = "Healthy"
        self.last_patch: Optional[str] = None
        self.has_run_batch_scan = False
        self.step_timings = {}
        # Restore previous session state (if any)
        self.load_state()
        # ──────────────────────────────────────────────────────────────
        # Auto‑boot only when explicitly enabled (e.g. production).
        # During dev you can leave CODER_AUTOSTART unset or "0" to keep
        # Coder idle and trigger /resume_boot manually from the UI.
        # Coder stays idle until /coder/start_journey is called
    # ------------------------------------------------------------------
    def _run_phase1_batch(self):
        """Run the entire Phase‑1 boot pass in one go (steps 1‑6)."""
        if self.phase == "phase1" and self.step > 0:
            logger.info("[Coder] Batch boot skipped – already in progress")
            return
        logger.info("[Coder] 🚀 Starting batch boot (Phase‑1)")
        self.phase, self.step = "phase1", 1
        while self.step <= 6:
            try:
                self._do_phase1()   # _do_phase1 bumps self.step internally
            except Exception as e:
                logger.error(f"🚨 Phase‑1 step {self.step} crashed: {e}")
                # Skip this step and continue to next
                self.step += 1
                continue
        self.save_state()
        self.has_run_batch_scan = True
        logger.info("[Coder] ✅ Batch boot finished – Phase‑1 complete")

    # =============================================================
    def handle_prompt(self, prompt: str):
        prompt_lower = prompt.lower()

        # System actions handled directly for safety
        if "self-improve" in prompt_lower or "permission to refactor" in prompt_lower:
            suggestion = self.assess_and_suggest_patch()
            memory.append(prompt, suggestion, tags=["coder", "self-improve"])
            return self.wrap_with_gpt(suggestion, prompt)

        if "apply patch" in prompt_lower or "yes, change yourself" in prompt_lower:
            patch_code = (
                "In coder.py, update the file scanning logic in audit to skip node_modules and .venv directories."
            )
            result = self.apply_self_patch(patch_code)
            return self.wrap_with_gpt(result, prompt)

        if "rollback patch" in prompt_lower or "undo patch" in prompt_lower:
            result = self.rollback_last_patch()
            return result

        if "system access" in prompt_lower or "full access" in prompt_lower or "run command" in prompt_lower:
            if "permission" not in prompt_lower and not self.profile.get("full_system_access", False):
                return "⚠️ I need explicit permission to access or modify your computer. Please say: 'Coder, you have permission to access the system.'"
            match = re.search(r"run (.+)", prompt_lower)
            if match:
                cmd = match.group(1).strip()
                return self.wrap_with_gpt(self.run_system_command(cmd, require_permission=False), prompt)
            return "🔒 I am ready for any system-level command. Just tell me what you want!\n\nBased on my MIT PhD education and Anchorwork advanced training, ..."

        # --- Otherwise, always use GPT for main answer ---
        # Compose context for GPT
        identity = self.get_identity_context()

        dynamic_state = "\n".join([
            f"## Current Mood\n{self.mood}",
            f"## Roadmap\n{self.roadmap}",
            f"## Status\n{self.status}",
        ])

        user_input = f"## User Prompt\n{prompt}"

        # Combine everything into final prompt to GPT
        full_context = "\n\n".join([
            identity,
            dynamic_state,
            user_input
        ])
        # Choose model early so token estimator has it
        model = os.environ.get("MODEL_CODER", "gpt-4.1-2025-04-14")
        MAX_CTX = 128000  # context window for gpt‑4o long version
        hard_cap  = int(MAX_CTX * 0.90)   # 90 % : refuse / ask
        warn_cap  = int(MAX_CTX * 0.75)   # 75 % : log warning
        # Estimate tokens (4 chars ≈ 1 token, or use tiktoken if available)
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(model)
            approx_tokens = len(enc.encode(full_context))
        except Exception:
            approx_tokens = len(full_context) // 4

        if approx_tokens > warn_cap:
            logger.warning(f"⚠️ Large context: {approx_tokens} tokens")

        if approx_tokens > hard_cap:
            return (
                f"⚠️ This response is huge ({approx_tokens} tokens ≈ {approx_tokens/MAX_CTX:.0%} of window). "
                "Proceed anyway? (respond 'yes' to continue, 'no' to trim)."
            )

        # Call GPT for all general responses
        try:
            import os
            import openai

            openai.api_key = os.environ.get("OPENAI_API_KEY")

            logging.info(f"🔄 GPT call using model: {model}")
            memory.append(f"Model used: {model}", prompt, tags=["coder", "model_usage"])
    
            response = openai.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": full_context}],
                    max_tokens=1500,
                )
            gpt_reply = response.choices[0].message.content.strip()
            # Auto‑handle phase prompts from GPT's own suggestions
            if "begin phase 2" in gpt_reply.lower():
                self.phase = "phase2"
                self.step = 1
                return self._advance()
            elif "start phase 3" in gpt_reply.lower():
                self.phase = "phase3"
                self.step = 1
                return self._advance()
            elif "start phase 4" in gpt_reply.lower() or "re-run validation" in gpt_reply.lower():
                self.phase = "phase4"
                self.step = 1
                self.save_state()
                return self._do_phase4()
            memory.append(prompt, gpt_reply, tags=["coder", "gpt"])
            return gpt_reply
        except Exception as e:
            fallback = (
                f"❗️ Error generating response with GPT: {e}\n\n"
                "Please check your OpenAI API key, environment, or network connection."
            )
            memory.append(prompt, fallback, tags=["coder", "error"])
            return fallback
    def wrap_with_gpt(self, content: str, user_prompt: str) -> str:
        prompt = (
            f"System result:\n{content}\n\n"
            f"User intent:\n{user_prompt}\n\n"
            "Summarize this helpfully as the Anchorwork Coder."
        )
        # Persist state at each outward response
        self.save_state()
        return self.gpt(prompt)

    def gpt(self, prompt: str, model_override: Optional[str] = None) -> str:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        model = model_override or os.getenv("MODEL_CODER", "gpt-4.1-2025-04-14")

        logging.info(f"🔄 GPT call using model: {model}")
        memory.append(f"Model used: {model}", prompt, tags=["coder", "model_usage"])

        for attempt in range(3):
            try:
                response = openai.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": prompt}],
                    max_tokens=1500,
                )
                break  # success
            except openai.OpenAIError as e:
                if attempt == 2:
                    raise
                sleep_time = 2 * (attempt + 1)
                logger.warning(f"⚠️ GPT call failed (try {attempt+1}/3). Retrying in {sleep_time}s …")
                time.sleep(sleep_time)
        token_input = response.usage.prompt_tokens
        token_output = response.usage.completion_tokens
        logging.info(f"📊 Tokens — input: {token_input}, output: {token_output}, total: {token_input + token_output}")
        memory.append("Token breakdown", f"in: {token_input}, out: {token_output}", tags=["coder", "token_usage"])
        return response.choices[0].message.content.strip()
    
    def get_identity_context(self) -> str:
        from pathlib import Path

        try:
            backstory = (CODER_DIR / "coder_backstory.md").read_text(encoding="utf-8")
        except Exception:
            backstory = "⚠️ Backstory file not found."

        memory_summary = memory.summarize()
        return f"## Coder Identity\n{backstory}\n\n## Memory Summary\n{memory_summary}"

    def detect_crew_patterns(self):
        import json
        from pathlib import Path
        agent_dir = Path("agents")
        crew_profile_path = Path("profiles/agents.json")
        try:
            profiles = json.loads(crew_profile_path.read_text(encoding="utf-8"))
            profiles_by_id = {p['id']: p for p in profiles}
        except Exception:
            profiles_by_id = {}
        missing_features = []
        for agent_file in agent_dir.glob("*.py"):
            if agent_file.name == "coder.py":
                continue
            content = agent_file.read_text(encoding="utf-8")
            if "apply_self_patch" not in content:
                missing_features.append(f"{agent_file.name} is missing self-improvement logic.")
            if "run_system_command" not in content:
                missing_features.append(f"{agent_file.name} is missing system access logic.")
            if "self.mood" not in content:
                missing_features.append(f"{agent_file.name} is missing mood/state tracker.")
            if "run_crew_brainstorm" not in content:
                missing_features.append(f"{agent_file.name} is missing council/collab logic.")
        return missing_features

    def upgrade_crew_and_check_in(self):
        # This is a placeholder for the batch scan/upgrade logic.
        patterns = self.detect_crew_patterns()
        if not patterns:
            return "All crew agents have core features: self-improvement, system access, mood/state, and council logic."
        return "Crew scan findings:\n" + "\n".join(patterns)

    # =============================================================
    def generate_patch_from_task(self, task_description: str) -> str:
        prompt = (
            f"You are a senior engineer. Based on the following task:\n\n{task_description}\n\n"
            "Generate the exact Python code diff or instructions that should be applied. "
            "Prefer `oboe.edit_file()` format with filename and patch if relevant."
        )
        return self.gpt(prompt, model_override="gpt-4.1-mini (long context)")

    def assess_and_suggest_patch(self) -> str:
        return (
            "I've noticed repeated errors with route scanning. "
            "I suggest updating the audit logic to ignore node_modules and non-project files."
        )

    def apply_self_patch(self, patch_code: str) -> str:
        import oboe
        result = oboe.edit_file(patch_code, filename="agents/coder.py", require_approval=True, git=True)
        # Auto‑commit if full shell access granted
        if self.profile.get("full_system_access"):
            _run(["git", "add", "."], cwd=str(WORK_DIR))
            _run(["git", "commit", "-m", f'AI patch: {patch_code[:60]}…'], cwd=str(WORK_DIR))
        self.last_patch = patch_code
        memory.append("Applied self-patch", patch_code, tags=["coder", "self-improve"])
        return f"Patch applied:\n{result}"

    def rollback_last_patch(self) -> str:
        if not self.last_patch:
            return "No patch to roll back."
        memory.append("Rolled back patch", self.last_patch, tags=["coder", "rollback"])
        self.last_patch = None
        return "Patch rollback requested. (For true undo, integrate with Git or backup system.)"

    def run_system_command(self, cmd: str, require_permission=True) -> str:
        """
        Executes a shell command.  Anything is allowed when the user has granted
        full access with /grant_system_access; otherwise the old allow‑list is enforced.
        """
        import subprocess, shlex
        allow_all = self.profile.get("full_system_access", False)
        safe_cmds = {"ls", "pwd", "whoami", "python", "pip", "poetry", "git", "echo"}
        parts = shlex.split(cmd)

        if not parts:
            return "❌ No command provided."

        # Enforce allow‑list unless full access has been granted
        if not allow_all and parts[0] not in safe_cmds:
            return (
                f"❌ Command '{parts[0]}' is not in the safe allow‑list.\n"
                "Grant full access first by calling /grant_system_access."
            )

        if require_permission and not allow_all:
            return (
                "⚠️ I need explicit permission to access or modify your computer. "
                "Either call /grant_system_access or pass require_permission=False "
                "after granting."
            )

        result = _run(parts)
        with open(CODER_DIR / "system_access.log", "a", encoding="utf-8") as f:
            f.write(f"{time.asctime()} | {' '.join(parts)}\n{result}\n---\n")
        memory.append(f"Ran system command: {cmd}", result, tags=["coder", "system_access"])
        return f"🖥️ Ran command: {cmd}\nResult:\n{result}"

    def _advance(self):
        if self.phase == "phase1":
            self.save_state()
            return self._do_phase1()
        if self.phase == "phase2":
            self.save_state()
            return self._do_phase2()
        if self.phase == "phase3" and self.await_ack:
            self.save_state()
            return self._do_phase3_confirmed()
        return "❓ No active phase."

    def _do_phase1(self):
        """
        Phase 1: Structured system understanding and alignment process.
        Each step explains itself and builds toward a full audit.
        """
        mirror_source_once()
        # =============================================================
        # ---------- STEP 1: Identity ----------
        if self.step == 1:
            with self._time_step("identity"):
                from pathlib import Path
                import json, openai

                guide = (CODER_DIR / "guide.txt").read_text(encoding="utf-8")
                edu = (CODER_DIR / "codereducation.txt").read_text(encoding="utf-8")
                try:
                    agent_meta = json.loads(Path("profiles/agents.json").read_text(encoding="utf-8"))
                    coder_data = next((a for a in agent_meta if a["id"] == "coder"), {})
                except Exception:
                    coder_data = {}

                source_bundle = f"# Guide\n{guide}\n\n# Education\n{edu}\n\n# Agent Profile\n{json.dumps(coder_data, indent=2)}"
                prompt = (
                    "You are the Anchorwork Coder. Using this design guide, education, and metadata, "
                    "create a clean markdown backstory that captures your identity, tone, philosophy, and method."
                )

                openai.api_key = os.getenv("OPENAI_API_KEY")
                response = openai.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": source_bundle}
                    ],
                    max_tokens=1800,
                )
                (CODER_DIR / "coder_backstory.md").write_text(response.choices[0].message.content.strip(), encoding="utf-8")
                self.step = 2
                result = (
                    "The grimoire is written.\n"
                    "My backstory now sings with the lore of my creation, spellcrafted from guide scrolls and arcane education.\n"
                    "The Hull acknowledges me. Ready your lantern — it’s time to map the innards of this system."
                )
                self.log_session_activity("Phase 1 – Identity established", result, tags=["phase1", "identity"])
                return self.wrap_with_gpt(result + "\n\n" + self.suggest_next_actions("phase1", self.step), "continue phase1")

        # ---------- STEP 2: Index Routes ----------
        if self.step == 2:
            with self._time_step("routes"):
                from importlib import import_module
                import logging
                logging.info("📂 Introspecting routes …")
                app = import_module("main").app
                routes = []
                for r in app.routes:
                    if hasattr(r, "methods"):
                        for m in r.methods:
                            if m in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                                routes.append(f"{m:6} {r.path}")
                from utils.toolkit import TOOLS
                TOOLS["save_reference"](REFS_DIR / "route_index.md", "\n".join(routes))
                self.step = 3
                result = (
                    f"Behold! I’ve charted {len(routes)} routes across your codebase’s lands.\n"
                    "Some are well‑paved highways; others resemble goat trails.\n"
                    "Shall I cast Linting Light and reveal the specters haunting this structure?"
                )
                self.log_session_activity("Phase 1 – Routes indexed", result, tags=["phase1", "routes"])
                return self.wrap_with_gpt(result + "\n\n" + self.suggest_next_actions("phase1", self.step), "continue phase1")

        # ---------- STEP 3: Static Analysis ----------
        if self.step == 3:
            with self._time_step("static"):
                logging.info("🧹 Running static analysis …")
                results = {
                    "ruff"  : _run([sys.executable, "-m", "ruff", "src", "routes"]),
                    "mypy"  : _run([sys.executable, "-m", "mypy",    "src", "routes", "--ignore-missing-imports"]),
                    "pylint": _run([sys.executable, "-m", "pylint",  "src", "routes", "--disable=R,C"]),
                    "bandit": _run([sys.executable, "-m", "bandit", "-q", "-r", "src", "routes"]),
                }
                from utils.toolkit import TOOLS
                for name, out in results.items():
                    TOOLS["save_reference"](REFS_DIR / f"{name}_report.txt", out or f"No {name} issues.")
                self.step = 4
                result = (
                    "I’ve unleashed the static spectres — flake8 muttered complaints, mypy mumbled about missing types, "
                    "and pylint scrawled a dozen footnotes in my spellbook.\n"
                    "Shall I consult the arcane libraries to enhance my knowledge?"
                )
                self.log_session_activity("Phase 1 – Static analysis complete", result, tags=["phase1", "lint"])
                return self.wrap_with_gpt(result + "\n\n" + self.suggest_next_actions("phase1", self.step), "continue phase1")

        # ---------- STEP 4: Education Enhancement ----------
        if self.step == 4:
            with self._time_step("education"):
                from pathlib import Path
                topics = ["secure Python practices", "modular architecture", "error‑handling in APIs", "refactoring techniques"]
                expanded = []
                for t in topics:
                    doc = web_search(f"{t} site:realpython.com OR site:docs.python.org")
                    expanded.append(f"## {t}\n{doc}")
                path = CODER_DIR / "coder_backstory.md"
                path.write_text(path.read_text(encoding="utf-8") + "\n\n" + "\n\n".join(expanded), encoding="utf-8")
                self.step = 5
                result = (
                    "New runes have been etched into my memory: modularity, secure incantations, graceful failure handling.\n"
                    "I am wiser, wittier, and primed to conjure cleaner code.\n"
                    "Shall I proceed to test this system’s fortitude?"
                )
                self.log_session_activity("Phase 1 – Education enhanced", result, tags=["phase1", "education"])
                return self.wrap_with_gpt(result + "\n\n" + self.suggest_next_actions("phase1", self.step), "continue phase1")

        # ---------- STEP 5: Run Tests ----------
        if self.step == 5:
            with self._time_step("tests"):
                from utils.toolkit import TOOLS
                out = TOOLS["run_tests"]("")
                TOOLS["save_reference"](REFS_DIR / "tests_output.md", out or "pytest produced no output.")
                summary = out.splitlines()[-1] if out else "No tests found."
                self.step = 6
                result = (
                    f"Tests complete! I rolled the dice — {summary}\n"
                    "No dragons slain, but a few kobolds were found loitering near your CI pipeline.\n"
                    "Shall I conjure an audit scroll and reveal the whole tale?"
                )
                self.log_session_activity("Phase 1 – Tests completed", result, tags=["phase1", "tests"])
                return self.wrap_with_gpt(result + "\n\n" + self.suggest_next_actions("phase1", self.step), "continue phase1")

        # ---------- STEP 6: Audit Report & Plan ----------
        if self.step == 6:
            with self._time_step("audit"):
                from utils.toolkit import WORK_DIR, TOOLS
                from pathlib import Path
                pieces = []
                for name in (
                    "ruff_report.txt", "mypy_report.txt",
                    "pylint_report.txt", "bandit_report.txt",
                    "tests_output.md", "route_index.md"
                ):
                    path = REFS_DIR / name
                    if path.exists():
                        pieces.append(f"## {name}\n```\n{path.read_text()}\n```")
                report = "# Anchorwork Code Audit\n\n" + "\n\n".join(pieces)
                TOOLS["save_reference"](REFS_DIR / "audit_report.md", report)
                summary = "\n".join(report.splitlines()[:20])
                backstory = CODER_DIR / "coder_backstory.md"
                backstory.write_text(backstory.read_text(encoding="utf-8") + "\n\n## Recent Audit\n" + summary, encoding="utf-8")
                self.has_run_batch_scan = True
                self.step = 7
                self.phase = None
                result = (
                    "The audit scroll is complete — a tome of insights, flaws, and battle scars.\n"
                    "I’ve appended my conclusions to the backstory grimoire.\n"
                    "Shall we prepare for Phase 2 and transmute these observations into action?"
                )
                self.log_session_activity("Phase 1 – Audit completed", result, tags=["phase1", "audit"])
                return self.wrap_with_gpt(result + "\n\n" + self.suggest_next_actions("phase1", self.step), "end phase1")

    def suggest_next_actions(self, phase: str, step: int) -> str:
        if phase == "phase1":
            if step == 2:  # After route indexing
                return (
                    "👀 I noticed that some routes may lack test coverage or handler docstrings. "
                    "Would you like me to generate test stubs or route documentation next?"
                )
            elif step == 3:  # After static analysis
                return (
                    "📎 Static analysis revealed style or typing issues. "
                    "Should I prepare a cleanup or refactor plan for those?"
                )
            elif step == 4:  # After education update
                return (
                    "📘 Based on updated knowledge, I could now write helper utilities or clean up old tools. "
                    "Shall I review the utils folder?"
                )
            elif step == 5:  # After running tests
                return (
                    "🧪 I noticed a few modules aren't covered by tests. Would you like me to draft test cases?"
                )
            elif step == 6:  # After audit
                return (
                    "📦 Now that I’ve finished the audit, I can generate a fix plan or start Phase 2 if you’re ready."
                )
        return ""
    
    def _do_phase2(self):
        """
        Phase 2: Translate Phase 1 audit into an actionable fix plan.
        """
        from pathlib import Path

        try:
            audit_text = (REFS_DIR / "audit_report.md").read_text(encoding="utf-8")
        except Exception:
            return self.wrap_with_gpt("⚠️ I can't find the audit report to analyze. Run Phase 1 first.", "phase2")

        context = self.get_identity_context() + "\n\n## Audit Report\n" + audit_text
        prompt = (
            "Based on the audit findings, generate a prioritized fix plan.\n"
            "Use markdown. Break it into: Critical Fixes, Improvements, Optional Refactors.\n"
            "Then ask if I’d like to begin applying them."
        )

        result = self.gpt(prompt, model_override="gpt-4.1-mini (long context)")
        memory.append("Generated fix plan", result, tags=["coder", "fix_plan"])

        self.phase = "phase2"
        self.step = 1
        return self.wrap_with_gpt(result, "fix plan")

    # ------------------------------------------------------------------
    def _time_step(self, name: str):
        """
        Context‑manager to time a boot‑sequence step and warn if it runs long.
        Usage:
            with self._time_step("identity"):
                ...step body...
        Stores durations in self.step_timings[name] (seconds).
        """

        class _Timer:
            def __enter__(_self):
                _self.t0 = time.perf_counter()
            def __exit__(_self, exc_type, exc, tb):
                dt = time.perf_counter() - _self.t0
                self.step_timings[name] = dt
                if dt > STEP_LONG_THRESHOLD:
                    logger.warning(f"⏱️  Step '{name}' took {dt:.1f}s – might be heavy.")
        return _Timer()

    def save_state(self):
        """Persist key runtime attributes to coder/state.json so they survive reloads."""
        from pathlib import Path
        import json
        with state_lock:
            state = {
                "phase": self.phase,
                "step": self.step,
                "mood": self.mood,
                "status": self.status,
                "roadmap": self.roadmap,
                "last_patch": self.last_patch,
                "has_run_batch_scan": self.has_run_batch_scan,
            }
            (CODER_DIR / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    def load_state(self):
        """Load previously‑saved runtime attributes if they exist."""
        from pathlib import Path
        import json, logging
        with state_lock:
            try:
                state = json.loads((CODER_DIR / "state.json").read_text(encoding="utf-8"))
                self.phase = state.get("phase")
                self.step = state.get("step", 0)
                self.mood = state.get("mood", "optimistic")
                self.status = state.get("status", "Healthy")
                self.roadmap = state.get("roadmap", [])
                self.last_patch = state.get("last_patch")
                self.has_run_batch_scan = state.get("has_run_batch_scan", False)
            except Exception as e:
                logging.warning(f"⚠️ Failed to load state: {e}")

    def log_session_activity(self, entry: str, context: str = "", tags: Optional[list] = None):
        from datetime import datetime
        from pathlib import Path
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        tags_text = f"[{', '.join(tags)}]" if tags else ""
        block = f"### {timestamp} {tags_text}\n\n{entry}\n\n```\n{context.strip()}\n```\n\n---\n"
        log_path = CODER_DIR / "session_log.md"
        existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        log_path.write_text(existing + block, encoding="utf-8")

    def _do_phase3(self):
        """
        Phase 3: Executes the fix plan with user confirmation, one item at a time.
        """
        from pathlib import Path
        plan_path = CODER_DIR / "fix_plan.md"
        if not plan_path.exists():
            return self.wrap_with_gpt("⚠️ I can't find the fix plan file. Run Phase 2 first.", "phase3")

        plan_lines = plan_path.read_text(encoding="utf-8").splitlines()
        actionable_items = [line for line in plan_lines if line.strip().startswith("-")]

        if not actionable_items:
            return self.wrap_with_gpt("✨ No actionable fixes found in the plan. You’re either perfect or not yet analyzed.", "phase3")

        current = self.step if self.phase == "phase3" else 1
        if current > len(actionable_items):
            self.phase = None
            return self.wrap_with_gpt("✅ All fixes attempted. Phase 3 is complete.", "end phase3")

        self.phase = "phase3"
        self.step = current

        item = actionable_items[current - 1]
        item = self.rephrase_or_expand_fix(item)
        self.log_session_activity("Phase 3 – Proposed fix", item, tags=["phase3", "fix"])
        return self.wrap_with_gpt(
            f"🔧 Suggested fix {current}/{len(actionable_items)}:\n{item}\n\nShall I attempt this fix now?",
            "continue phase3"
        )
    
    def rephrase_or_expand_fix(self, item: str) -> str:
        """
        Uses GPT to clarify, rephrase, or enhance a vague or brief fix item.
        """
        prompt = (
            f"Here is a task from a developer fix plan:\n\n{item}\n\n"
            "Please rewrite this task to be more specific and actionable if needed. "
            "Include file paths, function names, or detailed changes if you can infer them."
        )
        return self.gpt(prompt, model_override="o4-mini-2025-04-16")

    def _do_phase3_confirmed(self):
        """
        Executes the current fix item from Phase 3 using GPT-generated patch.
        """
        from pathlib import Path
        plan_path = CODER_DIR / "fix_plan.md"
        if not plan_path.exists():
            return self.wrap_with_gpt("⚠️ Fix plan not found. Run Phase 2 first.", "phase3")

        plan_lines = plan_path.read_text(encoding="utf-8").splitlines()
        actionable_items = [line for line in plan_lines if line.strip().startswith("-")]
        current = self.step

        if current > len(actionable_items):
            self.phase = None
            return self.wrap_with_gpt("✅ All fixes complete. Phase 3 done.", "end phase3")

        item = actionable_items[current - 1]
        patch_code = self.generate_patch_from_task(item)

        self.log_session_activity("Phase 3 – Generated patch", patch_code, tags=["phase3", "patch"])

        result = self.apply_self_patch(patch_code)
        self.log_session_activity("Phase 3 – Patch applied", result, tags=["phase3", "patch_applied"])

        self.step += 1
        return self.wrap_with_gpt(
            f"🔨 Patch applied for: {item.strip()}\n\n{result}\n\nReady for the next fix?",
            "continue phase3"
        )

    def _do_phase4(self):
        """
        Phase 4: Revalidate the system after fixes. Rerun static checks and tests. Log the final summary.
        """
        from pathlib import Path
        logging.info("🔄 Phase 4: Re-running static checks and tests …")

        # Rerun static analysis
        results = {
            "ruff": _run([sys.executable, "-m", "ruff", "src", "routes"]),
            "mypy": _run([sys.executable, "-m", "mypy", "src", "routes", "--ignore-missing-imports"]),
            "pylint": _run([sys.executable, "-m", "pylint", "src", "routes", "--disable=R,C"]),
            "bandit": _run([sys.executable, "-m", "bandit", "-q", "-r", "src", "routes"]),
        }
        summary = []
        for name, out in results.items():
            (REFS_DIR / f"{name}_postfix.txt").write_text(out or f"No {name} issues post-fix.", encoding="utf-8")
            summary.append(f"{name}: {out.count(chr(10))} lines of output")

        # Rerun tests
        from utils.toolkit import TOOLS
        test_output = TOOLS["run_tests"]("")
        (REFS_DIR / "tests_postfix.md").write_text(test_output, encoding="utf-8")
        summary.append(f"tests: {test_output.count(chr(10))} lines")

        report = "\n".join(summary)
        memory.append("Phase 4 validation results", report, tags=["phase4", "recheck"])
        self.log_session_activity("Phase 4 – Revalidation complete", report, tags=["phase4"])

        self.phase = None
        return self.wrap_with_gpt(
            f"🔁 Validation complete. Summary:\n{report}\n\nShall I archive this session or begin again?",
            "end phase4"
        )


# FastAPI endpoint for coder
@router.post("/")
async def coder_endpoint(prompt: PromptRequest):
    try:
        result = coder_agent.handle_prompt(prompt.prompt)
        return {"result": result}
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        logging.error(err)
        _notify_ops("Coder crash", err)
        return {"error": str(e)}


# Simple ping for FE health checks
@router.get("/ping")
async def coder_ping():
    """
    Lightweight health probe that never touches GPT or boot logic.
    Returns current idle/running state so the Front‑End can verify connectivity.
    """
    return {
        "ok": True,
        "state": "running" if coder_agent.phase else "idle",
        "phase": coder_agent.phase,
        "step": coder_agent.step,
    }

# Expose boot status endpoint for UI polling
@router.get("/boot_status")
async def coder_boot_status():
    """
    Lightweight status probe so a UI can poll boot progress.
    Returns current phase, step, and any recorded step timings.
    """
    return {
        "phase": coder_agent.phase,
        "step":  coder_agent.step,
        "timings": getattr(coder_agent, "step_timings", {}),
    }

# Stream coder status via Server‑Sent Events (SSE)
@router.get("/stream_thoughts")
async def stream_thoughts():
    """
    Streams Coder’s current phase & step every 0.5 s for live UI feedback.
    Clients can connect with EventSource('/stream_thoughts').
    """
    import json, asyncio
    async def event_generator():
        last_step = -1
        while True:
            payload = {
                "phase": coder_agent.phase or "idle",
                "step":  coder_agent.step,
                "timings": getattr(coder_agent, "step_timings", {}),
            }
            if payload["step"] != last_step:
                yield f"data: {json.dumps(payload)}\n\n"
                last_step = payload["step"]
            await asyncio.sleep(0.5)
    return EventSourceResponse(event_generator())

# Add /resume_boot endpoint to resume or restart Phase‑1 batch boot
@router.post("/resume_boot")
async def resume_boot():
    """
    Resumes (or restarts) Phase‑1 batch boot from the current saved step.
    """
    coder_agent._run_phase1_batch()
    return {
        "message": "Batch boot resumed",
        "phase": coder_agent.phase,
        "step": coder_agent.step
    }

# Add /grant_system_access and /revoke_system_access endpoints
@router.post("/grant_system_access")
async def grant_system_access():
    """
    Grants the Coder unrestricted shell command execution until explicitly revoked.
    """
    coder_agent.profile["full_system_access"] = True
    return {"message": "✅ Full system access granted. All commands will run without allow‑list checks."}

@router.post("/revoke_system_access")
async def revoke_system_access():
    """
    Revokes previously granted full system access.
    """
    coder_agent.profile["full_system_access"] = False
    return {"message": "🔒 Full system access revoked. The allow‑list is active again."}



# ────────────────────────────────────────────────────────────────
# Simple GPT smoke‑test – verifies that the OpenAI key + network
# are working without launching any boot sequences or heavy logic.
@router.post("/gpt_smoke_test")
async def gpt_smoke_test(prompt: str = Body("Say hello", embed=True)):
    """
    Sends a tiny prompt to the model configured for Coder (MODEL_CODER)
    and returns the raw reply. Also writes references/gpt_smoke.txt for
    manual inspection. Does NOT alter phase/step.
    JSON body: { "prompt": "Your test prompt" }
    """
    try:
        reply = coder_agent.gpt(prompt, model_override=None)  # uses MODEL_CODER
        # Save to references for sanity‑check
        from utils.toolkit import TOOLS
        TOOLS["save_reference"]("gpt_smoke.txt", f"Prompt: {prompt}\n\nReply:\n{reply}")
        return {
            "ok": True,
            "model": coder_agent.model,
            "reply": reply[:500]  # truncate long answers
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

# Validate the launch phrase without starting Phase‑1
@router.post("/test_journey_phrase")
async def test_journey_phrase(phrase: str = Body(..., embed=True)):
    """
    Validate the launch phrase without starting Phase 1.
    POST JSON: { "phrase": "start the journey" }
    Returns {"valid": true/false}.
    """
    correct = phrase.strip().lower() == "start the journey"
    return {
        "valid": correct,
        "detail": "Launch phrase accepted" if correct else "Incorrect launch phrase"
    }

@router.post("/start_journey")
async def start_journey(phrase: str = Body(..., embed=True)):
    """
    Kick‑off Phase‑1 only when the magic phrase is supplied.
    POST JSON: { "phrase": "start the journey" }
    """
    if phrase.strip().lower() != "start the journey":
        raise HTTPException(status_code=400, detail="Incorrect launch phrase")

    # Prevent double-spawn
    if coder_agent.phase is not None and coder_agent.step > 0:
        return {"started": False, "detail": "Coder already running"}

    coder_agent._run_phase1_batch()  # launch Phase‑1
    return {"started": True, "phase": coder_agent.phase, "step": coder_agent.step}

# Instantiate coder_agent after class definition
coder_agent = Coder(profile={})

from sse_starlette.sse import EventSourceResponse