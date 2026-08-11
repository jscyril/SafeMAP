# SafeMAP reviewer website

This directory is the static, outcome-blind web distribution of reviewer
packet UI2. GitHub Pages publishes it at `/SafeMAP/review/`.

The website has no response endpoint, analytics, advertising, or third-party
JavaScript. The review form stores drafts in browser local storage and exports
CSV/JSON locally. Reviewers return both files privately to the coordinator.

Canonical packet SHA-256:
`395125387fc42e16c1c07c2bd5d7c0b4c3594acaa396ec7eb8de570724a33540`.

The website is a presentation surface. Its embedded function inventory,
codebook hash, and exported response schema must remain identical to
`research/reviewer_packets/frozen_packet_ui2`.
