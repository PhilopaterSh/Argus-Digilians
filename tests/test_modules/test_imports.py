"""Import validation tests for tactical modules."""

import importlib
import pytest

pytestmark = pytest.mark.unit

MODULES = [
    "app.modules.base",
    "app.modules.argus_reasoning",
    "app.modules.argus_deep_exploit",
    "app.modules.stealth_exploit",
    "app.modules.run_recon",
    "app.modules.run_full_recon",
    "app.modules.map_target",
    "app.modules.seed_memory",
    "app.modules.ddgs",
    "app.modules.crawler",
    "app.modules.build_payload_db",
]


@pytest.mark.parametrize("module_path", MODULES)
def test_module_imports(module_path):
    """Verify Module imports.
    
    Args:
        module_path: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
    """
    mod = importlib.import_module(module_path)
    assert mod is not None


def test_base_tactical_module_abc():
    """Verify Base tactical module abc."""
    from app.modules.base import BaseTacticalModule
    with pytest.raises(TypeError):
        BaseTacticalModule()


def test_modules_registry():
    """Verify Modules registry."""
    from app.modules import register, run_module, run_all, list_modules
    assert callable(register)
    assert callable(run_module)
    assert callable(run_all)
    assert callable(list_modules)
