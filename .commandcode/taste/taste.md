# Taste

## Communication
- Communicates in French: plans, documentation, and section headers are written in French (with English technical terms). Respond in French. Confidence: 0.9

## Workflow
- Plan-first workflow with an explicit validation gate: no source code changes until the implementation plan is validated (project rule from AGENTS.md). Confidence: 0.85
- Plans are structured as phased remediations: severity-ranked phases (Critique/Haute → Moyenne → Basse → Tests), a traceability matrix mapping anomaly IDs to files/lines/severity/phase, "User Review Required" callouts, and "Open Questions" sections for design decisions needing user sign-off. Confidence: 0.8
- Expects audit findings to be verified against the real source code before implementation (each anomaly confirmed or refuted by reading the actual lines). Confidence: 0.75
