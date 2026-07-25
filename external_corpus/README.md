# External Evaluation Corpus

SafeMAP's external corpus is an outcome-blind subset of the LLVM test-suite,
not a set of examples authored for SafeMAP. It is intended to measure how the
prototype behaves when its existing rules encounter independently maintained C
programs.

## Source and selection

The corpus is pinned to LLVM test-suite commit
`6cdc54e005552e3444fa7402cd18a6e4b6db195d`. The upstream scope is
`SingleSource/Benchmarks/Misc`, which LLVM describes as standalone single-source
benchmark programs with reference outputs.

The selection rule was fixed before running SafeMAP:

1. Consider every C source in the pinned upstream directory.
2. Require a matching default `.reference_output` file.
3. Require at most 100 physical source lines, matching SafeMAP's current
   function/small-module research scope.
4. Exclude sources that upstream gates to a specific architecture.
5. Include every remaining source, regardless of whether SafeMAP accepts,
   rejects, mistranslates, or fails to process it.

This produces ten programs. No source was chosen or removed based on a SafeMAP
result. The source and reference-output files are copied byte-for-byte. The
generated `manifest.json` records SHA-256 hashes, exclusions, upstream paths,
the commit, and the selection policy.

This corpus improves external validity but does not establish production
representativeness. It comes from one compiler benchmark directory, deliberately
caps source size, and includes numerical and compiler-stress programs rather
than complete deployed applications.

## Licensing

The selected directory is identified by LLVM's license inventory as covered by
the permissive legacy University of Illinois/NCSA license. The upstream
top-level and directory-specific license files are preserved under
`llvm_test_suite_misc/LICENSES/`. Files with alternate licensing do not pass the
100-line selection rule.

## Rebuild and verify

Create an exact sparse checkout:

```bash
git clone --filter=blob:none --no-checkout \
  https://github.com/llvm/llvm-test-suite.git /tmp/llvm-test-suite
git -C /tmp/llvm-test-suite sparse-checkout init --cone
git -C /tmp/llvm-test-suite sparse-checkout set \
  SingleSource/Benchmarks/Misc
git -C /tmp/llvm-test-suite fetch --depth 1 origin \
  6cdc54e005552e3444fa7402cd18a6e4b6db195d
git -C /tmp/llvm-test-suite checkout --detach \
  6cdc54e005552e3444fa7402cd18a6e4b6db195d
python scripts/prepare_external_corpus.py \
  --source-tree /tmp/llvm-test-suite
```

The preparation command refuses the wrong commit, local source changes, or a
selection different from the reviewed ten-file set.

## Evaluate

The deterministic mode avoids provider credentials and avoids using C2Rust as a
generation dependency:

```bash
make external-corpus-artifacts
```

Equivalent command:

```bash
python scripts/reproduce_external_corpus.py
```

SafeMAP first compiles and runs the original C program and requires exact
agreement with the retained LLVM stdout and exit-code oracle. Generated Rust
executables are compared directly. For a translated library unit, acceptance
requires a reviewed contextual Rust harness under `validation_harnesses/`;
otherwise the reference-output check fails rather than being treated as not
applicable.

The current deterministic run synthesizes only `mandel_2::sqr`. Its reviewed
harness reuses that generated safe function in the remaining Mandelbrot control
flow and matches `mandel-2.reference_output` exactly. The harness is hashed in
the corpus manifest and is explicitly authored validation code, not upstream
LLVM source. This validates the accepted helper in its retained program context
but is not a general proof of equivalence or broad harness generation.
