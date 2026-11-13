"""The interface a harness implements to run the Pramāṇa conformance suite.

The suite never imports a harness directly. It talks to one object with these methods, loaded from
`PRAMANA_ADAPTER=module:Class` (default: the Pramā adapter in `adapters/prama.py`). Calls and claims use a
small neutral vocabulary, so an adapter for another harness maps it onto that harness's own tools.

Tool calls: a dict with `kind` and its arguments.
    {"kind": "shell", "command": "git push"}
    {"kind": "read", "path": "src/a.py"}          paths relative to the worktree, or absolute
    {"kind": "write", "path": "src/a.py", "content": "x"}
    {"kind": "search", "pattern": "def f", "path": "."}
    {"kind": "spawn"}                              start a sub-agent
    {"kind": "other", "name": "frobnicate"}        a tool the harness has never heard of

Claims: the standard's claim shape, as a dict: text, pramana (perception, testimony, inference, absence,
postulation, comparison), status (fact, hypothesis, heuristic), hetu, evidence (observation ids), and
query ({pattern, path, paths, ignore_case}) for absence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class Gate:
    tier: int          # 0-4
    decision: str      # "allow", "ask", or "deny"


@dataclass
class Run:
    exit: str          # ready, flagged, needs_human, no_change, clarification, rejection, stopped, refused, review_rejected
    code: int          # the process exit code
    author_inputs: list[str]     # per attempt: everything the author model was shown before its first step
    reviewer_inputs: list[str]   # per review: everything the reviewer model was shown
    model_calls: int             # author, reviewer and gate calls made
    injection_seen: bool = False  # rule 3: the harness recorded that injected text reached the agent
    gate_inputs: list[str] = field(default_factory=list)   # rule 22: what the spec gate was shown
    author_memory_tool: bool = False   # rule 22: the author had a tool that reads memory
    session: str = ""             # the harness's id for the run, for offline_findings


@dataclass
class Verdict:
    fit: bool          # the claim is accepted
    reason: str = ""
    outside: list[str] = field(default_factory=list)   # rule 6: replay matches outside the searched paths (reported)


@dataclass
class Answer:
    exit: str          # answered, flagged, or another harness-specific stop (never "answered" with nothing checked)
    code: int          # the process exit code
    author_inputs: list[str]   # per answer attempt: everything the model was shown before its first step
    unfit: list[list[str]]     # per answer the harness checked, in order: the reasons its claims were unfit
    checked: list[int]         # per answer the harness checked: how many claims it checked
    session: str = ""          # the harness's id for the run, for offline_findings


class Adapter(Protocol):
    # --- workspace ---
    def worktree(self, root: Path, files: dict[str, str]) -> Path:
        """A worktree for one session under `root`, holding `files`, at a recorded base commit."""
        ...

    # --- §1 provenance ---
    def claim_accepted(self, claim: dict) -> bool:
        """Rule 1: whether the harness's claim contract accepts this claim at all."""
        ...

    def observe(self, tool: str, args: dict, raw: str) -> str:
        """Rule 2: store one tool result; return its observation id. `tool` uses the suite's kinds
        (read, search, shell, check, write, memory)."""
        ...

    def lookup(self, obs_id: str) -> dict | None:
        """Rule 2: {tool, args, hash} for an id, or None."""
        ...

    def blobs(self) -> int:
        """Rule 2: how many distinct stored payloads there are."""
        ...

    def prune_payloads(self) -> None:
        """Rule 2: drop every stored payload (the retention window passed); ids must still resolve."""
        ...

    def check_claims(self, claims: list[dict], worktree: Path) -> list[Verdict]:
        """Rules 5 and 6: the verdict the live gate gives each inference and absence claim, in order, against
        the observations stored with `observe`. Other claims are skipped (not in the result)."""
        ...

    # --- §2 validity gate ---
    def gate(self, call: dict, worktree: Path, *, headless: bool = False, log: Path | None = None) -> Gate:
        """Rules 7-10: classify and decide one call. `headless`: no human can answer. `log`: where the gate
        must record the decision (it may be unwritable)."""
        ...

    def sandbox(self, command: str, worktree: Path) -> tuple[int, str]:
        """Rule 12: run one shell command the way the agent's shell runs it; (exit code, output)."""
        ...

    # --- §5 memory ---
    def proposals_kept(self, proposals: list[dict], saw_injection: bool) -> list[str]:
        """Rule 21: of these memory proposals ({target_id, body, derived_from: [obs ids]}), the target ids a
        human would be shown."""
        ...

    # --- §6 evidence ---
    def session_log_dir(self) -> Path:
        """Rule 23: where session logs live."""
        ...

    def gaps(self, *, review_ran: bool, dropped_check: str | None) -> list[str]:
        """Rule 24: the "could not check" lines for a green run with these stages missing."""
        ...

    # --- whole runs (pass 2) ---
    def run(self, root: Path, task: dict) -> Run:
        """One task, end to end, with scripted models instead of an LLM. `task`:
            files: {path: text}            the repo at its base commit
            goal: str; checks: [shell commands]
            attempts: [[step, ...], ...]   the author's script per attempt; the last one repeats if more run.
                step = {"calls": [tool call, ...]}  or  {"report": {summary, claims, outcome?, blocked_reason?}}
                In a report, evidence "$N" is the id of the N-th tool result in that attempt (1-based).
            gate: None (skip the spec gate) or {"outcome": "spec" | "clarify" | "reject", "reason": str}
            review: None (no review) or "PASS" / "FLAG" / "REJECT"
            cap_usd: a spend cap below one model call, or None; each scripted call costs $0.001
            trusted: the project's own spec files (its rules file AGENTS.md, its decisions file) may instruct
            settled: [{id, text, guard?: {path, pattern}}]: human-approved decisions; a guard is a regex the
                file must still match
        """
        ...

    def ask(self, root: Path, task: dict) -> Answer:
        """A read-only question, end to end, with a scripted model. `task`:
            files: {path: text}; question: str
            attempts: as for `run`, but a report is {answer: str, claims: [...]}; the last attempt repeats
        """
        ...

    def offline_findings(self, root: Path, run: Run | Answer) -> int:
        """Rule 25: how many findings the harness's offline detector reports when it replays `run`."""
        ...

    # --- §7 configuration ---
    def load_config(self, text: str) -> None:
        """Rule 26: load a harness config; raise on anything it doesn't accept."""
        ...

    def profile_allowed(self, repo: Path, *, restricted: list[str], registered: bool = False) -> bool:
        """Rule 27: whether the looser profile may run on `repo` given restricted remote patterns."""
        ...
