import importlib
import pytest

GUI_MODULES = [
    "app.GUI.app",
    "app.GUI.studio",
    "app.GUI.desktop_gui",
    "app.GUI.dashboard",
]


@pytest.mark.parametrize("module_path", GUI_MODULES)
def test_gui_module_imports(module_path):
    """Verify Gui module imports.

    Args:
        module_path (str): Dotted path of the GUI module to import.
    """
    mod = importlib.import_module(module_path)
    assert mod is not None
