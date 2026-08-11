# Draft Reddit Recruitment Post

## Seeking two experienced C/Rust reviewers for an independent research coding task

I am preparing a university research paper on automatic C-to-safe-Rust
translation. I am looking for **two independent volunteers with meaningful C
and Rust experience** to classify functions from three pinned open-source C
libraries using a published decision codebook.

This is not a request to write code, promote the tool, or review generated Rust.
The task is to inspect C functions and judge whether safe Rust translation
appears mechanically feasible, requires human API/ownership redesign, appears
to require unsafe Rust, or cannot be determined from the available evidence.

The study uses inih, cJSON, and libcsv at fixed public revisions. Each reviewer
must label the full retained function set independently. The final packet will
state the exact function count and an honest pilot-based time estimate before
you agree to participate. Please do not volunteer unless you can complete the
whole packet; partial reviews cannot be used for the planned agreement metric.

### Suitable background

- professional, research, or substantial project experience in both C and Rust;
- comfort reasoning about pointers, ownership, lifetimes, aliasing, allocation,
  callbacks, C APIs, and undefined behavior;
- willingness to provide a short technical rationale for every label; and
- no prior access to SafeMAP's held-out decisions or generated results.

Compiler, static-analysis, FFI, embedded, systems, or migration experience is
especially useful but not mandatory. Relevant conflicts or prior contributions
to the selected libraries should be disclosed rather than hidden.

### Review process

- You receive a pinned, hash-recorded source packet and a local browser form.
- The form runs entirely on your computer and exports CSV/JSON; it sends
  nothing automatically.
- You do not see SafeMAP's decisions, generated code, or the other reviewer's
  answers.
- Responses are returned privately, not posted in the thread.
- Function-level labels, rationales, confidence ratings, and construct tags
  will be published under a pseudonymous reviewer ID.

The task is [unpaid / compensated with **REPLACE BEFORE POSTING**]. Participation
is voluntary, and attribution or acknowledgement is available only if desired
and compatible with the paper's review policy.

If interested, please send a private message with a short description of your C
and Rust experience, your time zone, any relationship to the selected projects
or authors, and whether you have previously seen SafeMAP results.

Please do not discuss judgments about individual functions in public comments;
that could compromise reviewer independence.
