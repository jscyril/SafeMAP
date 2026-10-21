Dear Editors,

We submit "SafeMAP: Analysis-Guided Planning and Per-Function Validation for
Safe C-to-Rust Translation" for consideration in the *Software Quality
Journal*.

Migrating C code to safe Rust removes whole classes of memory errors, but
automatic translators either keep C's pointer conventions in unsafe Rust or
rely on large language models (LLMs) whose output is hard to check. The paper
addresses the quality-assurance side of this problem: when can a translated
function be trusted? SafeMAP translates a C function only when static analysis
finds a safe, testable Rust interface for it. It accepts a translation only if
the code contains no `unsafe` and matches the original C function on generated
inputs, with the C side run under AddressSanitizer and UndefinedBehaviorSanitizer
so that inputs with undefined C behavior are excluded rather than used as
expected outputs. Every other function is refused with a recorded reason.

We evaluated the frozen implementation under a sealed protocol on ten held-out
C libraries (9,456 lines, 356 translation units):

- Across three runs, SafeMAP accepted 12-16 units. A one-shot LLM given
  SafeMAP's planned interfaces accepted 9-15; the same model given only the C
  sources accepted 1. Raw C2Rust accepted none.
- Mutation analysis shows that the per-function check rejects 89% of compiling
  single-operator mutants of accepted functions.
- Most units are refused before translation, mainly because of mutable global
  state and C types with no safe Rust interface. The paper reports these
  reasons as a breakdown of what currently blocks safe automatic migration.

The results are modest and reported as such. We do not claim that SafeMAP's
guided loop beats an LLM given the same planned interfaces; ablations and the
plain-LLM baseline attribute the result to interface planning. We believe the
paper fits the journal's interest in testing, verification, and tools for
achieving software quality: it contributes an acceptance procedure whose every
decision is checked against the original program, and an empirical account of
its reach and its failure modes.

All code, protocols, manifests, raw results, and table-generation scripts are
public (https://doi.org/10.5281/zenodo.23494717). The manuscript is not under
consideration elsewhere. All authors approved the submission.

Sincerely,
Jacob Sebastian Cyril (corresponding author), on behalf of the authors
Department of Computer Science, CHRIST (Deemed to be) University, Bangalore
