# ADR 0004 — Use a primary approval gate on 5k and 10k, treating 15k as capacity stretch

## Status
Accepted

## Context
The lab evaluates the strategy across three capital scales: 5k, 10k, and 15k USD MEP.
Requiring the same level of robustness at the largest scale from day one can kill a strategy that is valid at realistic initial deployment size.
At the same time, ignoring the larger scale entirely would hide capacity limitations.

## Decision
The primary approval gate will require robustness at 5k and 10k USD MEP.
The 15k scale will remain mandatory to report, but it will be interpreted primarily as a capacity and stretch signal, not as a hard pass/fail gate for initial approval.

## Consequences
### Positive
- Keeps the lab aligned with realistic initial deployment size.
- Preserves visibility into scale deterioration without over-penalizing early viability.
- Separates strategy validity from later capacity ceiling.

### Negative
- A strategy may pass while already showing degradation at 15k.
- Reporting must be explicit so that 15k weakness is not ignored or hidden.

## Alternatives considered
### Require robustness at 5k, 10k, and 15k equally
Rejected because it makes initial approval too strict relative to plausible deployment size.

### Ignore 15k until much later
Rejected because capacity is part of the economic model and should be visible from the start.
