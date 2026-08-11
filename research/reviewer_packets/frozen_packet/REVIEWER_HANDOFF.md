# Private Reviewer Handoff

Thank you for agreeing to review the SafeMAP held-out eligibility corpus.

Before starting:

1. Return the completed consent and screening form privately.
2. Read `REVIEWER_CODEBOOK.md` completely.
3. Verify the SHA-256 values in `packet_manifest.json` if your platform permits.
4. Confirm that the packet contains source and form files but no SafeMAP
   decision, plan, generated Rust, or outcome file.
5. Open `review.html` locally in a current browser.

Enter only the pseudonymous reviewer identifier assigned by the coordinator.
Do not enter your email address or Reddit username into the review form.

For every function, select one label, set confidence from 1 to 5, select the
construct tags that affected the decision, and write a specific rationale. Use
the source links and full pinned source files when the excerpt is insufficient.

The form autosaves to browser local storage, but browser data can be cleared.
Use **Export draft JSON** periodically. When all rows pass validation, export
both final CSV and final JSON. Return both files privately to the coordinator.

Do not:

- look for SafeMAP results in repository branches, issues, or reports;
- consult the other reviewer;
- post function-specific reasoning publicly;
- change the source or function identifiers in the export; or
- include personal information in rationales.

Record external documentation or source history used in the `external_sources`
field of the JSON export. Procedural questions may be sent to the coordinator,
but the coordinator should not advise which label to choose.
