"""Application entry point.

A small splash window is shown first; the heavy scientific stack (numpy, pandas, matplotlib, scipy, Pillow) is
imported only afterwards, so the window appears almost instantly on startup.
"""
import sys


def main() -> None:
    try:
        import tkinter as tk
    except ImportError:
        sys.exit(
            "Tkinter is not available in this Python installation.\n"
            "On Debian/Ubuntu install it with:  sudo apt install python3-tk"
        )

    from rfanalyzer import theme as T

    T.load_saved_theme()

    # Create the native Tk window first so the OS can display something immediately
    # while the large scientific packages are loading.
    root = tk.Tk()
    root.title("RF Analyzer — Loading…")
    root.geometry("520x180")
    root.configure(bg=T.BG)
    root.resizable(False, False)

    loading_frame = tk.Frame(root, bg=T.BG)
    loading_frame.pack(fill=tk.BOTH, expand=True)
    tk.Label(loading_frame, text="RF Analyzer", bg=T.BG, fg=T.FG,
             font=("Arial", 18, "bold")).pack(pady=(38, 6))
    tk.Label(loading_frame, text="Loading analysis engine…", bg=T.BG, fg=T.MUTED,
             font=("Arial", 10)).pack()
    root.update_idletasks()
    root.update()

    # Importing the GUI package pulls in numpy / pandas / matplotlib / scipy / Pillow.
    from rfanalyzer.gui.main_window import RFAnalyzerApp

    loading_frame.destroy()
    root.resizable(True, True)
    RFAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
