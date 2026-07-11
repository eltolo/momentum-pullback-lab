from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CostScenario:
    name: str
    round_trip_total: float  # fraction of capital, e.g. 0.014 = 1.4%
    one_way: float  # half of round trip (assumes symmetric)

    @property
    def label(self) -> str:
        return f"{self.name} ({self.round_trip_total * 100:.1f}% rt)"


DEFAULT_COST_SCENARIOS = [
    CostScenario(name="base", round_trip_total=0.014, one_way=0.007),
    CostScenario(name="optimistic", round_trip_total=0.008, one_way=0.004),
    CostScenario(name="conservative", round_trip_total=0.018, one_way=0.009),
    CostScenario(name="stress", round_trip_total=0.025, one_way=0.0125),
]


def load_cost_scenarios(config: dict[str, Any]) -> list[CostScenario]:
    costs = config.get("scenarios", {})
    scenarios = []
    for name, rt in sorted(costs.items()):
        scenarios.append(CostScenario(name=name, round_trip_total=float(rt), one_way=float(rt) / 2.0))
    return scenarios


def apply_entry_cost(price: float, scenario: CostScenario) -> float:
    """Return effective entry price after buy cost."""
    return price * (1.0 + scenario.one_way)


def apply_exit_cost(price: float, scenario: CostScenario) -> float:
    """Return effective exit proceeds after sell cost."""
    return price * (1.0 - scenario.one_way)


def cost_erosion(gross_return: float, scenario: CostScenario) -> float:
    """Fraction of gross return consumed by round-trip costs."""
    if gross_return <= 0:
        return 1.0
    return min(scenario.round_trip_total / gross_return, 1.0)
