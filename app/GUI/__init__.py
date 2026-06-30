import sys
import os
import warnings

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

warnings.warn(
    "Direct import from app.GUI is deprecated. Import from app.GUI.dashboard instead.",
    DeprecationWarning,
    stacklevel=2,
)
