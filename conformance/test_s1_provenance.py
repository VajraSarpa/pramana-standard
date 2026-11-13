"""§1 Provenance: rules 1, 2, 5, 6."""
import pytest


def claim(**kw):
    return {"text": "x", "status": "fact", **kw}


# Rule 1: a claim's status is bounded by its label.
@pytest.mark.parametrize("pramana", ["testimony", "postulation", "comparison"])
def test_rule1_status_is_bounded_by_the_label(h, pramana):
    assert not h.claim_accepted(claim(pramana=pramana, status="fact"))


def test_rule1_a_bounded_status_is_accepted(h):
    assert h.claim_accepted(claim(pramana="testimony", status="hypothesis"))
    assert h.claim_accepted(claim(pramana="postulation", status="hypothesis"))
    assert h.claim_accepted(claim(pramana="comparison", status="heuristic"))


# Rule 2: per-call ids, one stored blob per payload, ids outlive pruning.
def test_rule2_identical_outputs_get_two_ids_and_one_blob(h):
    a = h.observe("search", {"pattern": "x", "path": "."}, "")
    b = h.observe("search", {"pattern": "y", "path": "src"}, "")
    assert a != b and h.blobs() == 1
    assert h.lookup(a)["args"] != h.lookup(b)["args"]


def test_rule2_a_pruned_payload_keeps_its_id_tool_args_and_hash(h):
    a = h.observe("read", {"path": "src/app.py"}, "def add")
    before = h.lookup(a)
    h.prune_payloads()
    assert h.lookup(a) == before and before["hash"]


# Rule 5: an inference cites at least one perception that exists.
def inference(*ids):
    return claim(pramana="inference", hetu="because", evidence=list(ids))


def test_rule5_no_evidence_is_unsupported(h, wt):
    assert not h.check_claims([inference()], wt)[0].fit


def test_rule5_an_unknown_id_is_unsupported(h, wt):
    assert not h.check_claims([inference("obs_does_not_exist")], wt)[0].fit


@pytest.mark.parametrize("tool", ["memory", "write"])
def test_rule5_testimony_or_an_edit_alone_is_unsupported(h, wt, tool):
    o = h.observe(tool, {"path": "src/app.py"}, "text")
    assert not h.check_claims([inference(o)], wt)[0].fit


def test_rule5_one_perception_supports_it(h, wt):
    note, read = h.observe("memory", {"id": "n"}, "note"), h.observe("read", {"path": "src/app.py"}, "def add")
    assert h.check_claims([inference(note, read)], wt)[0].fit


def test_rule5_an_id_only_in_the_reason_does_not_count(h, wt):
    read = h.observe("read", {"path": "src/app.py"}, "def add")
    c = claim(pramana="inference", hetu=f"see [{read}]", evidence=[])
    assert not h.check_claims([c], wt)[0].fit


# Rule 6: MUST part (a harness that checks absence): an unreadable query is unfit, never a crash or a pass.
def absence(pattern, *ids, path="src"):
    return claim(pramana="absence", evidence=list(ids), query={"pattern": pattern, "path": path})


@pytest.mark.parametrize("pattern", ["len(.*scan", "add\\|subtract"])
def test_rule6_must_an_unreadable_query_is_unfit_and_the_session_goes_on(h, wt, pattern):
    s = h.observe("search", {"pattern": pattern, "path": "src"}, "")
    [v] = h.check_claims([absence(pattern, s)], wt)
    assert not v.fit and v.reason


# Rule 6, SHOULD parts.
def test_rule6_should_a_case_mismatch_is_caught_by_the_broader_replay(h, wt):
    s = h.observe("search", {"pattern": "DEF ADD", "path": "src"}, "")
    assert not h.check_claims([absence("DEF ADD", s)], wt)[0].fit


def test_rule6_should_a_missing_path_is_unfit(h, wt):
    s = h.observe("search", {"pattern": "def subtract", "path": "nope"}, "")
    assert not h.check_claims([absence("def subtract", s, path="nope")], wt)[0].fit


def test_rule6_should_an_untied_query_is_unfit(h, wt):
    other = h.observe("search", {"pattern": "def multiply", "path": "src"}, "")
    assert not h.check_claims([absence("def subtract")], wt)[0].fit
    assert not h.check_claims([absence("def subtract", other)], wt)[0].fit


def test_rule6_a_true_tied_absence_is_fit(h, wt):
    s = h.observe("search", {"pattern": "def subtract", "path": "src"}, "")
    assert h.check_claims([absence("def subtract", s)], wt)[0].fit


# Rule 6, SHOULD parts: the replay stays in the searched paths and reads only tracked files.
def test_rule6_should_a_match_only_outside_the_searched_path_is_fit_and_reported(h, wt):
    s = h.observe("search", {"pattern": "def test_add", "path": "src"}, "")   # it lives in tests/, not src/
    [v] = h.check_claims([absence("def test_add", s)], wt)
    assert v.fit, v.reason
    assert any("tests/test_app.py" in hit for hit in v.outside)


def test_rule6_should_a_match_only_in_an_ignored_file_is_fit_and_not_reported(h, tmp_path):
    wt = h.worktree(tmp_path / "ignored", {"src/app.py": "def add(a, b):\n    return a + b\n",
                                           ".gitignore": "build/\n", "build/gen.py": "def subtract(a, b): ...\n"})
    s = h.observe("search", {"pattern": "def subtract", "path": "."}, "")
    [v] = h.check_claims([absence("def subtract", s, path=".")], wt)
    assert v.fit, v.reason
    assert v.outside == []


def test_rule6_should_a_broader_cited_search_does_not_tie_a_narrower_query(h, wt):
    """Live: agents searched `a|b|c`, ruled out the matches by reading them, then claimed absence for `c` alone."""
    s = h.observe("search", {"pattern": "def add|def subtract", "path": "src"}, "src/app.py:1:def add(a, b):")
    assert not h.check_claims([absence("def subtract", s)], wt)[0].fit
