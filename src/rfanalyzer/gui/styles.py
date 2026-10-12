"""ttk widget styling for the active theme."""
from tkinter import ttk

from rfanalyzer import theme as T


def style_ttk():
    s = ttk.Style()
    s.theme_use("clam")
    s.configure(".", background=T.BG, foreground=T.FG, fieldbackground=T.PANEL,
                 bordercolor=T.BORDER, darkcolor=T.BORDER, lightcolor=T.BORDER,
                 troughcolor=T.PANEL, selectbackground=T.ACCENT, selectforeground=T.FG)
    s.configure("TNotebook", background=T.BG, borderwidth=0, tabmargins=[0,0,0,0])
    s.configure("TNotebook.Tab", background=T.PANEL, foreground=T.MUTED,
                 padding=[14,6], font=("Arial",9,"bold"), borderwidth=0)
    s.map("TNotebook.Tab", background=[("selected",T.TAB_SEL)], foreground=[("selected",T.FG)])
    s.configure("TFrame", background=T.BG)
    s.configure("TLabel", background=T.BG, foreground=T.FG, font=("Arial",9))
    s.configure("TButton", background=T.PANEL, foreground=T.FG, font=("Arial",9,"bold"),
                 borderwidth=1, relief="flat", padding=[8,4])
    s.map("TButton", background=[("active",T.ACCENT),("pressed",T.ACCENT)])
    s.configure("TEntry", fieldbackground=T.PANEL, foreground=T.FG, insertcolor=T.FG, borderwidth=1)
    s.configure("TCheckbutton", background=T.BG, foreground=T.FG, font=("Arial",9))
    s.configure("TRadiobutton", background=T.BG, foreground=T.FG, font=("Arial",9))
    s.map("TRadiobutton", background=[("active",T.BG)])
    s.configure("Treeview", background=T.PANEL, foreground=T.FG, fieldbackground=T.PANEL,
                 rowheight=22, font=("Arial",9))
    s.configure("Treeview.Heading", background=T.BORDER, foreground=T.MUTED, font=("Arial",9,"bold"))
    s.map("Treeview", background=[("selected",T.ACCENT)])
    s.configure("TCombobox", fieldbackground=T.PANEL, foreground=T.FG, selectbackground=T.ACCENT, font=("Arial",9))
    s.configure("TScrollbar", background=T.PANEL, troughcolor=T.BG, borderwidth=0)
    s.configure("TLabelframe", background=T.BG, foreground=T.MUTED, bordercolor=T.BORDER)
    s.configure("TLabelframe.Label", background=T.BG, foreground=T.MUTED, font=("Arial",8,"bold"))
