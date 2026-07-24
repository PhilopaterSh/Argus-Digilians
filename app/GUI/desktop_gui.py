"""
Argus Desktop Security Studio - Tkinter interface.

Fallback: if Tkinter is not installed, prints a clear error message.
"""

import sys
import os

try:
    import tkinter as tk
    from tkinter import scrolledtext
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.core.config import ArgusConfig
from app.tools.tool_registry import WSLBridgeTools
from app.core.agent.brain import ArgusBrain
from langchain_core.tools import Tool


class DesktopArgusGUI:
    def __init__(self):
        """Build the Tkinter window and its widgets; exits the process if
        Tkinter isn't installed."""
        if not TK_AVAILABLE:
            print("Error: Tkinter is not available.")
            print("Install with: sudo apt-get install python3-tk  (WSL/Kali)")
            print("Or on Windows: Python includes tkinter by default - check your Python installation.")
            sys.exit(1)

        self.bridge = WSLBridgeTools()
        self.root = tk.Tk()
        self.root.title("Argus Desktop Security Studio")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e1e")
        self._build_ui()

    def _build_ui(self):
        """Lay out the title, target-input row, output text area, and status bar."""
        title = tk.Label(
            self.root, text="Argus Desktop Security Studio",
            fg="#00ff41", bg="#1e1e1e", font=("Consolas", 16, "bold"),
        )
        title.pack(pady=(10, 5))

        frame = tk.Frame(self.root, bg="#1e1e1e")
        frame.pack(pady=5, padx=10, fill=tk.X)

        tk.Label(frame, text="Target:", fg="#ccc", bg="#1e1e1e",
                 font=("Consolas", 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.target_var = tk.StringVar(value="https://example.com")
        entry = tk.Entry(frame, textvariable=self.target_var, width=60,
                         font=("Consolas", 10), bg="#2d2d2d", fg="#fff",
                         insertbackground="#fff")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        run_btn = tk.Button(frame, text="RUN ANALYSIS", command=self._run_analysis,
                            bg="#00aa41", fg="white", font=("Consolas", 10, "bold"),
                            padx=15)
        run_btn.pack(side=tk.LEFT, padx=(10, 0))

        output_frame = tk.Frame(self.root, bg="#1e1e1e")
        output_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.output = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#1e1e1e", fg="#00ff41", insertbackground="#fff",
            state=tk.DISABLED,
        )
        self.output.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value=" Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              bg="#2d2d2d", fg="#aaa", font=("Consolas", 9),
                              anchor=tk.W, padx=10)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _log(self, text):
        """Append a line to the output text area and scroll to the bottom.

        Args:
            text (str): The line to append (a newline is added).
        """
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)
        self.root.update()

    def _run_analysis(self):
        """Read the target field, run ArgusBrain against it, and log the result.

        Bound to the "RUN ANALYSIS" button; logs an error and updates the
        status bar instead of raising if the target is empty or the
        analysis itself fails.
        """
        target = self.target_var.get().strip()
        if not target:
            self._log("Error: No target provided.")
            return

        self._log(f"Starting analysis for: {target}")
        self.status_var.set(" Running analysis...")

        try:
            model = ArgusConfig.load().model_name
            tools = [
                Tool(name="Check_Reachability", func=self.bridge.check_reachability,
                     description="Check target reachability"),
                Tool(name="Recon_Suite", func=self.bridge.recon_suite,
                     description="Execute recon suite"),
                Tool(name="Query_Memory", func=self.bridge.get_intelligence_summary,
                     description="Query memory"),
            ]
            brain = ArgusBrain(model, tools)
            analysis = brain.ask(
                f"Perform a comprehensive security analysis for {target}."
            )
            output = analysis.get("output", str(analysis))
            self._log(f"\n--- ANALYSIS RESULT ---\n{output}")
            self.status_var.set(" Analysis complete.")
        except Exception as e:
            self._log(f"Error: {e}")
            self.status_var.set(" Analysis failed.")

    def run(self):
        """Run."""
        self.root.mainloop()


def main():
    """Create and run the Desktop Argus GUI (blocks on the Tkinter mainloop)."""
    app = DesktopArgusGUI()
    app.run()


if __name__ == "__main__":
    main()
