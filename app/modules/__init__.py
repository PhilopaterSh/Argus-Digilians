import logging
from typing import Optional

from app.modules.base import BaseTacticalModule

logger = logging.getLogger(__name__)

_modules: dict[str, BaseTacticalModule] = {}


def register(module: BaseTacticalModule) -> None:
    """Register a tactical module by its `.name`, overwriting any existing entry.

    Args:
        module (BaseTacticalModule): The module instance to register.

    Returns:
        None
    """
    _modules[module.name] = module
    logger.info("Registered tactical module: %s", module.name)


def run_module(name: str, target: str) -> str:
    """Execute one registered module by name against a target.

    Args:
        name (str): The registered module's name.
        target (str): The target to pass to `module.execute()`.

    Returns:
        str: The module's result.

    Raises:
        KeyError: If `name` isn't registered.
    """
    if name not in _modules:
        raise KeyError(f"Tactical module not found: {name}")
    return _modules[name].execute(target)


def run_all(target: str) -> dict[str, str]:
    """Execute every registered module against a target, catching per-module failures.

    Args:
        target (str): The target to pass to each module's `.execute()`.

    Returns:
        dict[str, str]: Module name to result (or `"Error: <message>"` if
        that module's `execute()` raised - one module's failure doesn't
        stop the others).
    """
    results = {}
    for name, module in _modules.items():
        try:
            results[name] = module.execute(target)
        except Exception as e:
            results[name] = f"Error: {e}"
            logger.error("Module %s failed on %s: %s", name, target, e)
    return results


def list_modules() -> list[tuple[str, str]]:
    """List modules."""
    return [(m.name, m.description) for m in _modules.values()]
