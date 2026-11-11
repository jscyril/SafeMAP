# SafeMAP v3: front-end changes

v2 refused about 311 of 356 held-out units before any translation. v3 widens
the front end so more units reach translation; acceptance still requires the
unchanged checks (cargo check, tests, per-unit Clippy, differential testing
against the sanitized C oracle).

## Changes

Bugs fixed:

- **libclang crash on typedef'd array parameters** (`va_list`). sds and printf
  silently fell back to the regex parser. `c_analyzer._clang_parameter`.
- **CRLF sources**: libclang byte offsets were applied to text read with
  newline translation, so function bodies were taken from the wrong place
  (printf.c). Bodies are now sliced from raw bytes.
- **Integer casts flagged as pointer casts**: `(size_t)len`, `(int)pad` were
  "unsupported". Only casts of pointers are now. `eligibility._casts_pointer_to_integer`.
- **Casts dropped by deterministic synthesis**: `(int)f(x)` and `(double)a / b`
  lost their casts. Rules that return an expression now refuse casts.
- **Harness name collision**: a C parameter named `r`, `v` or `e` collided with
  harness variables; parameter variables are now `sm_p_<name>`.

Wider analysis:

- **Read-only globals**: a non-const global that no function writes is
  treated as a constant (`GlobalInfo.written`). Arrays of `const` elements are
  immutable.
- **Allocator hooks**: a function-pointer global initialized to
  `malloc`/`free`/... is treated as that allocator in units that only call
  it; units that assign it still count as touching state
  (`GlobalInfo.allocator_hook`). Assumption: the harness never installs
  custom allocators.
- **memcpy/memmove/memset** no longer force `unsafe_required`; on planned
  slices they become `copy_from_slice`, `copy_within`, `fill`.
- **Struct handles**: a non-const pointer used only through `->` is `&T`, or
  `&mut T` when a field is written.
- **Pointers passed on**: a pointer only passed to other functions takes the
  role of the callee's parameter, resolved bottom-up to a fixed point
  (`pointer_classifier.resolve_passed_pointers`). A small table of read-only
  libc string functions is included.
- **String cursors**: a `const char *` scanned with `++` or indexing, with no
  length partner, that never escapes, plans as `&str` (`c_string_cursor`).
- **Borrow idioms**: plain `&T`/`&mut T` roles count as plan patterns, so such
  units are planned (previously rejected with no stated reason).
- **String fields**: `char *` struct fields map to `Option<String>` (NULL is
  `None`); the harness builds and compares them on both sides. Assumption:
  the field holds NUL-terminated text, as for `const char *` parameters.

- **Pointers to whole arrays**: `state_t *` (`uint8_t (*)[4][4]`) plans as
  `&mut [[u8; 4]; 4]` (`array_reference`); the harness builds, passes, and
  prints nested arrays on both sides.
- **String cursors are plain `char` only**: `const uint8_t *` key and buffer
  pointers are bytes, not NUL-terminated text.

Harness and planner fixes found by the first guided run:

- **Early stop on undefined inputs**: once more than half a unit's inputs
  are undefined in C, the unit cannot pass; the oracle stops restarting case
  by case (same verdict, much faster on sds).
- **C integer literals**: constant mining parsed `"0123456789"` (inside a
  string) as a number and crashed the semver run; strings are skipped and
  octal/hex literals are parsed as C does.
- **Program hooks**: printf.c expects the program to define `_putchar`.
  Missing symbols are linked to stubs that report a runtime error and abort,
  so inputs reaching them are undefined and other units are tested normally.
  (Ignoring unresolved symbols instead made the C binary fail to start, which
  looked like a defined abort on every input: unsound, and rejected.)
- **ctype predicates**: `return isalpha(c);` returns an unspecified nonzero
  value (glibc: 1024), so such units plan a `bool` return.
- **C strings without NUL**: plans for `char *` string parameters state that
  the end of the `&str` stands for the terminating `'\0'`.

Providers:

- `llm.fallbacks` lists providers to use, in order, once one is out of quota.
  A daily-quota 429 moves on at once (per-minute limits are still retried);
  ordinary errors never switch. Each unit records the models that answered
  (`synthesis/summary.json`, `models`), and switches are logged in
  `synthesis/provider_switches.json`. A result produced by more than one model
  must report the mix.
- Requests send a `User-Agent`; Groq's edge rejects the urllib default.
- The CLI reads `.env` (shell variables take precedence).

## Effect on development data (front end only)

`scripts/front_end_funnel.py` over the ten v2 held-out libraries (now v3
development data):

| | Units | Candidates | Planned |
|---|---:|---:|---:|
| v2 | 356 | 183 | 50 |
| v3 | 353 | 250 | 106 |

The unit count drops by 3 because sds and printf are now parsed by libclang
instead of the regex fallback, which had invented functions. The no-LLM lane
is unchanged (6 accepted): deterministic rules cover few shapes, so the new
units need the LLM lane.

## First guided run (development data)

`research/v3_development.yaml`, gemini-3.5-flash-lite (no fallback used),
one run, before the "found by the first guided run" fixes above:

| Library | v2 accepted | v3 accepted |
|---|---:|---:|
| microtar | 2 | 2 |
| parson | 3 | 6 |
| sds | 2 | 4 |
| tinyexpr | 21 | 21 |
| argparse | 0 | 2 |
| json-parser | 1 | 1 |
| printf | 0 | 0 |
| semver | 3 | 17 |
| tiny-AES-c | 1 | 7 |
| tiny-regex-c | 4 | 5 |
| Total | 37 / 356 | 65 / 353 |

v2 is the amendment-3 result (per-unit Clippy, run 1). semver was rerun
after the literal fix.

## Second guided run (development data)

Same configuration, with all fixes above. gemini-3.5-flash-lite answered
every request (84 units); no provider switch.

| Library | Run 1 | Run 2 | Gained in run 2 |
|---|---:|---:|---|
| microtar | 2 | 2 | |
| parson | 6 | 6 | |
| sds | 4 | 4 | |
| tinyexpr | 21 | 22 | `negate_logical_not` |
| argparse | 2 | 2 | |
| json-parser | 1 | 1 | |
| printf | 0 | 2 | `_strnlen_s`, `_is_digit` |
| semver | 17 | 17 | |
| tiny-AES-c | 7 | 7 | |
| tiny-regex-c | 5 | 8 | `matchalpha`, `matchwhitespace`, `matchcharclass` |
| Total | 65 / 353 | 71 / 353 | |

No unit accepted in run 1 was lost. The printf and tiny-regex gains follow
from the program-hook stubs, the ctype `bool` rule and the NUL constraint;
`negate_logical_not` was a translation error in run 1 and is likely model
variance. `matchmetachar` still fails differential testing. printf's other
13 units need the callback parameter (`out`), which is not supported yet.

## Third guided run (development data)

Commit `f49358e`, same configuration; gemini-3.5-flash-lite answered every
request (84 units), no provider switch. 71 / 353 accepted, with two changes
from run 2: tiny-regex-c gained `matchmetachar` (9), and tiny-AES-c lost
`InvMixColumns` (6), whose translation differed from C on all 1000 inputs
(model variance). Raw outputs:
`SafeMAP_versions/v3/raw_runs/run3` (runs 1 and 2 were in `/tmp` and were
lost in a reboot; only the tables above remain).

**v3 on development data, three runs: 65–71 / 353** (v2: 36–37 / 356).

## Evaluating v3

The ten v2 held-out libraries informed these changes and are now development
data. A v3 result needs a newly selected, sealed held-out corpus (the
`safemap_v2_candidates` pool minus the libraries already used) and a freeze
record, following the v2 protocol. Use `research/v3_development.yaml` for
development runs; it is the v2 configuration with per-unit Clippy on.

## Not done yet

- parson's value graph (`JSON_Value` with parent back-pointers and a union):
  most of its refusals, including the returned-pointer ones. Needs whole
  data-structure translation (an arena or `Rc`/`Weak`) and API-level
  differential tests rather than per-function ones.
- Callback parameters (printf's `out`), `void *` user data.
- Mutable `char *` buffers without a length (`&mut String`); sds strings keep a
  header before the pointer and must stay excluded.
- Pointer-to-pointer outputs (`const char **end`).
- Mutable global state that is written (6 units).
