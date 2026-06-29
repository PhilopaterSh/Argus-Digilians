import logging
from typing import Optional

from app.modules.base import BaseTacticalModule

logger = logging.getLogger(__name__)

_modules: dict[str, BaseTacticalModule] = {}


def register(module: BaseTacticalModule) -> None:
    _modules[module.name] = module
    logger.info("Registered tactical module: %s", module.name)


def run_module(name: str, target: str) -> str:
    if name not in _modules:
        raise KeyError(f"Tactical module not found: {name}")
    return _modules[name].execute(target)


def run_all(target: str) -> dict[str, str]:
    results = {}
    for name, module in _modules.items():
        try:
            results[name] = module.execute(target)
        except Exception as e:
            results[name] = f"Error: {e}"
            logger.error("Module %s failed on %s: %s", name, target, e)
    return results


def list_modules() -> list[tuple[str, str]]:
    return [(m.name, m.description) for m in _modules.values()]
