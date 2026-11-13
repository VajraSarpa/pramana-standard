# Pramāṇa Harness Standard

Rules for a coding-agent harness: the program between a language model and a repository that decides what the agent may run, what counts as evidence, and when a change is ready for a person.

The name comes from pramāṇa, the Indian philosophical term for a means of valid knowledge. The standard's central idea is that every piece of context has a source (seen, told, inferred, searched for and not found), and that a claim can't be stronger than its source.

- [STANDARD.md](STANDARD.md): the rules, v0.1 draft. 27 rules in 7 sections; each has the rule, why, the evidence, and a conformance test. An appendix covers measuring a harness against a plain baseline.
- [conformance/](conformance/): a pytest suite a third party can run against any harness through an adapter. Each test names its rule.

## Status

v0.1 is a draft from one builder's runs (323 logged sessions, October to mid-November 2026, across four projects and lab repos). It will change. The reference implementation is Pramā; this repository holds the standard and its conformance suite, not Pramā's code.

## Where the evidence is

The catches come mostly from execution and memory: checks the harness runs itself (a test that fails on the base and passes after, mutation testing of new tests, checks in a sandbox) and settled decisions with guards that fail when a change breaks them. Those rules have the most cases behind them.

The claim rules (§1) have thin live evidence. The inference rule has fired live twice and the absence check a handful of times, always on a real defect in how a claim was stated, never on a false conclusion. The āpta registry has only been tested on planted instructions. Read those rules as design, checked offline, not yet proven in use.

The harness was also measured against a plain baseline, and the losses are published (appendix): on the latest rerun it was stricter but not more accurate.

## Reading it

Start with the Terms section, then §2 (validity gate) and §4 (verification), which carry most of the weight. Evidence notes say when a rule rests on one case.

## License

The text of the standard (STANDARD.md and this README) is licensed under [CC BY 4.0](LICENSE): you may copy and adapt it with credit. The code in `conformance/` is licensed under [MIT](LICENSE-CODE). Only versions published in this repository are the Pramāṇa Harness Standard; an adapted version needs its own name.
