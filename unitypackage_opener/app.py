# ...existing code...
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .extractor import extract_multiple
from .settings import AppSettings, load_settings, save_settings
from .registry import ensure_registered, APP_NAME, SETTINGS_DIR
from .progress_indicator import extraction_progress_indicator, try_show_toast_notification


class App(ctk.CTk):
    def __init__(self, passed_files: list[str] | None = None):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(APP_NAME)
        self.geometry("600x360")

        self.font_family = "Meiryo"
        try:
            ctk.CTkLabel(self, text="").configure(font=(self.font_family, 12))
        except Exception:
            self.font_family = None

        self.settings = ensure_registered() or {}
        self.app_settings = load_settings()

        self._build_ui(passed_files or [])

    def _label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=(self.font_family, 12) if self.font_family else None)

    def _radio(self, parent, text, variable, value):
        return ctk.CTkRadioButton(parent, text=text, variable=variable, value=value, font=(self.font_family, 12) if self.font_family else None)

    def _button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, font=(self.font_family, 12) if self.font_family else None)

    def _entry(self, parent, textvariable):
        return ctk.CTkEntry(parent, textvariable=textvariable, font=(self.font_family, 12) if self.font_family else None, width=420)

    def _build_ui(self, passed_files: list[str]):
        pad = {"padx": 12, "pady": 8}
        gpad = {"pady": 5}

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, **pad)
        frame.grid_columnconfigure(1, weight=1)

        row = 0
        # 解凍モード（横並び）
        self._label(frame, "解凍モード").grid(row=row, column=0, sticky="w", **gpad)
        self.mode_var = tk.StringVar(value=self.app_settings.mode)
        mode_row = ctk.CTkFrame(frame)
        mode_row.grid(row=row, column=1, sticky="we", **gpad)
        self._radio(mode_row, "マージモード", self.mode_var, "merge").grid(row=0, column=0, sticky="w", padx=6)
        self._radio(mode_row, "個別モード", self.mode_var, "individual").grid(row=0, column=1, sticky="w", padx=6)
        row += 1

        # 競合解決（横並び）
        self._label(frame, "競合解決").grid(row=row, column=0, sticky="w", **gpad)
        self.conflict_var = tk.StringVar(value=self.app_settings.conflict)
        conflict_row = ctk.CTkFrame(frame)
        conflict_row.grid(row=row, column=1, sticky="we", **gpad)
        self._radio(conflict_row, "常に上書き", self.conflict_var, "overwrite").grid(row=0, column=0, sticky="w", padx=6)
        self._radio(conflict_row, "常にスキップ", self.conflict_var, "skip").grid(row=0, column=1, sticky="w", padx=6)
        self._radio(conflict_row, "常に名前を変えて保存", self.conflict_var, "rename").grid(row=0, column=2, sticky="w", padx=6)
        row += 1

        # 出力先モード（横並び）
        self._label(frame, "出力先").grid(row=row, column=0, sticky="w", **gpad)
        self.output_mode_var = tk.StringVar(value=getattr(self.app_settings, "output_dir_mode", "auto"))
        outmode_row = ctk.CTkFrame(frame)
        outmode_row.grid(row=row, column=1, sticky="we", **gpad)
        self._radio(outmode_row, "自動（入力ファイルの場所）", self.output_mode_var, "auto").grid(row=0, column=0, sticky="w", padx=6)
        self._radio(outmode_row, "固定", self.output_mode_var, "fixed").grid(row=0, column=1, sticky="w", padx=6)
        row += 1

        # 出力先パス（固定のときのみ有効）
        self._label(frame, "出力先パス").grid(row=row, column=0, sticky="w", **gpad)
        path_row = ctk.CTkFrame(frame)
        path_row.grid(row=row, column=1, sticky="we", **gpad)
        path_row.grid_columnconfigure(0, weight=1)
        self.output_var = tk.StringVar(value=self.app_settings.output_dir)
        self.output_entry = self._entry(path_row, self.output_var)
        self.output_entry.grid(row=0, column=0, sticky="we")
        self.browse_btn = self._button(path_row, "参照...", self._choose_output)
        self.browse_btn.grid(row=0, column=1, sticky="w", padx=6)

        def on_mode_change(*_):
            is_fixed = self.output_mode_var.get() == "fixed"
            state = "normal" if is_fixed else "disabled"
            try:
                self.output_entry.configure(state=state)
                self.browse_btn.configure(state=state)
            except Exception:
                pass
        self.output_mode_var.trace_add("write", on_mode_change)
        on_mode_change()

        row += 1
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="we", pady=16)
        btn_frame.grid_columnconfigure(0, weight=1)
        self._button(btn_frame, "保存", self._save_settings).grid(row=0, column=0, sticky="e", padx=4)

    def _choose_output(self):
        d = filedialog.askdirectory(initialdir=self.output_var.get() or os.path.expanduser("~"))
        if d:
            self.output_var.set(d)

    def _save_settings(self):
        self.app_settings.mode = self.mode_var.get()  # type: ignore
        self.app_settings.conflict = self.conflict_var.get()  # type: ignore
        self.app_settings.output_dir_mode = self.output_mode_var.get()  # type: ignore
        self.app_settings.output_dir = self.output_var.get()
        save_settings(self.app_settings)
        messagebox.showinfo(APP_NAME, "設定を保存しました。")


def main():
    args = sys.argv[1:]
    # Clear debug log at every launch
    debug_log_path = os.path.join(SETTINGS_DIR, "debug_headless.log")
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(debug_log_path, "w", encoding="utf-8") as df:
            df.write("")
    except Exception:
        pass
    with open(debug_log_path, "a", encoding="utf-8") as df:
        df.write("[DEBUG] sys.argv: " + repr(sys.argv) + "\n")
        df.write("[DEBUG] raw args: " + repr(args) + "\n")
    headless_flag = False
    file_candidates = []
    for a in args:
        if a == "--headless":
            headless_flag = True
            continue
        if a.strip():
            file_candidates.append(a)
    # ログ: 受け取ったファイル候補一覧
    with open(os.path.join(SETTINGS_DIR, "debug_headless.log"), "a", encoding="utf-8") as df:
        df.write("[DEBUG] file_candidates: " + repr(file_candidates) + "\n")
    # .unitypackage拡張子で存在するファイルのみ抽出
    passed = []
    for arg in file_candidates:
        exists = os.path.exists(arg)
        is_unitypackage = arg.lower().endswith('.unitypackage')
        with open(os.path.join(SETTINGS_DIR, "debug_headless.log"), "a", encoding="utf-8") as df:
            df.write(f"[DEBUG] arg: {arg} | exists: {exists} | unitypackage: {is_unitypackage}\n")
        if is_unitypackage and exists:
            passed.append(arg)
    with open(os.path.join(SETTINGS_DIR, "debug_headless.log"), "a", encoding="utf-8") as df:
        df.write("[DEBUG] passed_detected: " + repr(passed) + "\n")

    if headless_flag or passed:
        app_settings = load_settings()

        os.makedirs(SETTINGS_DIR, exist_ok=True)
        log_path = os.path.join(SETTINGS_DIR, "last_run.log")
        debug_path = os.path.join(SETTINGS_DIR, "debug_headless.log")

        try:
            with open(debug_path, "a", encoding="utf-8") as df:
                df.write("===== Invocation =====\n")
                df.write(f"argv            : {sys.argv}\n")
                df.write(f"headless_flag   : {headless_flag}\n")
                df.write(f"raw_args        : {args}\n")
                df.write(f"passed_detected : {passed}\n")
                for p in passed:
                    exists = os.path.exists(p)
                    size = os.path.getsize(p) if exists else 'NA'
                    df.write(f"  file_exists?  : {p} -> {exists} size={size}\n")
                df.write(f"settings.mode   : {getattr(app_settings,'mode',None)}\n")
                df.write(f"settings.conflict: {getattr(app_settings,'conflict',None)}\n")
                df.write(f"settings.output_dir_mode: {getattr(app_settings,'output_dir_mode','auto')}\n")

            if getattr(app_settings, "output_dir_mode", "auto") == "auto" and passed:
                base_dir = os.path.dirname(os.path.abspath(passed[0]))
                output_dir = base_dir
            else:
                output_dir = app_settings.output_dir

            conflict_policy = app_settings.conflict

            with open(debug_path, "a", encoding="utf-8") as df:
                df.write(f"resolved_output_dir: {output_dir}\n")
                df.write(f"effective_conflict : {conflict_policy}\n")
                if not passed:
                    df.write("NO FILES -> nothing to extract (headless no-op)\n")
                else:
                    df.write(f"extracting {len(passed)} unitypackage(s)\n")

            # Show progress indication during extraction
            if passed:
                # Show notification for extraction start
                first_file = os.path.basename(passed[0])
                try_show_toast_notification(
                    "Unity Package Extractor", 
                    f"Extracting {first_file}..."
                )
            
            with extraction_progress_indicator(
                show_cursor=True,
                create_temp_file=bool(passed),
                output_dir=output_dir if passed else None
            ):
                all_results = extract_multiple(
                    unitypackages=passed,
                    output_dir=output_dir,
                    mode=app_settings.mode,
                    conflict_policy=conflict_policy,
                )

            # Show completion notification
            if passed and all_results:
                total_entries = sum(len(entries) for entries in all_results.values())
                try_show_toast_notification(
                    "Unity Package Extractor",
                    f"Extraction complete! {total_entries} files extracted."
                )

            with open(debug_path, "a", encoding="utf-8") as df:
                df.write(f"extraction_result_count: {len(all_results)}\n")
                for up, entries in all_results.items():
                    df.write(f"  {up} -> {len(entries)} entries\n")
                df.write("===== End Invocation =====\n")

            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"Mode: {app_settings.mode}\n")
                f.write(f"Conflict: {app_settings.conflict}\n")
                f.write(f"Output: {output_dir}\n")
                f.write("Processed files:\n")
                for p in passed:
                    f.write(f" - {p}\n")
            return
        except Exception as e:
            with open(debug_path, "a", encoding="utf-8") as df:
                df.write(f"ERROR: {e}\n")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"Error: {e}\n")
            sys.exit(1)

    app = App([])
    app.mainloop()

if __name__ == "__main__":
    main()
