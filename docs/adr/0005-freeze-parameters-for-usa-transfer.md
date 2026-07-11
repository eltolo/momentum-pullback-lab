# ADR 0005 — Freeze parameters for the USA transfer test

## Status
Accepted

## Context
The final phase of the lab includes a transfer test from Argentina to the USA.
If parameters are recalibrated during that step, the experiment stops measuring transferability and starts measuring a second optimization cycle.
That would weaken the lab's ability to claim that the underlying logic travels across markets.

## Decision
The USA transfer test in T270 will use frozen principles and frozen parameters from the approved Argentina base version.
No parameter recalibration will be allowed inside the transfer run.

## Consequences
### Positive
- The transfer result remains interpretable as a portability test.
- The lab can distinguish a portable idea from a market-specific fit.
- Failure in USA becomes informative instead of ambiguous.

### Negative
- The first USA result may look worse than what a tuned USA variant could achieve.
- Some potentially useful market-specific improvements are intentionally postponed.

## Alternatives considered
### Recalibrate lightly for USA
Rejected because even minor retuning blurs whether the result came from transferability or fresh optimization.

### Rebuild a new USA-specific version directly
Rejected because that would answer a different research question.
