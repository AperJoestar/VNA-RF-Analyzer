"""Floating coordinate read-out that follows the mouse over matplotlib axes."""
from rfanalyzer import theme as T


class CursorReadout:
    """Floating coordinate label that follows the mouse over matplotlib axes
    (same idea as the Label62/Label53 readouts in the C# app).
    Axes whose x label starts with "Freq" show f and y; categorical axes (file names) show y only."""

    def __init__(self, canvas, axes):
        self.canvas = canvas
        self.axes = list(axes)
        self._ann = {}
        canvas.mpl_connect("motion_notify_event", self.on_move)
        canvas.mpl_connect("figure_leave_event", self.on_leave)

    def _annotation(self, ax):
        ann = self._ann.get(ax)
        # ax.clear() removes the artist, so recreate it when it is gone
        if ann is None or ann not in ax.texts:
            ann = ax.annotate("", xy=(0, 0), xytext=(10, 10), textcoords="offset points",
                              fontsize=8, color=T.FG, zorder=100, annotation_clip=False,
                              bbox=dict(boxstyle="round,pad=0.3", fc=T.PANEL, ec=T.ACCENT, alpha=0.95))
            ann.set_in_layout(False)
            ann.set_visible(False)
            self._ann[ax] = ann
        return ann

    @staticmethod
    def _fmt_y(y, span):
        dec = 2 if span >= 5 else (3 if span >= 0.5 else 4)
        return f"{y:.{dec}f}"

    def on_move(self, event):
        changed = False
        for ax in self.axes:
            ann = self._annotation(ax)
            if event.inaxes is ax and event.xdata is not None and event.ydata is not None:
                x0, x1 = ax.get_xlim()
                y0, y1 = ax.get_ylim()
                xspan, yspan = abs(x1 - x0) or 1.0, abs(y1 - y0) or 1.0
                text = f"y = {self._fmt_y(event.ydata, yspan)}"
                if ax.get_xlabel().lower().startswith("freq"):
                    text = f"f = {event.xdata:.4f} GHz\n" + text
                ann.set_text(text)
                ann.xy = (event.xdata, event.ydata)
                near_right = (event.xdata - min(x0, x1)) / xspan > 0.78
                near_top = (event.ydata - min(y0, y1)) / yspan > 0.85
                ann.set_position((-10 if near_right else 10, -10 if near_top else 10))
                ann.set_ha("right" if near_right else "left")
                ann.set_va("top" if near_top else "bottom")
                ann.set_visible(True)
                changed = True
            elif ann.get_visible():
                ann.set_visible(False)
                changed = True
        if changed:
            self.canvas.draw_idle()

    def on_leave(self, event):
        hid = False
        for ann in self._ann.values():
            if ann.get_visible():
                ann.set_visible(False)
                hid = True
        if hid:
            self.canvas.draw_idle()
