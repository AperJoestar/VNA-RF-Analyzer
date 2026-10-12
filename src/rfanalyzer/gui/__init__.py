"""Tkinter / matplotlib user interface.

Importing this package selects the TkAgg backend, so import it only after the Tk root window exists
(``rfanalyzer.app`` does this so the splash window appears before the heavy imports run).
"""
import matplotlib

matplotlib.use("TkAgg")
