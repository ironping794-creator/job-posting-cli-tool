from __future__ import annotations

import argparse
import contextlib
import io
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .clean import run as run_clean
from .collect import collect as run_collect


class JobPostingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Job Posting Tool {__version__}")
        self.geometry("920x680")
        self.minsize(760, 560)

        self.clean_vars = {
            "input_csv": tk.StringVar(),
            "out_dir": tk.StringVar(value="outputs/jobs"),
            "cities": tk.StringVar(value="上海,北京,深圳"),
            "keywords": tk.StringVar(value="AI,大模型,数据分析"),
            "salary_min": tk.StringVar(value="8000"),
            "xlsx": tk.BooleanVar(value=True),
        }
        self.collect_vars = {
            "url": tk.StringVar(),
            "method": tk.StringVar(value="POST"),
            "page_param": tk.StringVar(value="page"),
            "size_param": tk.StringVar(value="size"),
            "page_size": tk.StringVar(value="50"),
            "records_path": tk.StringVar(value="data.records"),
            "total_path": tk.StringVar(value="data.total"),
            "pages_path": tk.StringVar(value="data.pages"),
            "limit": tk.StringVar(value="200"),
            "max_pages": tk.StringVar(),
            "delay": tk.StringVar(value="0.5"),
            "timeout": tk.StringVar(value="30"),
            "out_dir": tk.StringVar(value="outputs/collected_jobs"),
            "xlsx": tk.BooleanVar(value=True),
        }

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="Job Posting Tool", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(header, text="Clean CSV files or collect public JSON APIs without any AI runtime.").pack(
            side="left", padx=(14, 0)
        )

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)
        notebook.add(self._clean_tab(notebook), text="Clean CSV")
        notebook.add(self._collect_tab(notebook), text="Collect API")

        log_frame = ttk.LabelFrame(root, text="Run Log", padding=8)
        log_frame.pack(fill="both", expand=False, pady=(10, 0))
        self.log = tk.Text(log_frame, height=8, wrap="word")
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        scrollbar.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=scrollbar.set)

    def _clean_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=14)
        self._path_row(frame, 0, "Input CSV", self.clean_vars["input_csv"], self._choose_csv)
        self._path_row(frame, 1, "Output Folder", self.clean_vars["out_dir"], self._choose_clean_out_dir)
        self._entry_row(frame, 2, "Cities", self.clean_vars["cities"], "上海,北京,深圳")
        self._entry_row(frame, 3, "Keywords", self.clean_vars["keywords"], "AI,大模型,数据分析")
        self._entry_row(frame, 4, "Minimum Salary", self.clean_vars["salary_min"], "8000")
        ttk.Checkbutton(frame, text="Also export formatted XLSX files", variable=self.clean_vars["xlsx"]).grid(
            row=5, column=1, sticky="w", pady=8
        )

        actions = ttk.Frame(frame)
        actions.grid(row=6, column=1, sticky="w", pady=(12, 0))
        ttk.Button(actions, text="Run Clean", command=self.run_clean).pack(side="left")
        ttk.Button(actions, text="Open Output Folder", command=lambda: self._open_folder(self.clean_vars["out_dir"].get())).pack(
            side="left", padx=(8, 0)
        )
        self._configure_grid(frame)
        return frame

    def _collect_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=14)
        self._entry_row(frame, 0, "API URL", self.collect_vars["url"], "https://example.com/api/jobs")
        ttk.Label(frame, text="Method").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Combobox(frame, textvariable=self.collect_vars["method"], values=["POST", "GET"], width=12, state="readonly").grid(
            row=1, column=1, sticky="w", pady=6
        )

        ttk.Label(frame, text="Headers JSON").grid(row=2, column=0, sticky="nw", pady=6)
        self.headers_text = tk.Text(frame, height=4, width=70)
        self.headers_text.insert("1.0", "{}")
        self.headers_text.grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="Payload JSON").grid(row=3, column=0, sticky="nw", pady=6)
        self.payload_text = tk.Text(frame, height=5, width=70)
        self.payload_text.insert("1.0", "{}")
        self.payload_text.grid(row=3, column=1, sticky="ew", pady=6)

        paths = ttk.Frame(frame)
        paths.grid(row=4, column=1, sticky="ew", pady=6)
        for index, (label, key, width) in enumerate(
            [
                ("Page", "page_param", 10),
                ("Size", "size_param", 10),
                ("Records", "records_path", 18),
                ("Total", "total_path", 14),
                ("Pages", "pages_path", 14),
            ]
        ):
            ttk.Label(paths, text=label).grid(row=0, column=index * 2, sticky="w", padx=(0, 4))
            ttk.Entry(paths, textvariable=self.collect_vars[key], width=width).grid(row=0, column=index * 2 + 1, padx=(0, 8))

        numbers = ttk.Frame(frame)
        numbers.grid(row=5, column=1, sticky="ew", pady=6)
        for index, (label, key, width) in enumerate(
            [
                ("Page Size", "page_size", 8),
                ("Limit", "limit", 10),
                ("Max Pages", "max_pages", 10),
                ("Delay", "delay", 8),
                ("Timeout", "timeout", 8),
            ]
        ):
            ttk.Label(numbers, text=label).grid(row=0, column=index * 2, sticky="w", padx=(0, 4))
            ttk.Entry(numbers, textvariable=self.collect_vars[key], width=width).grid(row=0, column=index * 2 + 1, padx=(0, 8))

        self._path_row(frame, 6, "Output Folder", self.collect_vars["out_dir"], self._choose_collect_out_dir)
        ttk.Checkbutton(frame, text="Also export formatted XLSX files", variable=self.collect_vars["xlsx"]).grid(
            row=7, column=1, sticky="w", pady=8
        )

        actions = ttk.Frame(frame)
        actions.grid(row=8, column=1, sticky="w", pady=(12, 0))
        ttk.Button(actions, text="Run Collect", command=self.run_collect).pack(side="left")
        ttk.Button(actions, text="Open Output Folder", command=lambda: self._open_folder(self.collect_vars["out_dir"].get())).pack(
            side="left", padx=(8, 0)
        )
        self._configure_grid(frame)
        return frame

    def _entry_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar, placeholder: str = "") -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=6)
        if placeholder:
            ttk.Label(parent, text=placeholder, foreground="#666").grid(row=row, column=2, sticky="w", padx=(8, 0))

    def _path_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar, command) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, sticky="w", padx=(8, 0), pady=6)

    @staticmethod
    def _configure_grid(frame: ttk.Frame) -> None:
        frame.columnconfigure(1, weight=1)

    def _choose_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.clean_vars["input_csv"].set(path)

    def _choose_clean_out_dir(self) -> None:
        self._choose_dir(self.clean_vars["out_dir"])

    def _choose_collect_out_dir(self) -> None:
        self._choose_dir(self.collect_vars["out_dir"])

    @staticmethod
    def _choose_dir(variable: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            variable.set(path)

    def _open_folder(self, folder: str) -> None:
        path = Path(folder)
        if not path.exists():
            messagebox.showinfo("Output folder", f"Folder does not exist yet:\n{path}")
            return
        os.startfile(path) if os.name == "nt" else None

    def append_log(self, text: str) -> None:
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")

    def run_clean(self) -> None:
        input_csv = self.clean_vars["input_csv"].get().strip()
        if not input_csv:
            messagebox.showwarning("Missing input", "Please choose an input CSV file.")
            return
        if not Path(input_csv).exists():
            messagebox.showwarning("Missing input", f"Input CSV does not exist:\n{input_csv}")
            return
        salary_text = self.clean_vars["salary_min"].get().strip()
        try:
            salary_min = float(salary_text) if salary_text else None
        except ValueError:
            messagebox.showwarning("Invalid salary", "Minimum salary must be a number or blank.")
            return

        args = argparse.Namespace(
            input_csv=input_csv,
            out_dir=self.clean_vars["out_dir"].get().strip() or "outputs/jobs",
            cities=self.clean_vars["cities"].get().strip(),
            keywords=self.clean_vars["keywords"].get().strip(),
            salary_min=salary_min,
            xlsx=self.clean_vars["xlsx"].get(),
        )
        self._run_background("Clean CSV", lambda: run_clean(args), args.out_dir)

    def run_collect(self) -> None:
        if not self.collect_vars["url"].get().strip():
            messagebox.showwarning("Missing URL", "Please enter an API URL.")
            return
        try:
            args = argparse.Namespace(
                url=self.collect_vars["url"].get().strip(),
                method=self.collect_vars["method"].get(),
                headers=self.headers_text.get("1.0", "end").strip() or "{}",
                payload=self.payload_text.get("1.0", "end").strip() or "{}",
                page_param=self.collect_vars["page_param"].get().strip() or "page",
                size_param=self.collect_vars["size_param"].get().strip() or "size",
                page_size=int(self.collect_vars["page_size"].get().strip() or "50"),
                records_path=self.collect_vars["records_path"].get().strip() or "data.records",
                total_path=self.collect_vars["total_path"].get().strip(),
                pages_path=self.collect_vars["pages_path"].get().strip(),
                limit=self.collect_vars["limit"].get().strip() or None,
                no_prompt=True,
                max_pages=int(self.collect_vars["max_pages"].get()) if self.collect_vars["max_pages"].get().strip() else None,
                delay=float(self.collect_vars["delay"].get().strip() or "0.5"),
                timeout=float(self.collect_vars["timeout"].get().strip() or "30"),
                xlsx=self.collect_vars["xlsx"].get(),
                out_dir=self.collect_vars["out_dir"].get().strip() or "outputs/collected_jobs",
            )
        except ValueError as exc:
            messagebox.showwarning("Invalid number", str(exc))
            return
        self._run_background("Collect API", lambda: run_collect(args), args.out_dir)

    def _run_background(self, label: str, worker, out_dir: str) -> None:
        self.append_log(f"[{label}] started")

        def run() -> None:
            buffer = io.StringIO()
            try:
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                    worker()
            except Exception as exc:
                output = buffer.getvalue()
                error = exc
                self.after(0, lambda: self._finish_error(label, output, error))
                return
            output = buffer.getvalue()
            self.after(0, lambda: self._finish_success(label, output, out_dir))

        threading.Thread(target=run, daemon=True).start()

    def _finish_success(self, label: str, output: str, out_dir: str) -> None:
        if output.strip():
            self.append_log(output)
        self.append_log(f"[{label}] done. Output: {Path(out_dir).resolve()}")
        messagebox.showinfo(label, f"Done.\nOutput folder:\n{Path(out_dir).resolve()}")

    def _finish_error(self, label: str, output: str, exc: Exception) -> None:
        if output.strip():
            self.append_log(output)
        self.append_log(f"[{label}] failed: {exc}")
        messagebox.showerror(label, str(exc))


def main() -> None:
    app = JobPostingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
