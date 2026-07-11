# ADR 0003 — Use a scale-specific tradable universe and ranking

## Status
Accepted

## Context
The lab evaluates multiple capital scales in USD MEP.
A ticker can be tradable for 5k and non-tradable for 15k on the same date.
If ranking is computed once on the full universe and then filtered later, larger scales can inherit names that were never truly executable for that scale.
That would distort both selection quality and portfolio realism.

## Decision
The lab will derive tradability by date and by capital scale in T267, and compute momentum ranking separately for each scale-specific tradable universe in T268.

## Consequences
### Positive
- Selection stays tied to executable opportunity.
- Capacity constraints are reflected before portfolio construction.
- Results across scales become economically interpretable.

### Negative
- More artifacts must be produced and maintained.
- Cross-scale comparisons require clearer reporting because the eligible universe can differ.

## Alternatives considered
### One global ranking then filter later
Rejected because it allows non-executable names to influence the ranking used by larger scales.

### One global tradable universe for all scales
Rejected because it throws away valid opportunities at smaller scales and hides capacity structure.
