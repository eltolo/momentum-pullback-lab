# ADR 0001 — Evaluate liquidity and tradability by a family of capital scales

## Status
Accepted

## Context
The lab needs a definition of daily tradability that is economically meaningful.
A fixed absolute liquidity threshold is easy to implement, but it hides whether the strategy only works at tiny scale.
A single fixed simulated capital is also fragile: the lab could approve an edge that disappears as soon as capital grows.

## Decision
The lab will evaluate tradability and liquidity against a mandatory family of simulated capital scales, not a single fixed capital.

This affects at least:
- daily tradable universe selection
- liquidity filters
- participation constraints
- interpretation of benchmark comparability
- later portfolio sizing and capacity analysis

## Consequences
### Positive
- Capacity becomes part of the strategy thesis, not an afterthought.
- A signal that only survives at tiny size is exposed early.
- Cross-sectional ranking is tied to executable opportunity, not abstract availability.

### Negative
- T267 and later tickets become more complex.
- Reports must show results conditional on capital scale.
- More scenarios increase runtime and artifact volume.

## Alternatives considered
### Single fixed simulated capital
Rejected because it can overfit the lab to one arbitrary account size.

### Absolute liquidity threshold independent of capital
Rejected because it ignores the economic size of the strategy and can mark a ticker as tradable when it is not tradable for the intended deployment scale.
