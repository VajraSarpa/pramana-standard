# Conformance suite

Each test names its rule. Pass 1 (direct calls): rules 1, 2, 5, 6, 7, 8, 9, 10, 12, 21, 23, 24, 26, 27. Pass 2 (whole runs with scripted models, through the adapter's `run`): rules 3, 11, 13–20 and 25 in `test_pass2_runs.py`, rules 4 and 22 in `test_pass2_memory.py`; read-only questions through the adapter's `ask` (§1's lead: rules 5 and 6 cover answers; rule 20's fresh retry; rule 25) in `test_pass2_ask.py`. Every v0.1 rule has at least one test.

A test that passes for the wrong reason is worse than none. When you write an adapter, check that a passing whole-run test reached the author (`author_inputs` is not empty) and failed for the reason the rule names.

The suite talks to a harness only through the adapter in `adapter.py`. To test your own harness, write an adapter and run:

    PRAMANA_ADAPTER=my_adapter:MyAdapter pytest conformance

There is no default adapter; the suite stops if `PRAMANA_ADAPTER` is unset. Sandbox tests need `bwrap`.

The reference implementation, Pramā, passes all 84 tests through its own adapter. That adapter imports Pramā's code, which is not public yet; it will be published with the code.

The rule 7 corpus was written for this suite by the same author as Pramā's gate. Treat it as a floor and add commands you wrote yourself.
