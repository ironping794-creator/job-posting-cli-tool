from __future__ import annotations

import argparse
import contextlib
import io
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from . import __version__
from .clean import run as run_clean
from .collect import collect as run_collect
from .url_export import export_url

DATE_RANGE_OPTIONS = {
    "不限": None,
    "近 1 个月": 30,
    "近 3 个月": 90,
    "近半年": 180,
    "近 1 年": 365,
}

BG = "#F4F7FB"
CARD = "#FFFFFF"
TEXT = "#172033"
MUTED = "#64748B"
BORDER = "#D9E2EF"
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
SOFT_ACCENT = "#EAF1FF"
INPUT_BG = "#FBFCFE"


class JobPostingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"招聘岗位数据工具 {__version__}")
        self.geometry("1040x760")
        self.minsize(720, 560)
        self.configure(background=BG)
        self.option_add("*Font", ("Microsoft YaHei UI", 10))

        self.url_vars = {
            "url": tk.StringVar(),
            "out_dir": tk.StringVar(value="outputs/url_export"),
            "max_records": tk.StringVar(value="20000"),
            "cities": tk.StringVar(),
            "keywords": tk.StringVar(),
            "date_range": tk.StringVar(value="不限"),
            "highlight_keywords": tk.StringVar(),
            "highlight_color": tk.StringVar(value="#FFF2CC"),
            "token": tk.StringVar(),
        }
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

        self._configure_style()
        self._build_ui()

    def _configure_style(self) -> None:
        self.style = ttk.Style(self)
        with contextlib.suppress(tk.TclError):
            self.style.theme_use("clam")

        self.style.configure(".", font=("Microsoft YaHei UI", 10), background=BG, foreground=TEXT)
        self.style.configure("App.TFrame", background=BG)
        self.style.configure("Header.TFrame", background=BG)
        self.style.configure("Card.TFrame", background=CARD, relief="flat")
        self.style.configure("Card.TLabelframe", background=CARD, bordercolor=BORDER, relief="solid")
        self.style.configure("Card.TLabelframe.Label", background=CARD, foreground=TEXT, font=("Microsoft YaHei UI", 10, "bold"))
        self.style.configure("TLabel", background=CARD, foreground=TEXT)
        self.style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Microsoft YaHei UI", 22, "bold"))
        self.style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=("Microsoft YaHei UI", 10))
        self.style.configure("Hint.TLabel", background=CARD, foreground=MUTED, font=("Microsoft YaHei UI", 9))
        self.style.configure("Support.TLabel", background=SOFT_ACCENT, foreground=TEXT, font=("Microsoft YaHei UI", 9))
        self.style.configure("Field.TLabel", background=CARD, foreground=TEXT, font=("Microsoft YaHei UI", 10, "bold"))
        self.style.configure("TEntry", fieldbackground=INPUT_BG, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=(8, 5))
        self.style.configure("TCombobox", fieldbackground=INPUT_BG, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=(8, 5))
        self.style.configure("TCheckbutton", background=CARD, foreground=TEXT)
        self.style.configure("Accent.TButton", background=ACCENT, foreground="#FFFFFF", bordercolor=ACCENT, focusthickness=0, padding=(16, 8))
        self.style.map("Accent.TButton", background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)], foreground=[("disabled", "#E5E7EB")])
        self.style.configure("Secondary.TButton", background="#FFFFFF", foreground=TEXT, bordercolor=BORDER, focusthickness=0, padding=(14, 8))
        self.style.map("Secondary.TButton", background=[("active", SOFT_ACCENT), ("pressed", SOFT_ACCENT)])
        self.style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 6, 0, 0))
        self.style.configure("TNotebook.Tab", background="#E9EEF7", foreground=MUTED, padding=(18, 8), borderwidth=0)
        self.style.map("TNotebook.Tab", background=[("selected", CARD), ("active", "#F8FAFC")], foreground=[("selected", TEXT), ("active", TEXT)])

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=18, style="App.TFrame")
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root, style="Header.TFrame")
        header.pack(fill="x", pady=(0, 14))
        tk.Label(
            header,
            text="招聘岗位数据工具",
            background=BG,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="粘贴网址、清洗 CSV、采集公开接口，一键导出 Excel。",
            background=BG,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)
        notebook.add(self._scrollable_tab(notebook, self._url_tab), text="粘贴网址导出")
        notebook.add(self._scrollable_tab(notebook, self._clean_tab), text="清洗 CSV")
        notebook.add(self._scrollable_tab(notebook, self._collect_tab), text="接口采集")

        log_frame = ttk.LabelFrame(root, text="运行日志", padding=12, style="Card.TLabelframe")
        log_frame.pack(fill="both", expand=False, pady=(14, 0))
        self.log = tk.Text(
            log_frame,
            height=6,
            wrap="word",
            borderwidth=0,
            relief="flat",
            background="#F8FAFC",
            foreground=TEXT,
            insertbackground=TEXT,
            padx=10,
            pady=8,
        )
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        scrollbar.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=scrollbar.set)

    def _scrollable_tab(self, parent: ttk.Notebook, builder) -> ttk.Frame:
        outer = ttk.Frame(parent, style="Card.TFrame")
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0, background=CARD)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        content = builder(canvas)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def sync_scroll_region(_: tk.Event | None = None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_content_width(event: tk.Event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        def on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", sync_scroll_region)
        canvas.bind("<Configure>", sync_content_width)
        outer.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", on_mousewheel))
        outer.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
        return outer

    def _url_tab(self, parent: tk.Misc) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=18, style="Card.TFrame")
        intro = ttk.Label(
            frame,
            text="把公开招聘页面网址粘贴进来，按需填写筛选条件，点击按钮导出 Excel。请只导出你有权限访问的数据。",
            style="Hint.TLabel",
            wraplength=780,
        )
        intro.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        self._supported_sites_panel(frame, 1)
        self._entry_row(frame, 2, "招聘网址", self.url_vars["url"], "粘贴公开招聘页面网址")
        self._path_row(frame, 3, "输出文件夹", self.url_vars["out_dir"], self._choose_url_out_dir)
        self._entry_row(frame, 4, "城市筛选", self.url_vars["cities"], "多个城市用逗号分隔，可留空")
        self._entry_row(frame, 5, "岗位/关键词筛选", self.url_vars["keywords"], "匹配公司、标题、行业、岗位，可留空")
        self._combo_row(
            frame,
            6,
            "发布日期范围",
            self.url_vars["date_range"],
            list(DATE_RANGE_OPTIONS.keys()),
            "按发布时间过滤，可选最近 1 个月/半年/一年",
        )
        self._entry_row(frame, 7, "最多导出条数", self.url_vars["max_records"], "筛选前最多保留多少条；可改小以快速测试")
        self._entry_row(frame, 8, "高亮关键词", self.url_vars["highlight_keywords"], "留空时使用岗位/关键词筛选")
        self._color_row(frame, 9)
        self._entry_row(frame, 10, "登录 Token（可选）", self.url_vars["token"], "通常不用填；需要授权数据时再填")

        actions = self._actions_row(frame, 11)
        ttk.Button(actions, text="一键导出 Excel", style="Accent.TButton", command=self.run_url_export).pack(side="left", padx=(0, 10), pady=4)
        ttk.Button(actions, text="打开输出文件夹", style="Secondary.TButton", command=lambda: self._open_folder(self.url_vars["out_dir"].get())).pack(side="left", pady=4)
        self._configure_grid(frame)
        return frame

    def _clean_tab(self, parent: tk.Misc) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=18, style="Card.TFrame")
        self._path_row(frame, 0, "输入 CSV", self.clean_vars["input_csv"], self._choose_csv)
        self._path_row(frame, 1, "输出文件夹", self.clean_vars["out_dir"], self._choose_clean_out_dir)
        self._entry_row(frame, 2, "城市筛选", self.clean_vars["cities"], "上海,北京,深圳")
        self._entry_row(frame, 3, "关键词筛选", self.clean_vars["keywords"], "AI,大模型,数据分析")
        self._entry_row(frame, 4, "最低薪资", self.clean_vars["salary_min"], "8000")
        self._check_row(frame, 5, "同时导出格式化 XLSX 文件", self.clean_vars["xlsx"])

        actions = self._actions_row(frame, 6)
        ttk.Button(actions, text="开始清洗", style="Accent.TButton", command=self.run_clean).pack(side="left", padx=(0, 10), pady=4)
        ttk.Button(actions, text="打开输出文件夹", style="Secondary.TButton", command=lambda: self._open_folder(self.clean_vars["out_dir"].get())).pack(side="left", pady=4)
        self._configure_grid(frame)
        return frame

    def _collect_tab(self, parent: tk.Misc) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=18, style="Card.TFrame")
        self._entry_row(frame, 0, "接口地址", self.collect_vars["url"], "https://example.com/api/jobs")
        self._combo_row(frame, 1, "请求方法", self.collect_vars["method"], ["POST", "GET"])

        body = self._field_container(frame, 2, "请求头 JSON")
        self.headers_text = tk.Text(body, height=4, width=1, borderwidth=1, relief="solid", background=INPUT_BG, foreground=TEXT, padx=8, pady=6)
        self.headers_text.insert("1.0", "{}")
        self.headers_text.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        body = self._field_container(frame, 3, "参数 JSON")
        self.payload_text = tk.Text(body, height=5, width=1, borderwidth=1, relief="solid", background=INPUT_BG, foreground=TEXT, padx=8, pady=6)
        self.payload_text.insert("1.0", "{}")
        self.payload_text.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        paths = self._field_container(frame, 4, "分页和数据路径", "根据接口返回 JSON 填写；不确定时先保留默认值。")
        paths.columnconfigure(1, weight=1)
        paths.columnconfigure(3, weight=1)
        for index, (label, key, width) in enumerate(
            [
                ("页码", "page_param", 10),
                ("每页数", "size_param", 10),
                ("列表路径", "records_path", 18),
                ("总数路径", "total_path", 14),
                ("总页路径", "pages_path", 14),
            ]
        ):
            row = index // 2 + 2
            column = (index % 2) * 2
            ttk.Label(paths, text=label, style="Hint.TLabel").grid(row=row, column=column, sticky="w", padx=(0, 5), pady=4)
            ttk.Entry(paths, textvariable=self.collect_vars[key], width=width).grid(row=row, column=column + 1, sticky="ew", padx=(0, 12), pady=4)

        numbers = self._field_container(frame, 5, "采集数量和网络设置")
        numbers.columnconfigure(1, weight=1)
        numbers.columnconfigure(3, weight=1)
        for index, (label, key, width) in enumerate(
            [
                ("每页数量", "page_size", 8),
                ("采集数量", "limit", 10),
                ("最大页数", "max_pages", 10),
                ("延迟", "delay", 8),
                ("超时", "timeout", 8),
            ]
        ):
            row = index // 2 + 2
            column = (index % 2) * 2
            ttk.Label(numbers, text=label, style="Hint.TLabel").grid(row=row, column=column, sticky="w", padx=(0, 5), pady=4)
            ttk.Entry(numbers, textvariable=self.collect_vars[key], width=width).grid(row=row, column=column + 1, sticky="ew", padx=(0, 12), pady=4)

        self._path_row(frame, 6, "输出文件夹", self.collect_vars["out_dir"], self._choose_collect_out_dir)
        self._check_row(frame, 7, "同时导出格式化 XLSX 文件", self.collect_vars["xlsx"])

        actions = self._actions_row(frame, 8)
        ttk.Button(actions, text="开始采集", style="Accent.TButton", command=self.run_collect).pack(side="left", padx=(0, 10), pady=4)
        ttk.Button(actions, text="打开输出文件夹", style="Secondary.TButton", command=lambda: self._open_folder(self.collect_vars["out_dir"].get())).pack(side="left", pady=4)
        self._configure_grid(frame)
        return frame

    def _entry_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar, placeholder: str = "") -> None:
        body = self._field_container(parent, row, label, placeholder)
        ttk.Entry(body, textvariable=variable).grid(row=2, column=0, sticky="ew", pady=(6, 0))

    def _path_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar, command) -> None:
        body = self._field_container(parent, row, label)
        line = ttk.Frame(body, style="Card.TFrame")
        line.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        line.columnconfigure(0, weight=1)
        ttk.Entry(line, textvariable=variable).grid(row=0, column=0, sticky="ew")
        ttk.Button(line, text="浏览", style="Secondary.TButton", command=command).grid(row=0, column=1, sticky="e", padx=(10, 0))

    def _color_row(self, parent: ttk.Frame, row: int) -> None:
        body = self._field_container(parent, row, "高亮颜色", "用于标出命中关键词的单元格")
        color_frame = ttk.Frame(body, style="Card.TFrame")
        color_frame.grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(color_frame, textvariable=self.url_vars["highlight_color"], width=12).pack(side="left")
        ttk.Button(color_frame, text="选择颜色", style="Secondary.TButton", command=self._choose_highlight_color).pack(side="left", padx=(10, 0))
        self.highlight_swatch = tk.Label(color_frame, width=4, height=1, background=self.url_vars["highlight_color"].get(), relief="flat")
        self.highlight_swatch.pack(side="left", padx=(10, 0), ipadx=8, ipady=5)

    def _supported_sites_panel(self, parent: ttk.Frame, row: int) -> None:
        text = "支持自动抓取：offer.gfjianli.com、带结构化 __NUXT_DATA__ 的公开招聘页；公开 JSON API 请用“接口采集”。"
        ttk.Label(parent, text=text, style="Support.TLabel", padding=(10, 7), wraplength=760).grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=(0, 12)
        )

    def _combo_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        values: list[str],
        hint: str = "",
    ) -> None:
        body = self._field_container(parent, row, label, hint)
        ttk.Combobox(body, textvariable=variable, values=values, width=16, state="readonly").grid(row=2, column=0, sticky="w", pady=(6, 0))

    def _check_row(self, parent: ttk.Frame, row: int, text: str, variable: tk.BooleanVar) -> None:
        body = ttk.Frame(parent, style="Card.TFrame")
        body.grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Checkbutton(body, text=text, variable=variable).pack(anchor="w")

    def _actions_row(self, parent: ttk.Frame, row: int) -> ttk.Frame:
        body = ttk.Frame(parent, style="Card.TFrame")
        body.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        return body

    def _field_container(self, parent: ttk.Frame, row: int, label: str, hint: str = "") -> ttk.Frame:
        body = ttk.Frame(parent, style="Card.TFrame")
        body.grid(row=row, column=0, columnspan=3, sticky="ew", pady=7)
        body.columnconfigure(0, weight=1)
        ttk.Label(body, text=label, style="Field.TLabel").grid(row=0, column=0, sticky="w")
        if hint:
            ttk.Label(body, text=hint, style="Hint.TLabel", wraplength=760).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return body

    @staticmethod
    def _configure_grid(frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)

    def _choose_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")])
        if path:
            self.clean_vars["input_csv"].set(path)

    def _choose_clean_out_dir(self) -> None:
        self._choose_dir(self.clean_vars["out_dir"])

    def _choose_url_out_dir(self) -> None:
        self._choose_dir(self.url_vars["out_dir"])

    def _choose_collect_out_dir(self) -> None:
        self._choose_dir(self.collect_vars["out_dir"])

    def _choose_highlight_color(self) -> None:
        _, color = colorchooser.askcolor(color=self.url_vars["highlight_color"].get(), title="选择高亮颜色")
        if color:
            self.url_vars["highlight_color"].set(color)
            self.highlight_swatch.configure(background=color)

    @staticmethod
    def _choose_dir(variable: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            variable.set(path)

    def _open_folder(self, folder: str) -> None:
        path = Path(folder)
        if not path.exists():
            messagebox.showinfo("输出文件夹", f"文件夹还不存在：\n{path}")
            return
        os.startfile(path) if os.name == "nt" else None

    def append_log(self, text: str) -> None:
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")

    def run_url_export(self) -> None:
        url = self.url_vars["url"].get().strip()
        if not url:
            messagebox.showwarning("缺少网址", "请先粘贴招聘网站网址。")
            return
        try:
            max_records = int(self.url_vars["max_records"].get().strip() or "20000")
            if max_records <= 0:
                raise ValueError("最多导出条数必须大于 0。")
        except ValueError as exc:
            messagebox.showwarning("数字格式错误", str(exc))
            return
        out_dir = self.url_vars["out_dir"].get().strip() or "outputs/url_export"
        token = self.url_vars["token"].get().strip()
        cities = self.url_vars["cities"].get().strip()
        keywords = self.url_vars["keywords"].get().strip()
        highlight_keywords = self.url_vars["highlight_keywords"].get().strip()
        highlight_color = self.url_vars["highlight_color"].get().strip() or "#FFF2CC"
        published_within_days = DATE_RANGE_OPTIONS.get(self.url_vars["date_range"].get())
        self._run_background(
            "网址导出 Excel",
            lambda: export_url(
                url,
                out_dir,
                max_records,
                token,
                cities,
                keywords,
                published_within_days,
                highlight_keywords,
                highlight_color,
            ),
            out_dir,
        )

    def run_clean(self) -> None:
        input_csv = self.clean_vars["input_csv"].get().strip()
        if not input_csv:
            messagebox.showwarning("缺少输入", "请选择输入 CSV 文件。")
            return
        if not Path(input_csv).exists():
            messagebox.showwarning("缺少输入", f"输入 CSV 不存在：\n{input_csv}")
            return
        salary_text = self.clean_vars["salary_min"].get().strip()
        try:
            salary_min = float(salary_text) if salary_text else None
        except ValueError:
            messagebox.showwarning("薪资格式错误", "最低薪资必须是数字，或留空。")
            return

        args = argparse.Namespace(
            input_csv=input_csv,
            out_dir=self.clean_vars["out_dir"].get().strip() or "outputs/jobs",
            cities=self.clean_vars["cities"].get().strip(),
            keywords=self.clean_vars["keywords"].get().strip(),
            salary_min=salary_min,
            xlsx=self.clean_vars["xlsx"].get(),
        )
        self._run_background("清洗 CSV", lambda: run_clean(args), args.out_dir)

    def run_collect(self) -> None:
        if not self.collect_vars["url"].get().strip():
            messagebox.showwarning("缺少接口地址", "请输入 API URL。")
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
            messagebox.showwarning("数字格式错误", str(exc))
            return
        self._run_background("接口采集", lambda: run_collect(args), args.out_dir)

    def _run_background(self, label: str, worker, out_dir: str) -> None:
        self.append_log(f"[{label}] 开始运行")

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
        self.append_log(f"[{label}] 已完成。输出位置：{Path(out_dir).resolve()}")
        messagebox.showinfo(label, f"完成。\n输出文件夹：\n{Path(out_dir).resolve()}")

    def _finish_error(self, label: str, output: str, exc: Exception) -> None:
        if output.strip():
            self.append_log(output)
        self.append_log(f"[{label}] 失败：{exc}")
        messagebox.showerror(label, str(exc))


def main() -> None:
    app = JobPostingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
