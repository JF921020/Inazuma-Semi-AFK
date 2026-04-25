from __future__ import annotations

import os
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from afkbot.config import load_config
from afkbot.engine import BotEngine
from afkbot.profiles import GameProfile, get_profile_by_name, list_game_profiles


class BotGui(tk.Tk):
    def __init__(self, base_dir: Path) -> None:
        super().__init__()
        self.base_dir = base_dir
        self.profiles: list[GameProfile] = []
        self.selected_profile: GameProfile | None = None
        self.engine: BotEngine | None = None
        self.engine_thread: threading.Thread | None = None

        self.title("Inazuma Semi AFK")
        self.geometry("820x560")
        self.minsize(720, 500)

        self.status_var = tk.StringVar(value="Idle")
        self.profile_var = tk.StringVar()
        self.config_var = tk.StringVar(value="No game selected")
        self.scene_count_var = tk.StringVar(value="Scenes: -")
        self.debug_var = tk.StringVar(value="Debug: -")

        self._build_ui()
        self.refresh_profiles()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

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

        selector = ttk.Frame(self, padding=(18, 8, 18, 4))
        selector.grid(row=1, column=0, sticky="ew")
        selector.columnconfigure(1, weight=1)

        ttk.Label(selector, text="遊戲").grid(row=0, column=0, sticky="w")
        self.profile_combo = ttk.Combobox(
            selector,
            textvariable=self.profile_var,
            state="readonly",
            values=[],
        )
        self.profile_combo.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
        ttk.Button(selector, text="重新整理", command=self.refresh_profiles).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(selector, text="開啟資料夾", command=self.open_profile_folder).grid(
            row=0, column=3
        )

        controls = ttk.Frame(self, padding=(18, 8))
        controls.grid(row=2, column=0, sticky="ew")
        controls.columnconfigure(6, weight=1)

        ttk.Button(controls, text="啟動引擎", command=self.start_engine).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(controls, text="開始監控", command=self.start_monitoring).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(controls, text="暫停", command=self.pause_monitoring).grid(
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
        details.grid(row=3, column=0, sticky="nsew")
        details.columnconfigure(0, weight=1)
        details.rowconfigure(1, weight=1)

        meta = ttk.Frame(details)
        meta.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(meta, textvariable=self.scene_count_var).pack(side="left")
        ttk.Label(meta, textvariable=self.debug_var).pack(side="left", padx=(18, 0))
        ttk.Label(meta, text="快捷鍵：ALT+1 開始，ALT+0 暫停，F8 停止").pack(
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

    def refresh_profiles(self) -> None:
        current_name = self.profile_var.get()
        self.profiles = list_game_profiles(self.base_dir)
        names = [profile.name for profile in self.profiles]
        self.profile_combo.configure(values=names)

        next_name = current_name if current_name in names else (names[0] if names else "")
        self.profile_var.set(next_name)
        self.selected_profile = get_profile_by_name(self.base_dir, next_name)
        self._load_config_preview()

    def _on_profile_selected(self, _event: tk.Event) -> None:
        if self._engine_is_running():
            messagebox.showinfo("Engine Running", "Stop the engine before changing game.")
            self.profile_var.set(self.selected_profile.name if self.selected_profile else "")
            return
        self.selected_profile = get_profile_by_name(self.base_dir, self.profile_var.get())
        self._load_config_preview()

    def _load_config_preview(self) -> None:
        if self.selected_profile is None:
            self.config_var.set("No game config found. Add folders under games/.")
            self.scene_count_var.set("Scenes: -")
            self.debug_var.set("Debug: -")
            self.status_var.set("Config missing")
            self.log("No game profiles found.")
            return

        self.config_var.set(str(self.selected_profile.config_path))
        try:
            config = load_config(self.selected_profile.config_path)
        except Exception as exc:
            self.scene_count_var.set("Scenes: -")
            self.debug_var.set("Debug: -")
            self.status_var.set("Config error")
            self.log(f"[ERROR] Failed to load config: {exc}")
            return

        self.scene_count_var.set(f"Scenes: {len(config.scenes)}")
        self.debug_var.set(f"Debug: {config.debug}")
        self.status_var.set("Idle")
        self.log(f"Config loaded for {self.selected_profile.name}. {len(config.scenes)} scenes ready.")

    def start_engine(self) -> None:
        if self._engine_is_running():
            self.log("Engine is already running.")
            return
        if self.selected_profile is None:
            messagebox.showerror("Missing Config", "No game config selected.")
            return

        try:
            config = load_config(self.selected_profile.config_path)
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
        self.log(f"Engine started for {self.selected_profile.name}.")

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
            messagebox.showinfo("Engine Running", "Stop the engine before reloading config.")
            return
        self.refresh_profiles()

    def open_config(self) -> None:
        if self.selected_profile is None or not self.selected_profile.config_path.exists():
            messagebox.showerror("Missing File", "config.json not found.")
            return
        os.startfile(self.selected_profile.config_path)

    def open_profile_folder(self) -> None:
        if self.selected_profile is None or not self.selected_profile.path.exists():
            messagebox.showerror("Missing Folder", "Game folder not found.")
            return
        os.startfile(self.selected_profile.path)

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
