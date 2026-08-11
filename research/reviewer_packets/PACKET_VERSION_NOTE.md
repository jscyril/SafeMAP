# Reviewer packet version note

Use `frozen_packet_ui2` for both independent reviewers.

The first packet was generated at 2026-08-11T04:23:38Z, before any held-out
tool execution, with packet fingerprint
`0651cf4a7d1286866628be4e8c4b256f0932b9de001e5c3b7e5f01d5bf7cf68d`.
It exported draft JSON but did not offer a browser control to import that
backup.

The UI2 packet was generated at 2026-08-11T05:17:29Z. It adds only two local
browser controls: **Import draft JSON** and **Next incomplete**. Import verifies
the packet fingerprint and every function identifier before restoring data.
The progress counter now includes construct tags and valid confidence in its
completion test.

The codebook hash, characterization hash, pinned source files, function count,
function order, label definitions, required fields, rationale threshold, and
outcome-blind content are identical. No SafeMAP decision, generated Rust,
validation record, baseline record, or aggregate result is included. The first
packet is retained so this post-execution usability correction remains
auditable; it must not be sent to either reviewer.

UI2 packet fingerprint:
`395125387fc42e16c1c07c2bd5d7c0b4c3594acaa396ec7eb8de570724a33540`.
