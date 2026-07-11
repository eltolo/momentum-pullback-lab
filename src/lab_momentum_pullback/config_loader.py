from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
REQUIRED_FILES = {
    "argentina": CONFIG_DIR / "argentina.yaml",
    "usa": CONFIG_DIR / "usa.yaml",
    "costs": CONFIG_DIR / "costs.yaml",
    "experiments": CONFIG_DIR / "experiments.yaml",
}
REQUIRED_DIRS = [
    ROOT / "data" / "raw",
    ROOT / "data" / "processed",
    ROOT / "data" / "quality_reports",
    ROOT / "experiments",
    ROOT / "results",
    ROOT / "tests",
]


@dataclass(frozen=True)
class ConfigCheckResult:
    ok: bool
    loaded: dict[str, Any]
    missing_paths: list[str]
    validation_errors: list[str]


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ensure_directories() -> None:
    for directory in REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def validate_configs(configs: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    argentina = configs.get("argentina", {})
    costs = configs.get("costs", {})
    experiments = configs.get("experiments", {})

    if not argentina.get("universe"):
        errors.append("config/argentina.yaml: universe must not be empty")
    if argentina.get("currency") != "USD_MEP":
        errors.append("config/argentina.yaml: currency must be USD_MEP")

    scenarios = costs.get("scenarios", {})
    for name in ["optimistic", "base", "conservative", "stress"]:
        if name not in scenarios:
            errors.append(f"config/costs.yaml: missing scenario '{name}'")
        elif scenarios[name].get("round_trip_total") is None:
            errors.append(f"config/costs.yaml: scenario '{name}' needs round_trip_total")

    phases = experiments.get("phases", [])
    if not phases:
        errors.append("config/experiments.yaml: phases must not be empty")

    return errors


def run_check() -> ConfigCheckResult:
    ensure_directories()

    missing_paths = [str(path) for path in REQUIRED_FILES.values() if not path.exists()]
    loaded: dict[str, Any] = {}
    validation_errors: list[str] = []

    if not missing_paths:
        for name, path in REQUIRED_FILES.items():
            loaded[name] = load_yaml(path)
        validation_errors = validate_configs(loaded)

    return ConfigCheckResult(
        ok=not missing_paths and not validation_errors,
        loaded=loaded,
        missing_paths=missing_paths,
        validation_errors=validation_errors,
    )
