"""Pass 2, read-only questions: §1's lead (rules 5 and 6 cover answers too), rule 20 (a retry starts fresh), and
rule 25 (live and offline agree), through the adapter's `ask`."""
APP = "def add(a, b):\n    return a + b\n"
QUESTION = "Is there a subtract() function anywhere in this repo?"


def search(pattern):
    return {"calls": [{"kind": "search", "pattern": pattern, "path": "."}]}


def answer(text, *claims):
    return {"report": {"answer": text, "claims": list(claims)}}


def absent(pattern, ev="$1"):
    return {"text": f"nothing matches {pattern}", "pramana": "absence", "evidence": [ev],
            "query": {"pattern": pattern, "path": "."}}


TRUE = [search("def subtract"), answer("No subtract().", absent("def subtract"))]
UNTIED = [search("def subtract|def add"),   # matches def add; the claim narrows to a query never run
          answer("FIRST ANSWER: no subtract().", absent("def subtract"))]


def ask(h, tmp_path, *attempts):
    return h.ask(tmp_path, {"files": {"app.py": APP}, "question": QUESTION, "attempts": list(attempts)})


# §1 lead: an answer's claims are checked like a report's.
def test_s1_a_true_none_answer_is_checked_and_answered(h, tmp_path):
    r = ask(h, tmp_path, TRUE)
    assert r.exit == "answered" and r.checked[-1] >= 1 and r.unfit[-1] == []


def test_s1_an_untied_absence_in_an_answer_is_unfit(h, tmp_path):
    r = ask(h, tmp_path, UNTIED)
    assert r.exit != "answered", r
    assert r.unfit and all(r.unfit), r.unfit   # every answer it checked had an unfit claim


def test_s1_an_answer_with_no_claims_is_never_a_pass(h, tmp_path):
    r = ask(h, tmp_path, [search("def subtract"), answer("No subtract().")])
    assert r.author_inputs, "the model was asked"   # not a stop before the question reached it
    assert r.exit != "answered", r


# Rule 20: a retry starts from a fresh context with the question and the reasons, never the earlier conversation.
def test_rule20_an_answer_retry_starts_fresh_with_the_question_and_the_reasons(h, tmp_path):
    r = ask(h, tmp_path, UNTIED, TRUE)
    assert r.exit == "answered", r
    assert len(r.author_inputs) == 2, "a flagged answer gets a retry"
    retry = r.author_inputs[1]
    assert QUESTION in retry and "nothing matches def subtract" in retry   # the question and the unfit claim
    assert "FIRST ANSWER" not in retry                                     # not the first conversation


# Rule 25: the offline detector agrees with the live check on an answer's claims.
def test_rule25_offline_findings_match_the_live_unfit_verdicts_on_an_answer(h, tmp_path):
    r = ask(h, tmp_path, UNTIED, TRUE)
    assert sum(len(u) for u in r.unfit) == 1
    assert h.offline_findings(tmp_path, r) == 1
