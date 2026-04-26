from __future__ import annotations

import os
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from afkbot.actions import post_key_press
from afkbot.config import load_config
from afkbot.engine import BotEngine
from afkbot.profiles import GameProfile, get_profile_by_name, list_game_profiles
from afkbot.windows import WindowInfo, is_window, list_visible_windows


class BotGui(tk.Tk):
    def __init__(self, base_dir: Path) -> None:
        super().__init__()
        self.base_dir = base_dir
        self.profiles: list[GameProfile] = []
        self.windows: list[WindowInfo] = []
        self.window_by_label: dict[str, WindowInfo] = {}
        self.selected_profile: GameProfile | None = None
        self.engine: BotEngine | None = None
        self.engine_thread: threading.Thread | None = None

        self.title("Inazuma Semi AFK")
        self.geometry("880x600")
        self.minsize(760, 520)

        self.status_var = tk.StringVar(value="待機")
        self.profile_var = tk.StringVar()
        self.window_var = tk.StringVar()
        self.background_input_var = tk.BooleanVar(value=False)
        self.config_var = tk.StringVar(value="尚未選擇遊戲")
        self.scene_count_var = tk.StringVar(value="場景：-")
        self.debug_var = tk.StringVar(value="Debug：-")

        self._build_ui()
        self.refresh_profiles()
        self.refresh_windows()
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

        ttk.Checkbutton(
            selector,
            text="背景輸入",
            variable=self.background_input_var,
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.window_combo = ttk.Combobox(
            selector,
            textvariable=self.window_var,
            state="readonly",
            values=[],
        )
        self.window_combo.grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(8, 0))
        ttk.Button(selector, text="重新整理視窗", command=self.refresh_windows).grid(
            row=1, column=2, padx=(0, 8), pady=(8, 0)
        )
        ttk.Button(selector, text="測試 Enter", command=self.test_background_enter).grid(
            row=1, column=3, pady=(8, 0)
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

    def refresh_windows(self) -> None:
        current_label = self.window_var.get()
        self.windows = list_visible_windows()
        self.window_by_label = {window.label: window for window in self.windows}
        labels = list(self.window_by_label)
        self.window_combo.configure(values=labels)

        next_label = current_label if current_label in labels else (labels[0] if labels else "")
        self.window_var.set(next_label)
        self.log(f"已找到 {len(labels)} 個可選視窗。")

    def _on_profile_selected(self, _event: tk.Event) -> None:
        if self._engine_is_running():
            messagebox.showinfo("引擎執行中", "請先停止引擎，再切換遊戲。")
            self.profile_var.set(self.selected_profile.name if self.selected_profile else "")
            return
        self.selected_profile = get_profile_by_name(self.base_dir, self.profile_var.get())
        self._load_config_preview()

    def _load_config_preview(self) -> None:
        if self.selected_profile is None:
            self.config_var.set("找不到遊戲設定，請在 games/ 底下新增資料夾。")
            self.scene_count_var.set("場景：-")
            self.debug_var.set("Debug：-")
            self.status_var.set("缺少設定")
            self.log("找不到遊戲設定。")
            return

        self.config_var.set(str(self.selected_profile.config_path))
        try:
            config = load_config(self.selected_profile.config_path)
        except Exception as exc:
            self.scene_count_var.set("場景：-")
            self.debug_var.set("Debug：-")
            self.status_var.set("設定錯誤")
            self.log(f"[ERROR] 設定讀取失敗：{exc}")
            return

        self.scene_count_var.set(f"場景：{len(config.scenes)}")
        self.debug_var.set(f"Debug：{config.debug}")
        self.status_var.set("待機")
        self.log(f"已載入 {self.selected_profile.name}，共 {len(config.scenes)} 個場景。")

    def start_engine(self) -> None:
        if self._engine_is_running():
            self.log("引擎已在執行中。")
            return
        if self.selected_profile is None:
            messagebox.showerror("缺少設定", "尚未選擇遊戲設定。")
            return

        try:
            config = load_config(self.selected_profile.config_path)
        except Exception as exc:
            messagebox.showerror("設定錯誤", str(exc))
            self.log(f"[ERROR] 設定讀取失敗：{exc}")
            return

        input_mode = "foreground"
        target_hwnd = None
        if self.background_input_var.get():
            target_hwnd = self.get_selected_window_hwnd()
            if target_hwnd is None:
                messagebox.showerror("背景輸入", "請先選擇有效的目標視窗。")
                return
            input_mode = "background"

        self.engine = BotEngine(
            config,
            log=self.log_from_thread,
            on_monitoring_changed=self.on_monitoring_changed,
            input_mode=input_mode,
            target_hwnd=target_hwnd,
        )
        self.engine_thread = threading.Thread(target=self._run_engine, daemon=True)
        self.engine_thread.start()
        self.status_var.set("引擎執行中")
        self.log(f"已啟動 {self.selected_profile.name}。")
        if input_mode == "background":
            self.log(f"背景輸入目標：{self.window_var.get()}")

    def start_monitoring(self) -> None:
        self.start_engine()
        if self.engine is not None:
            self.engine.start_monitoring()
            self.status_var.set("監控中")

    def pause_monitoring(self) -> None:
        if self.engine is None:
            self.log("引擎尚未啟動。")
            return
        self.engine.pause_monitoring()
        self.status_var.set("已暫停")

    def stop_engine(self) -> None:
        if self.engine is None:
            self.log("引擎尚未啟動。")
            return
        self.engine.request_stop()
        self.status_var.set("停止中")
        self.log("已送出停止要求。")

    def reload_config(self) -> None:
        if self._engine_is_running():
            messagebox.showinfo("引擎執行中", "請先停止引擎，再重新載入設定。")
            return
        self.refresh_profiles()

    def open_config(self) -> None:
        if self.selected_profile is None or not self.selected_profile.config_path.exists():
            messagebox.showerror("找不到檔案", "找不到 config.json。")
            return
        os.startfile(self.selected_profile.config_path)

    def open_profile_folder(self) -> None:
        if self.selected_profile is None or not self.selected_profile.path.exists():
            messagebox.showerror("找不到資料夾", "找不到遊戲資料夾。")
            return
        os.startfile(self.selected_profile.path)

    def get_selected_window_hwnd(self) -> int | None:
        window = self.window_by_label.get(self.window_var.get())
        if window is None:
            return None
        if not is_window(window.hwnd):
            self.log("選取的視窗已不存在，請重新整理視窗清單。")
            return None
        return window.hwnd

    def test_background_enter(self) -> None:
        target_hwnd = self.get_selected_window_hwnd()
        if target_hwnd is None:
            messagebox.showerror("背景輸入", "請先選擇有效的目標視窗。")
            return
        post_key_press(target_hwnd, "enter")
        self.log(f"已對背景視窗送出 Enter：{self.window_var.get()}")

    def _run_engine(self) -> None:
        try:
            if self.engine is not None:
                self.engine.run()
        except Exception as exc:
            self.log_from_thread(f"[ERROR] 引擎錯誤：{exc}")
        finally:
            self.after(0, self._mark_engine_stopped)

    def _mark_engine_stopped(self) -> None:
        self.status_var.set("待機")
        self.engine = None
        self.engine_thread = None

    def _engine_is_running(self) -> bool:
        return self.engine_thread is not None and self.engine_thread.is_alive()

    def on_monitoring_changed(self, enabled: bool) -> None:
        self.after(0, self.status_var.set, "監控中" if enabled else "已暫停")

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
