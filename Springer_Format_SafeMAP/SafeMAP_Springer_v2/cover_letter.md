Dear Editor,

We submit "SafeMAP: Analysis-Guided Planning and Per-Function Validation for
Safe C-to-Rust Translation" for consideration in *Automated Software
Engineering*.

An earlier version of this work was submitted to the journal [manuscript ID,
date] and declined before review. Its frozen evaluation accepted 0 of 142
translation units, and its baselines produced no usable output, so it could
not support any conclusion. We traced that outcome to six implementation
defects, each of which independently forced the result to zero (Section 4.1).
Because we inspected the earlier test libraries while finding these defects,
we did not reuse them as test data. Instead we:

- corrected the defects and froze the implementation under a new, sealed
  evaluation protocol;
- evaluated the system on ten newly selected C libraries (9,456 lines, 356
  units), chosen by a fixed rule before any execution on them. The addition of
  six libraries after the first four results were seen is disclosed and
  reported separately;
- replaced the earlier baselines with one-shot LLM baselines with and without
  SafeMAP's planned interfaces, a rules-only configuration, and C2Rust in a
  pinned container;
- added per-function differential testing against the original C function
  under AddressSanitizer and UndefinedBehaviorSanitizer, mutation analysis of
  that check, three repeated LLM runs, and component ablations; and
- removed claims that depended on an unadjudicated human labeling study.

The revised results are modest and reported as such. Across three runs SafeMAP
accepted 12-16 of 356 held-out units and the one-shot baseline, given the same
planned interfaces, 9-15; rules alone accepted 1 and C2Rust 0. The same model given
only the C sources accepted 1. We do not claim that the guided loop beats the
interface-given baseline; the contribution is the interface planning, which
the plain baseline and the ablations isolate. Most units are refused before translation, for recorded reasons
(global state, C types without a safe interface, unsafe memory operations).
We believe the contribution is a conservative migration method whose every
acceptance is checked against the original C, and an empirical account of
what currently blocks safe automatic migration of production C.

All code, protocols, manifests, raw results, and table-generation scripts are
public. The manuscript is not under consideration elsewhere. All authors
approved the submission.

Sincerely,
Jacob Sebastian Cyril (corresponding author), on behalf of the authors
Department of Computer Science, CHRIST (Deemed to be) University, Bangalore
