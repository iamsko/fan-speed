import tkinter as tk
from tkinter import ttk
import math
import time
import platform

THEMES = {
    "dark": {
        "bg": "#1a1a2e", "fg": "#e0e0e0", "accent": "#00d4ff",
        "slider_bg": "#16213e", "speed_fg": "#00d4ff",
        "mode_bg": "#0f3460", "mode_fg": "#e0e0e0", "mode_active": "#00d4ff",
        "blade": "#e0e0e0", "hub": "#00d4ff", "rim": "#0f3460",
    },
    "light": {
        "bg": "#f0f4f8", "fg": "#1a1a2e", "accent": "#e94560",
        "slider_bg": "#dde3ed", "speed_fg": "#e94560",
        "mode_bg": "#c4d1e0", "mode_fg": "#1a1a2e", "mode_active": "#e94560",
        "blade": "#1a1a2e", "hub": "#e94560", "rim": "#c4d1e0",
    },
    "neon": {
        "bg": "#0a0a0a", "fg": "#00ff41", "accent": "#ff00ff",
        "slider_bg": "#1a1a1a", "speed_fg": "#00ff41",
        "mode_bg": "#111111", "mode_fg": "#00ff41", "mode_active": "#ff00ff",
        "blade": "#ff00ff", "hub": "#00ff41", "rim": "#1a1a1a",
    },
}

MODES = [
    {"name": "Silent", "speed": 15, "color": "#00ff88"},
    {"name": "Balanced", "speed": 45, "color": "#ffaa00"},
    {"name": "Performance", "speed": 75, "color": "#ff6600"},
    {"name": "Turbo", "speed": 100, "color": "#ff0044"},
]

BLADES_COUNT = 5


class FanApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("fan speed")
        self.root.geometry("520x620")
        self.root.minsize(400, 500)

        self.theme_name = tk.StringVar(value="dark")
        self.speed = tk.IntVar(value=0)
        self.angle = 0.0
        self.last_time = time.time()

        self._build_ui()
        self.apply_theme("dark")
        self._animate()

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = tk.Frame(self.root)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.columnconfigure(1, weight=1)

        tk.Label(header, text="❄", font=("Segoe UI", 18)).grid(row=0, column=0, padx=(0, 8))

        self.title_lbl = tk.Label(header, text="fan speed", font=("Segoe UI", 16, "bold"))
        self.title_lbl.grid(row=0, column=1, sticky="w")

        self.theme_btn = tk.Button(
            header, text="🎨", font=("Segoe UI", 14),
            command=self._cycle_theme, relief="flat", cursor="hand2",
            bd=0, highlightthickness=0, padx=4, pady=2
        )
        self.theme_btn.grid(row=0, column=2)

        canvas_frame = tk.Frame(self.root)
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, width=300, height=300, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.canvas_size = 300
        self.cx = self.canvas_size // 2
        self.cy = self.canvas_size // 2
        self.radius = 110

        self.bg_circle = self.canvas.create_oval(0, 0, 0, 0, width=0)
        self.rim_circle = self.canvas.create_oval(0, 0, 0, 0, width=4)
        self.hub = self.canvas.create_oval(0, 0, 0, 0, fill="", width=0)
        self.blade_ids = [self.canvas.create_polygon(0, 0, 0, 0, 0, 0, fill="", width=0) for _ in range(BLADES_COUNT)]
        self._redraw_canvas()

        self.canvas.bind("<Configure>", self._on_canvas_resize)

        controls = tk.Frame(self.root)
        controls.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        controls.columnconfigure(1, weight=1)

        self.speed_lbl = tk.Label(controls, text="0%", font=("Segoe UI", 28, "bold"))
        self.speed_lbl.grid(row=0, column=0, padx=(0, 16))

        slider_frame = tk.Frame(controls)
        slider_frame.grid(row=0, column=1, sticky="ew")
        slider_frame.columnconfigure(0, weight=1)

        self.slider = tk.Scale(
            slider_frame, from_=0, to=100, orient=tk.HORIZONTAL,
            variable=self.speed, showvalue=False,
            troughcolor="", bd=0, highlightthickness=0,
            sliderlength=24, width=10
        )
        self.slider.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.rpm_lbl = tk.Label(controls, text="0 RPM", font=("Segoe UI", 10))
        self.rpm_lbl.grid(row=0, column=2, padx=(8, 0))

        mode_frame = tk.Frame(self.root)
        mode_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        for i, mode in enumerate(MODES):
            btn = tk.Button(
                mode_frame, text=mode["name"],
                font=("Segoe UI", 10, "bold"),
                command=lambda m=mode: self.slider.set(m["speed"]),
                relief="flat", cursor="hand2",
                bd=0, padx=16, pady=6
            )
            btn.pack(side=tk.LEFT, padx=4, expand=True, fill=tk.X)
        self.mode_btns = mode_frame.winfo_children()

        status_frame = tk.Frame(self.root)
        status_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 12))
        status_frame.columnconfigure(0, weight=1)

        self.status_lbl = tk.Label(status_frame, text="⏸ Paused", font=("Segoe UI", 9))
        self.status_lbl.grid(row=0, column=0, sticky="w")

        self.fps_lbl = tk.Label(status_frame, text="", font=("Segoe UI", 9))
        self.fps_lbl.grid(row=0, column=1, sticky="e")

    def _redraw_canvas(self):
        s = self.canvas_size
        cx, cy = s // 2, s // 2
        r = int(s * 0.38)
        self.radius = r
        m = 6
        self.canvas.coords(self.bg_circle, m, m, s - m, s - m)
        self.canvas.coords(self.rim_circle, m + 6, m + 6, s - m - 6, s - m - 6)
        hub_r = max(int(r * 0.18), 12)
        self.canvas.coords(self.hub, cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r)

    def _on_canvas_resize(self, event):
        new_size = min(event.width, event.height)
        if new_size < 100:
            return
        self.canvas_size = new_size
        self.cx = new_size // 2
        self.cy = new_size // 2
        self._redraw_canvas()

    def _draw_blades(self):
        s = self.speed.get()
        if s == 0:
            for bid in self.blade_ids:
                self.canvas.coords(bid, 0, 0, 0, 0, 0, 0)
            return

        cx, cy = self.cx, self.cy
        r = max(self.radius, 20)
        theme = THEMES[self.theme_name.get()]

        for i, bid in enumerate(self.blade_ids):
            a = self.angle + (2 * math.pi / BLADES_COUNT) * i
            tip_len = r * 1.0
            mid_len = r * 0.45
            width_factor = 0.18 + 0.06 * math.sin(s * 3.14 / 100)
            w = r * width_factor

            tip = (cx + tip_len * math.cos(a), cy + tip_len * math.sin(a))
            a_mid = a + math.pi / 2
            left = (cx + mid_len * math.cos(a - w), cy + mid_len * math.sin(a - w))
            right = (cx + mid_len * math.cos(a + w), cy + mid_len * math.sin(a + w))

            self.canvas.coords(bid, left[0], left[1], tip[0], tip[1], right[0], right[1])

    def _cycle_theme(self):
        names = list(THEMES.keys())
        idx = names.index(self.theme_name.get())
        self.theme_name.set(names[(idx + 1) % len(names)])
        self.apply_theme(self.theme_name.get())

    def apply_theme(self, name):
        theme = THEMES[name]
        self.root.configure(bg=theme["bg"])
        for widget in [self.title_lbl, self.speed_lbl, self.rpm_lbl, self.status_lbl, self.fps_lbl]:
            widget.configure(bg=theme["bg"], fg=theme["fg"])
        self.slider.configure(bg=theme["slider_bg"], troughcolor=theme["slider_bg"], fg=theme["fg"])
        self.canvas.configure(bg=theme["bg"])
        self.canvas.itemconfig(self.bg_circle, fill=theme["slider_bg"], outline="")
        self.canvas.itemconfig(self.rim_circle, outline=theme["accent"])
        self.canvas.itemconfig(self.hub, fill=theme["hub"], outline="")
        for bid in self.blade_ids:
            self.canvas.itemconfig(bid, fill=theme["blade"], outline=theme["hub"])
        for btn in self.mode_btns:
            btn.configure(bg=theme["mode_bg"], fg=theme["fg"], activebackground=theme["accent"], activeforeground=theme["mode_fg"])
        self.theme_btn.configure(bg=theme["mode_bg"], fg=theme["fg"])

    def _animate(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        s = self.speed.get()
        self.speed_lbl.config(text=f"{s}%")

        if s > 0:
            rotation = s * 6.0 * dt
            self.angle = (self.angle + rotation) % (2 * math.pi)
            rpm = int(s * 12)
            self.rpm_lbl.config(text=f"{rpm} RPM")
            self.status_lbl.config(text=f"▶ Running")
        else:
            self.status_lbl.config(text="⏸ Paused")
            self.rpm_lbl.config(text="0 RPM")

        self._draw_blades()
        self.root.after(int(max(16, 200 - s * 1.5)), self._animate)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    FanApp().run()
