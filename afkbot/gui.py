from __future__ import annotations

import os
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from afkbot.config import load_config
from afkbot.engine import BotEngine


class BotGui(tk.Tk):
    def __init__(self, base_dir: Path) -> None:
        super().__init__()
        self.base_dir = base_dir
        self.config_path = base_dir / "config.json"
        self.engine: BotEngine | None = None
        self.engine_thread: threading.Thread | None = None

        self.title("Inazuma Semi AFK")
        self.geometry("760x520")
        self.minsize(680, 460)

        self.status_var = tk.StringVar(value="Idle")
        self.config_var = tk.StringVar(value=str(self.config_path))
        self.scene_count_var = tk.StringVar(value="Scenes: -")
        self.debug_var = tk.StringVar(value="Debug: -")

        self._build_ui()
        self._load_config_preview()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        style = ttk.Style(self)
        style.configure("Status.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))

        header = ttk.Frame(self, padding=(18, 14, 18, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Inazuma Semi AFK", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").grid(
            row=0, column=1, sticky="e"
        )
        ttk.Label(header, textvariable=self.config_var).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        controls = ttk.Frame(self, padding=(18, 8))
        controls.grid(row=1, column=0, sticky="ew")
        controls.columnconfigure(6, weight=1)

        ttk.Button(controls, text="啟動引擎", command=self.start_engine).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(controls, text="開始監控", command=self.start_monitoring).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(controls, text="暫停監控", command=self.pause_monitoring).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(controls, text="停止", command=self.stop_engine).grid(
            row=0, column=3, padx=(0, 8)
        )
        ttk.Button(controls, text="重新載入設定", command=self.reload_config).grid(
            row=0, column=4, padx=(0, 8)
        )
        ttk.Button(controls, text="開啟設定檔", command=self.open_config).grid(
            row=0, column=5, padx=(0, 8)
        )

        details = ttk.Frame(self, padding=(18, 0, 18, 8))
        details.grid(row=2, column=0, sticky="nsew")
        details.columnconfigure(0, weight=1)
        details.rowconfigure(1, weight=1)

        meta = ttk.Frame(details)
        meta.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(meta, textvariable=self.scene_count_var).pack(side="left")
        ttk.Label(meta, textvariable=self.debug_var).pack(side="left", padx=(18, 0))
        ttk.Label(meta, text="Hotkeys: ALT+1 start, ALT+0 pause, F8 stop").pack(
            side="left", padx=(18, 0)
        )

        log_frame = ttk.Frame(details)
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame,
            height=18,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _load_config_preview(self) -> None:
        try:
            config = load_config(self.config_path)
        except Exception as exc:
            self.scene_count_var.set("Scenes: -")
            self.debug_var.set("Debug: -")
            self.status_var.set("Config error")
            self.log(f"[ERROR] Failed to load config: {exc}")
            return

        self.scene_count_var.set(f"Scenes: {len(config.scenes)}")
        self.debug_var.set(f"Debug: {config.debug}")
        self.log(f"Config loaded. {len(config.scenes)} scenes ready.")

    def start_engine(self) -> None:
        if self._engine_is_running():
            self.log("Engine is already running.")
            return

        try:
            config = load_config(self.config_path)
        except Exception as exc:
            messagebox.showerror("Config Error", str(exc))
            self.log(f"[ERROR] Failed to load config: {exc}")
            return

        self.engine = BotEngine(
            config,
            log=self.log_from_thread,
            on_monitoring_changed=self.on_monitoring_changed,
        )
        self.engine_thread = threading.Thread(target=self._run_engine, daemon=True)
        self.engine_thread.start()
        self.status_var.set("Engine running")
        self.log("Engine started.")

    def start_monitoring(self) -> None:
        self.start_engine()
        if self.engine is not None:
            self.engine.start_monitoring()
            self.status_var.set("Monitoring")

    def pause_monitoring(self) -> None:
        if self.engine is None:
            self.log("Engine is not running.")
            return
        self.engine.pause_monitoring()
        self.status_var.set("Paused")

    def stop_engine(self) -> None:
        if self.engine is None:
            self.log("Engine is not running.")
            return
        self.engine.request_stop()
        self.status_var.set("Stopping")
        self.log("Stop requested.")

    def reload_config(self) -> None:
        if self._engine_is_running():
            messagebox.showinfo(
                "Engine Running",
                "Stop the engine before reloading config.",
            )
            return
        self._load_config_preview()

    def open_config(self) -> None:
        if not self.config_path.exists():
            messagebox.showerror("Missing File", "config.json not found.")
            return
        os.startfile(self.config_path)

    def _run_engine(self) -> None:
        try:
            if self.engine is not None:
                self.engine.run()
        except Exception as exc:
            self.log_from_thread(f"[ERROR] Engine crashed: {exc}")
        finally:
            self.after(0, self._mark_engine_stopped)

    def _mark_engine_stopped(self) -> None:
        self.status_var.set("Idle")
        self.engine = None
        self.engine_thread = None

    def _engine_is_running(self) -> bool:
        return self.engine_thread is not None and self.engine_thread.is_alive()

    def on_monitoring_changed(self, enabled: bool) -> None:
        self.after(0, self.status_var.set, "Monitoring" if enabled else "Paused")

    def log_from_thread(self, message: str) -> None:
        self.after(0, self.log, message)

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _on_close(self) -> None:
        if self.engine is not None:
            self.engine.request_stop()
        self.destroy()


def run_gui(base_dir: Path) -> None:
    app = BotGui(base_dir)
    app.mainloop()
