from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@lru_cache
def load_model_config() -> dict[str, Any]:
    config_path = Path(__file__).with_name("model_config.yaml")
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_step_config(step: str) -> dict[str, Any]:
    steps = load_model_config().get("steps", {})
    return steps.get(step, {})
