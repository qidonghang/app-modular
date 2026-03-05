"""
ui.py
-----
Everything the user sees and interacts with.

This file handles:
  - The application window layout (buttons, text fields, log panel)
  - User input collection and validation
  - Calling processor.run_processing() in a background thread
  - Displaying results/errors to the user

It does NOT contain any data processing logic.
That all lives in processor.py and sheets.py.
"""

import os
import threading
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog, messagebox, scrolledtext, ttk

from processor import run_processing
import config

# Background colour — defined once so _build_ui and _apply_theme stay in sync
_BG = "#FAFAFA"

# Windows DPI fix — makes text sharp on high-resolution screens
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


class SLSSortingApp:
    """
    The main application window.

    Structure:
      __init__()      — set up fonts, variables, build UI, apply theme
      _build_ui()     — create all the widgets (labels, entries, buttons)
      _apply_theme()  — set colors
      _start()        — validate inputs, then launch processing in background
      _run_safe()     — wrapper that calls run_processing() and shows the result
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SLS Sorting Instruction Generator  v2.0")
        self.root.geometry("1100x1020")
        self.root.resizable(True, True)

        # Scale UI for high-DPI displays
        try:
            self.root.tk.call("tk", "scaling", 1.5)
        except Exception:
            pass

        # Define fonts (fall back to system defaults if Arial/Courier are missing)
        try:
            self.fnt_title = tkFont.Font(family="Arial",       size=22, weight="bold")
            self.fnt_label = tkFont.Font(family="Arial",       size=13)
            self.fnt_mono  = tkFont.Font(family="Courier New", size=12)
            self.fnt_hint  = tkFont.Font(family="Arial",       size=11, slant="italic")
        except Exception:
            self.fnt_title = tkFont.Font(size=22, weight="bold")
            self.fnt_label = tkFont.Font(size=13)
            self.fnt_mono  = tkFont.Font(size=12)
            self.fnt_hint  = tkFont.Font(size=11)

        # StringVars bind each text field to a Python variable
        # Brand Judge and Brand Auth are pre-filled from config.py
        self.sv_batch_no        = tk.StringVar()
        self.sv_all_info        = tk.StringVar()
        self.sv_manifest        = tk.StringVar()
        self.sv_brand_judge_url = tk.StringVar(value=config.BRAND_JUDGE_URL)
        self.sv_brand_auth_url  = tk.StringVar(value=config.BRAND_AUTH_URL)
        self.sv_output_dir      = tk.StringVar()

        self._build_ui()
        self._apply_theme()
        self._center_window(1100, 1020)

    # ── Theme / Colors ────────────────────────────────────────────────────────

    def _apply_theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Shopee colour palette
        BG     = _BG         # near-white background (defined at module level)
        FG     = "#333333"   # dark text
        MID    = "#666666"   # medium grey text
        ORANGE = "#EE4D2D"   # Shopee signature orange
        ORANGE_DARK  = "#D73211"   # hover / pressed
        ORANGE_LIGHT = "#FFF3F0"   # subtle tint for button hover
        BORDER = "#F0D0C8"   # soft orange border for sections

        self.root.configure(bg=_BG)
        style.configure("TFrame",            background=BG)
        style.configure("TLabelframe",       background=BG, bordercolor=BORDER, relief="solid")
        style.configure("TLabelframe.Label", background=BG, foreground=ORANGE, font=("Arial", 13, "bold"))
        style.configure("TLabel",            background=BG, foreground=MID,    font=("Arial", 13))
        style.configure("TEntry",            fieldbackground="#FFFFFF", foreground=FG, padding=6)
        style.configure("TButton",           background="#F5F5F5", foreground=FG,
                         font=("Arial", 11), padding=(10, 6), relief="flat")
        style.map("TButton",                 background=[("active", ORANGE_LIGHT)],
                                             foreground=[("active", ORANGE)])
        style.configure("Accent.TButton",    background=ORANGE, foreground="#FFFFFF",
                         font=("Arial", 13, "bold"), padding=(20, 9), relief="flat")
        style.map("Accent.TButton",          background=[("active", ORANGE_DARK), ("disabled", "#F0A090")])
        style.configure("TSeparator",        background=ORANGE)

        # Log box — keep dark terminal style, orange for info tag
        self.log_box.config(bg="#1A202C", fg="#A0AEC0", insertbackground="#A0AEC0")
        self.log_box.tag_config("ok",   foreground="#68D391")  # green
        self.log_box.tag_config("err",  foreground="#FC8181")  # red
        self.log_box.tag_config("warn", foreground="#F6AD55")  # amber
        self.log_box.tag_config("info", foreground="#EE4D2D")  # Shopee orange
        self.log_box.tag_config("dim",  foreground="#718096")  # grey

    def _center_window(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── UI Layout ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Outer frame + scrollable canvas (so the window can be resized)
        outer  = ttk.Frame(self.root)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0, bg=_BG)
        vscr   = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.body = ttk.Frame(canvas)
        self.body.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=vscr.set)
        canvas.pack(side="left",  fill="both", expand=True)
        vscr.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        PAD = {"padx": 18, "pady": 8}

        # Title
        ttk.Label(self.body, text="SLS Sorting Instruction Generator",
                  font=self.fnt_title, foreground="#EE4D2D").pack(**PAD, anchor="w")
        ttk.Label(self.body, text="Cross-Border Reverse Logistics  |  v2.0",
                  font=self.fnt_hint, foreground="#666666").pack(padx=18, pady=(0, 4), anchor="w")
        ttk.Separator(self.body, orient="horizontal").pack(fill="x", padx=14, pady=4)

        # Step 1 — Batch No.
        f1 = ttk.LabelFrame(self.body, text="Step 1 — Batch No.", padding=10)
        f1.pack(fill="x", **PAD)
        ttk.Label(f1, text="Batch No.  (inserted as Column A in output):") \
            .grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(f1, textvariable=self.sv_batch_no, width=40) \
            .grid(row=0, column=1, padx=10, sticky="ew")
        f1.columnconfigure(1, weight=1)

        # Step 2 — Local files
        f2 = ttk.LabelFrame(self.body, text="Step 2 — Local File Inputs", padding=10)
        f2.pack(fill="x", **PAD)
        self._file_row(f2, 0, "All Info Excel File:", self.sv_all_info,
                       "e.g.  PH Normal All Info Output Combined.xlsx")
        self._file_row(f2, 1, "Manifest Excel File:", self.sv_manifest,
                       "e.g.  PH Normal MNF Output.xlsx")
        f2.columnconfigure(1, weight=1)

        # Step 3 — Google Sheets (with local file fallback)
        f3 = ttk.LabelFrame(self.body,
            text="Step 3 — Brand Data  (Google Sheets URL or local Excel file)",
            padding=10)
        f3.pack(fill="x", **PAD)

        ttk.Label(f3, text="Brand Judge:") \
            .grid(row=0, column=0, sticky="w", pady=(0, 2))
        bj_row = ttk.Frame(f3)
        bj_row.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        ttk.Entry(bj_row, textvariable=self.sv_brand_judge_url) \
            .pack(side="left", fill="x", expand=True)
        ttk.Button(bj_row, text="Browse file...",
                   command=lambda: self._browse_file(
                       self.sv_brand_judge_url,
                       [("Excel/CSV files", "*.xlsx *.xls *.csv"), ("All files", "*.*")]
                   )).pack(side="left", padx=(8, 0))
        ttk.Label(f3,
            text='Columns: "item name brand"  |  "item name exclude"  |  "sub_cagtegory & level3_category exclue"',
            font=self.fnt_hint).grid(row=2, column=0, sticky="w", pady=(0, 10))

        ttk.Label(f3, text="Brand Authorization:") \
            .grid(row=3, column=0, sticky="w", pady=(0, 2))
        ba_row = ttk.Frame(f3)
        ba_row.grid(row=4, column=0, sticky="ew", pady=(0, 2))
        ttk.Entry(ba_row, textvariable=self.sv_brand_auth_url) \
            .pack(side="left", fill="x", expand=True)
        ttk.Button(ba_row, text="Browse file...",
                   command=lambda: self._browse_file(
                       self.sv_brand_auth_url,
                       [("Excel/CSV files", "*.xlsx *.xls *.csv"), ("All files", "*.*")]
                   )).pack(side="left", padx=(8, 0))
        ttk.Label(f3,
            text='Column: "child_shopid"  |  If URL fails, click "Browse file..." to use a local Excel instead',
            font=self.fnt_hint).grid(row=5, column=0, sticky="w")

        f3.columnconfigure(0, weight=1)

        # Step 4 — Output folder
        f4 = ttk.LabelFrame(self.body, text="Step 4 — Output Folder", padding=10)
        f4.pack(fill="x", **PAD)
        row4 = ttk.Frame(f4)
        row4.pack(fill="x")
        ttk.Entry(row4, textvariable=self.sv_output_dir, width=62) \
            .pack(side="left", fill="x", expand=True)
        ttk.Button(row4, text="Browse...", command=self._browse_dir) \
            .pack(side="left", padx=(8, 0))
        ttk.Label(f4,
            text='Output file: "Sorting Instruction of [Batch No].xlsx"',
            font=self.fnt_hint).pack(anchor="w", pady=(4, 0))

        # Log panel
        f5 = ttk.LabelFrame(self.body, text="Processing Log", padding=8)
        f5.pack(fill="both", expand=True, **PAD)
        self.log_box = scrolledtext.ScrolledText(
            f5, height=14, width=100, font=self.fnt_mono, state="disabled")
        self.log_box.pack(fill="both", expand=True)

        # Action buttons
        bf = ttk.Frame(self.body)
        bf.pack(pady=12)
        self.btn_run = ttk.Button(bf, text="Start Processing",
                                  style="Accent.TButton", command=self._start)
        self.btn_run.pack(side="left", padx=8)
        ttk.Button(bf, text="Clear Log", command=self._clear_log).pack(side="left", padx=4)
        ttk.Button(bf, text="Exit",      command=self.root.quit).pack(side="left", padx=4)

    def _file_row(self, parent, idx, label, sv, hint=""):
        """Helper: create a labelled file-picker row."""
        ttk.Label(parent, text=label) \
            .grid(row=idx * 3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        fr = ttk.Frame(parent)
        fr.grid(row=idx * 3 + 1, column=0, columnspan=2, sticky="ew", pady=(0, 2))
        ttk.Entry(fr, textvariable=sv, width=62).pack(side="left", fill="x", expand=True)
        ttk.Button(fr, text="Browse...",
                   command=lambda v=sv: self._browse_file(v)).pack(side="left", padx=(8, 0))
        if hint:
            ttk.Label(parent, text=hint, font=self.fnt_hint) \
                .grid(row=idx * 3 + 2, column=0, columnspan=2, sticky="w")

    # ── File / Folder Pickers ─────────────────────────────────────────────────

    def _browse_file(self, sv, filetypes=None):
        if filetypes is None:
            filetypes = [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        p = filedialog.askopenfilename(title="Select file", filetypes=filetypes)
        if p:
            sv.set(p)

    def _browse_dir(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p:
            self.sv_output_dir.set(p)

    # ── Log Panel ─────────────────────────────────────────────────────────────

    def _log(self, msg: str, tag: str = ""):
        """Append a line to the log panel, with optional colour tag."""
        self.log_box.config(state="normal")
        start = self.log_box.index("end")
        self.log_box.insert("end", msg + "\n")
        if tag:
            self.log_box.tag_add(tag, start, self.log_box.index("end"))
        self.log_box.see("end")
        self.log_box.config(state="disabled")
        self.root.update_idletasks()

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        """Check all required fields before starting. Show error dialogs if any are missing."""
        if not self.sv_batch_no.get().strip():
            messagebox.showerror("Missing input", "Please enter a Batch No.")
            return False
        for label, sv in [("All Info", self.sv_all_info), ("Manifest", self.sv_manifest)]:
            p = sv.get().strip()
            if not p:
                messagebox.showerror("Missing input", f"Please select the {label} file.")
                return False
            if not os.path.isfile(p):
                messagebox.showerror("File not found", f"{label} file not found:\n{p}")
                return False
        if not self.sv_output_dir.get().strip():
            messagebox.showerror("Missing input", "Please select an output folder.")
            return False
        if not os.path.isdir(self.sv_output_dir.get()):
            messagebox.showerror("Folder not found",
                                 f"Output folder not found:\n{self.sv_output_dir.get()}")
            return False
        return True

    # ── Start Processing ──────────────────────────────────────────────────────

    def _start(self):
        if not self._validate():
            return
        self._clear_log()
        self.btn_run.config(state="disabled")
        # Run in a background thread so the window stays responsive
        threading.Thread(target=self._run_safe, daemon=True).start()

    def _run_safe(self):
        """Collect inputs, call run_processing(), show result or error."""
        try:
            params = {
                "batch_no":        self.sv_batch_no.get().strip(),
                "all_info_path":   self.sv_all_info.get().strip(),
                "manifest_path":   self.sv_manifest.get().strip(),
                "brand_judge_url": self.sv_brand_judge_url.get().strip(),
                "brand_auth_url":  self.sv_brand_auth_url.get().strip(),
                "out_dir":         self.sv_output_dir.get().strip(),
            }
            result = run_processing(params, log_fn=self._log)
            messagebox.showinfo("Complete",
                f"File saved!\n\n"
                f"File  : {result['out_fname']}\n"
                f"Rows  : {result['rows']:,}\n"
                f"HKP-F : {result['hkp_f']:,}\n\n"
                f"Location:\n{result['out_dir']}")
        except Exception as exc:
            self._log(f"\nFATAL ERROR: {exc}", "err")
            messagebox.showerror("Error", str(exc))
        finally:
            self.btn_run.config(state="normal")
