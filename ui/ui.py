import tkinter as tk
from tkinter import ttk, font as tkfont
import os
import datetime

class NetMonUI:
    def __init__(self, base_dir: str):
        self.root = tk.Tk()
        self.root.title("AuraCast Network Monitor")
        self.root.geometry("1000x800")
        self.root.configure(bg="#111827")
        self.choices = {"output": "both", "input": "pcap"}
        self.core = None
        self.log_widget = None
        self.base_dir = base_dir
        self.session_path = self._create_session_log_dir()
        self.click_log_path = os.path.join(self.session_path, "click_log.txt")
        self.alert_log_path = os.path.join(self.session_path, "alert_log.txt")
        self.setup_mode_selection()

    def _create_session_log_dir(self):
        base_dir = self.base_dir
        os.makedirs(base_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_path = os.path.join(base_dir, f"session_{timestamp}")
        os.makedirs(session_path, exist_ok=True)
        return session_path

    def set_core(self, core):
        self.core = core

    def get_log_callback(self):
        return self.write_log

    def get_alert_log_path(self):
        return self.alert_log_path

    def get_click_log_path(self):
        return self.click_log_path

    def setup_mode_selection(self):
        self.output_var = tk.StringVar(value="both")
        self.input_var = tk.StringVar(value="pcap")

        heading = ttk.Label(self.root, text="Auracast Mode Selection", font=("Helvetica", 20), foreground="#f9fafb", background="#111827")
        heading.pack(pady=(20, 10))

        output_frame = ttk.LabelFrame(self.root, text="Output Mode", padding=20)
        output_frame.pack(pady=10, padx=20, fill="x")

        for text, value in [("Sonification Only", "sonification"), ("Visualisation Only", "visualisation"), ("Both", "both"), ("None", "none")]:
            ttk.Radiobutton(output_frame, text=text, variable=self.output_var, value=value).pack(anchor="w")

        input_frame = ttk.LabelFrame(self.root, text="Input Mode", padding=20)
        input_frame.pack(pady=10, padx=20, fill="x")

        for text, value in [("PCAP Replay", "pcap"), ("Live Traffic", "live")]:
            ttk.Radiobutton(input_frame, text=text, variable=self.input_var, value=value).pack(anchor="w")

        RoundedButton(
            self.root,
            text="Confirm choices",
            radius=15,
            command=self.start_monitor_mode,
            bg="#111827",
            fg="#f9fafb",
            activebg="#374151",
            activefg="#f9fafb",
            font=("Helvetica", 12)
        ).pack(pady=20)

    def start_monitor_mode(self):
        self.choices["output"] = self.output_var.get()
        self.choices["input"] = self.input_var.get()
        for widget in self.root.winfo_children():
            widget.destroy()

        self.log_widget = tk.Text(self.root, bg="#1f2937", fg="#f9fafb", font=("Courier", 10), state="disabled")
        self.log_widget.pack(expand=True, fill="both", padx=20, pady=20)

        button_frame = tk.Frame(self.root, bg="#111827")
        button_frame.pack(fill="x", padx=20, pady=10)

        self.click_button = RoundedButton(
            button_frame,
            text="Register Event",
            command=self.register_event,
            radius=15,
            bg="#065f46",
            fg="#f9fafb",
            activebg="#047857",
            activefg="#f9fafb"
        )
        self.click_button.pack(side="left", expand=False, fill="x", padx=(0, 10))

        stop_button = RoundedButton(
            button_frame,
            text="Stop Programme",
            command=self.quit_app,
            radius=15,
            bg="#7f1d1d",
            fg="#f9fafb",
            activebg="#b91c1c",
            activefg="#f9fafb"
        )
        stop_button.pack(side="right", expand=False, fill="x", padx=(10, 0))

    def register_event(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.click_log_path, "a") as f:
            f.write(f"{timestamp} - Analyst registered an event\n")
        print(f"[UI] Event registered at {timestamp}")

    def write_log(self, text):
        def append_to_log():
            self.log_widget.configure(state="normal")
            self.log_widget.insert("end", text + "\n")
            self.log_widget.see("end")
            self.log_widget.configure(state="disabled")
            with open(self.alert_log_path, "a") as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")

        try:
            self.root.after(0, append_to_log)
        except Exception as e:
            print(f"[UI] Error while writing log to UI: {e}")

    def quit_app(self):
        print("[UI] Stop Programme clicked. Cleaning up...")
        if getattr(self, 'core', None):
            self.core.stop()
            self.core = None
        self.root.quit()
        if hasattr(self, "net_monitor"):
            self.net_monitor.stop()

    def run(self):
        self.root.mainloop()


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text="",
        radius=25,
        padding=10,
        command=None,
        bg="#111827",
        fg="#f9fafb",
        activebg="#374151",
        activefg="#f9fafb",
        font=("Helvetica", 12),
        *args, **kwargs
    ):
        super().__init__(parent, highlightthickness=0, bg=bg, *args, **kwargs)
        self.command = command
        self.bg = bg
        self.fg = fg
        self.activebg = activebg
        self.activefg = activefg
        self.radius = radius
        self.padding = padding
        self._font = tkfont.Font(family=font[0], size=font[1])

        text_width = self._font.measure(text)
        text_height = self._font.metrics("linespace")

        width = text_width + 2 * padding
        height = text_height + 2 * padding

        self.config(width=width, height=height)

        self.round_rect = self._create_round_rect(0, 0, width, height, radius, fill=bg, outline="")

        self.text_item = self.create_text(
            width / 2,
            height / 2,
            text=text,
            fill=fg,
            font=self._font
        )

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _create_round_rect(self, x1, y1, x2, y2, r=25, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2,     y1,
            x2,     y1 + r,
            x2,     y2 - r,
            x2,     y2,
            x2 - r, y2,
            x1 + r, y2,
            x1,     y2,
            x1,     y2 - r,
            x1,     y1 + r,
            x1,     y1
        ]
        return self.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    def _on_click(self, event):
        if self.command:
            self.command()

    def _on_enter(self, event):
        self.itemconfig(self.round_rect, fill=self.activebg)
        self.itemconfig(self.text_item, fill=self.activefg)

    def _on_leave(self, event):
        self.itemconfig(self.round_rect, fill=self.bg)
        self.itemconfig(self.text_item, fill=self.fg)