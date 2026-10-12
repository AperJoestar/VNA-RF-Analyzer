"""Side-by-side instrument screenshot viewer with crosshair markers."""
import glob
import os
import tkinter as tk
from tkinter import filedialog, ttk

from PIL import Image, ImageDraw, ImageTk


class GalleryMixin:
    """Side-by-side instrument screenshot viewer with crosshair markers.

    Mixed into :class:`rfanalyzer.gui.main_window.RFAnalyzerApp`; relies on the state set up in its ``__init__``.
    """

    def upload_screenshot(self):
        file_path = filedialog.askopenfilename(title="Select File in Screenshot Folder", filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            target_dir = os.path.dirname(file_path)
            pngs = glob.glob(os.path.join(target_dir, "*.png"))
            jpgs = glob.glob(os.path.join(target_dir, "*.jpg"))
            self.image_paths = sorted(pngs + jpgs)
            
            self.refresh_image_gallery()
            self.notebook.select(self.image_tab)

    def refresh_image_gallery(self):
        for widget in self.image_tab.winfo_children(): widget.destroy()
        if not hasattr(self, 'image_paths') or not self.image_paths: return

        top_bar = ttk.Frame(self.image_tab, padding=5)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        ttk.Button(top_bar, text="❌ Clear Crosshair Markers", command=self.clear_both_viewports).pack(side=tk.RIGHT, padx=5)

        split_workspace = ttk.Frame(self.image_tab)
        split_workspace.pack(fill=tk.BOTH, expand=True, pady=5)

        left_panel = ttk.LabelFrame(split_workspace, text=" 🔍 Primary Viewport ")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        combo_l = ttk.Combobox(left_panel, values=[os.path.basename(p) for p in self.image_paths], state="readonly")
        combo_l.pack(fill=tk.X, padx=2)
        self.canvas_left = tk.Label(left_panel, cursor="crosshair", bg="gray20")
        self.canvas_left.pack(fill=tk.BOTH, expand=True, pady=4)
        self.canvas_left.bind("<Button-1>", lambda e: self.on_canvas_clicked(e, "left"))

        right_panel = ttk.LabelFrame(split_workspace, text=" 🔍 Secondary Viewport ")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=4)
        combo_r = ttk.Combobox(right_panel, values=[os.path.basename(p) for p in self.image_paths], state="readonly")
        combo_r.pack(fill=tk.X, padx=2)
        self.canvas_right = tk.Label(right_panel, cursor="crosshair", bg="gray20")
        self.canvas_right.pack(fill=tk.BOTH, expand=True, pady=4)
        self.canvas_right.bind("<Button-1>", lambda e: self.on_canvas_clicked(e, "right"))

        def update_l(e=None):
            if combo_l.get():
                full_path = next((p for p in self.image_paths if os.path.basename(p) == combo_l.get()), None)
                if full_path:
                    self.raw_pil_left = Image.open(full_path)
                    self.markers_left = []; self.render_panel_view("left")

        def update_r(e=None):
            if combo_r.get():
                full_path = next((p for p in self.image_paths if os.path.basename(p) == combo_r.get()), None)
                if full_path:
                    self.raw_pil_right = Image.open(full_path)
                    self.markers_right = []; self.render_panel_view("right")

        combo_l.bind("<<ComboboxSelected>>", update_l)
        combo_r.bind("<<ComboboxSelected>>", update_r)
        combo_l.current(0); update_l()
        if len(self.image_paths) > 1:
            combo_r.current(1)
        else:
            combo_r.current(0)
        update_r()

    def on_canvas_clicked(self, event, panel):
        if panel == "left" and self.disp_pil_left:
            self.markers_left.append((event.x, event.y)); self.render_panel_view("left")
        elif panel == "right" and self.disp_pil_right:
            self.markers_right.append((event.x, event.y)); self.render_panel_view("right")

    def render_panel_view(self, panel):
        w, h = int(self.root.winfo_width() / 2) - 160, 580
        if w < 250: w = 680
        resample = getattr(Image, 'LANCZOS', 1)

        if panel == "left" and self.raw_pil_left:
            img = self.raw_pil_left.copy()
            img.thumbnail((w, h), resample); self.disp_pil_left = img
            draw = ImageDraw.Draw(self.disp_pil_left)
            for i, (mx, my) in enumerate(self.markers_left): self.draw_marker(draw, mx, my, i+1)
            self.tk_img_left = ImageTk.PhotoImage(self.disp_pil_left)
            self.canvas_left.config(image=self.tk_img_left)
        elif panel == "right" and self.raw_pil_right:
            img = self.raw_pil_right.copy()
            img.thumbnail((w, h), resample); self.disp_pil_right = img
            draw = ImageDraw.Draw(self.disp_pil_right)
            for i, (mx, my) in enumerate(self.markers_right): self.draw_marker(draw, mx, my, i+1)
            self.tk_img_right = ImageTk.PhotoImage(self.disp_pil_right)
            self.canvas_right.config(image=self.tk_img_right)

    def draw_marker(self, draw, x, y, idx):
        draw.ellipse([x-8, y-8, x+8, y+8], outline="cyan", width=2)
        draw.line([x-12, y, x+12, y], fill="red", width=2)
        draw.line([x, y-12, x, y+12], fill="red", width=2)
        draw.text((x+10, y-10), f"M{idx}", fill="yellow")

    def clear_both_viewports(self):
        self.markers_left = []; self.markers_right = []
        self.render_panel_view("left"); self.render_panel_view("right")
