# Independent Eligibility Review Package

This directory defines the human-review process for SafeMAP's frozen held-out
evaluation. It is public so that prospective reviewers can inspect the method
before volunteering. The generated reviewer packets do **not** contain SafeMAP
decisions, generated Rust, acceptance outcomes, or aggregate results.

## What the review measures

Reviewers classify whether each C function appears suitable for automatic
translation to safe Rust in principle. This is an eligibility judgment, not a
prediction of whether SafeMAP currently implements the required translation.

Every retained function must be reviewed independently by exactly two people.
The reviewers must not compare answers until both response files have been
submitted and cryptographically hashed. A later adjudicator resolves
disagreements without changing either original response.

## Files

- `REVIEWER_CODEBOOK.md`: definitions, decision tree, examples, and edge cases.
- `REVIEWER_CONSENT_AND_SCREENING.md`: eligibility, conflicts, consent, and
  data-use questions.
- `REDDIT_RECRUITMENT_DRAFT.md`: recruitment text suitable for a programming or
  research community.
- `REVIEWER_HANDOFF.md`: instructions sent privately with a generated packet.
- `COORDINATOR_PREFLIGHT.md`: ethics, privacy, recruitment, and freeze checks
  that must be completed before contacting volunteers.
- `reviewer_response_template.csv`: the response schema.
- `adjudication_template.csv`: the independent adjudication schema.

After the implementation is frozen and the pinned corpus is materialized, run:

```bash
python scripts/characterize_corpus.py \
  --corpus-root external_corpus/conference_heldout \
  --output-json research/results/heldout_characterization.json \
  --output-csv research/results/heldout_functions.csv

python scripts/build_eligibility_reviewer_packet.py \
  --corpus-root external_corpus/conference_heldout \
  --characterization research/results/heldout_characterization.json \
  --output research/reviewer_packets/frozen_packet
```

The generated `review.html` is a local, serverless form. Reviewers should
download the entire packet, open that file in a modern browser, complete all
items, and export both CSV and JSON. The JSON preserves the screening answers;
the CSV is the machine-readable function-label input.

## Privacy and publication

Use stable pseudonymous identifiers such as `reviewer_a` and `reviewer_b` in
the research artifact. Keep names, email addresses, Reddit handles, and consent
records outside the public repository. Tell reviewers before they begin that
their function-level labels, rationales, confidence ratings, and declared
construct tags will be published under the chosen identifier.

Do not promise anonymity that cannot be delivered. A distinctive rationale can
sometimes identify its author even after names are removed.

## Independence rules

A response is eligible only when the reviewer:

1. has enough C and Rust experience to apply the codebook;
2. reports relevant conflicts of interest;
3. has not seen SafeMAP's decisions or held-out generated outputs;
4. completes the assigned corpus without coordinating labels;
5. gives a rationale for each judgment; and
6. agrees that the de-identified response may be published.

Recruitment through Reddit is acceptable only as a way to find volunteers.
Labels should be returned privately, not posted in comments. Public discussion
of specific functions before both reviews finish would break independence.

Before recruitment, ask the research guide whether the exercise requires an
institutional research-ethics determination or approved consent language. Do
not assume that public-source code review is exempt when reviewer responses and
experience information will be collected and published.
