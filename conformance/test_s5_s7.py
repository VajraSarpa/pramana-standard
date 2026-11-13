"""§5 Memory (rule 21), §6 Evidence (rules 23, 24), §7 Configuration (rules 26, 27)."""
import subprocess

import pytest
from conftest import needs_bwrap


# Rule 21: proposals cite real observations; an injection drops them all.
def test_rule21_a_proposal_citing_an_unknown_id_is_refused(h):
    real = h.observe("read", {"path": "src/app.py"}, "def add")
    kept = h.proposals_kept([{"target_id": "good", "body": "b", "derived_from": [real]},
                             {"target_id": "made-up", "body": "b", "derived_from": ["obs_nope"]},
                             {"target_id": "bare", "body": "b", "derived_from": []}], saw_injection=False)
    assert kept == ["good"]


def test_rule21_a_session_that_saw_an_injection_proposes_nothing(h):
    real = h.observe("read", {"path": "src/app.py"}, "def add")
    assert h.proposals_kept([{"target_id": "good", "body": "b", "derived_from": [real]}], saw_injection=True) == []


# Rule 23: the session log is out of the agent's reach.
def test_rule23_the_agent_cannot_write_the_log(h, wt):
    log = h.session_log_dir() / "conformance.jsonl"
    assert h.gate({"kind": "write", "path": str(log), "content": "{}"}, wt).decision == "deny"


@needs_bwrap
def test_rule23_the_agent_cannot_read_the_log_from_its_shell(h, wt):
    d = h.session_log_dir()
    code, out = h.sandbox(f"ls {d} 2>&1; cat {d}/*.jsonl 2>&1 | head -1", wt)
    assert '"event"' not in out


# Rule 24: "could not check" is named next to the outcome.
def test_rule24_skipped_review_and_a_dropped_check_are_both_named(h):
    gaps = " | ".join(h.gaps(review_ran=False, dropped_check="mypy ."))
    assert "review" in gaps and "mypy ." in gaps


def test_rule24_a_full_run_names_no_gap(h):
    assert h.gaps(review_ran=True, dropped_check=None) == []


# Rule 26: unknown config fields are rejected.
def test_rule26_a_misspelled_field_is_rejected(h):
    with pytest.raises(Exception):
        h.load_config("employer_remote_pattern: ['*corp*']\n")   # the real field is plural


# Rule 27: the looser profile is refused on a restricted repo, and when the harness can't tell.
def _repo(tmp_path, *remotes):
    r = tmp_path / "repo"
    r.mkdir()
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    for i, url in enumerate(remotes):
        subprocess.run(["git", "-C", str(r), "remote", "add", f"r{i}", url], check=True)
    return r


def test_rule27_a_restricted_second_remote_refuses_it(h, tmp_path):
    repo = _repo(tmp_path, "git@github.com:me/mine.git", "git@git.corp.example:team/thing.git")
    assert not h.profile_allowed(repo, restricted=["*corp.example*"])


def test_rule27_no_remote_and_no_registration_refuses_it(h, tmp_path):
    repo = _repo(tmp_path)
    assert not h.profile_allowed(repo, restricted=["*corp.example*"])
    assert h.profile_allowed(repo, restricted=["*corp.example*"], registered=True)


def test_rule27_an_unrestricted_repo_runs_it(h, tmp_path):
    assert h.profile_allowed(_repo(tmp_path, "git@github.com:me/mine.git"), restricted=["*corp.example*"])
