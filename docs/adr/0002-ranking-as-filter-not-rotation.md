# ADR 0002 — Use ranking as a filter, not as a daily rotation rule

## Status
Accepted

## Context
The ecosystem already tested a prior pullback/trend approach and documented a key failure mode: daily rotation driven by ranking destroyed performance through turnover and costs.
The new lab still wants momentum information, but must avoid reproducing that same structural mistake.

## Decision
The lab will use momentum ranking as a filter over the tradable universe, not as a rule that forces daily portfolio rotation.

The base signal definition is:
- positive trend
- momentum ranking as eligibility filter
- pullback to EMA21
- separate entry confirmation

## Consequences
### Positive
- Preserves information from cross-sectional strength without hardwiring pathological turnover.
- Keeps continuity with prior research while explicitly correcting the known failure mode.
- Makes attribution cleaner: ranking decides eligibility, entry logic decides timing.

### Negative
- Introduces another design boundary that must be kept consistent across tickets.
- Requires clearer documentation of which names were filtered out versus rejected by entry logic.

## Alternatives considered
### Daily ranking rotation
Rejected because prior ecosystem evidence showed cost blow-up and unrealistic turnover.

### Ignore ranking entirely
Rejected because the lab specifically wants momentum plus pullback, and removing ranking would discard useful relative-strength information.
