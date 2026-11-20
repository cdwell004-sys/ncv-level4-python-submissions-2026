"""
Community Water Consumption and Billing Management System
NCV Level 4 - Advanced Python - Individual practical assessment

Reads water_readings.txt, validates every record, calculates monthly
consumption and progressive charges, classifies households, ranks the
top five consumers and writes billing_report.txt and errors.log.
A Tkinter GUI is provided so the whole process can be run with buttons.

Record layout: MeterNumber,HouseholdName,PreviousReading,CurrentReading,Area
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ======================================================================
# SECTION 1: CONSTANTS (tariff, class limits, file names)
# ======================================================================
INPUT_FILE = "water_readings.txt"
REPORT_FILE = "billing_report.txt"
ERROR_FILE = "errors.log"

FREE_LIMIT = 6          # first 6 kL are free
BAND2_LIMIT = 20        # above 6 up to 20 kL
BAND2_RATE = 8.50       # Rand per kL in band 2
BAND3_RATE = 12.00      # Rand per kL above 20 kL

LOW_LIMIT = 20          # LOW      = 0 - 20 kL
MODERATE_LIMIT = 50     # MODERATE = above 20 up to 50 kL, HIGH = above 50

FIELD_NAMES = ["MeterNumber", "HouseholdName", "PreviousReading",
               "CurrentReading", "Area"]


# ======================================================================
# SECTION 2: FILE READING (Q1)
# ======================================================================
def read_lines(path):
    """Return (list_of_lines, error_message). Never crashes on a bad file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines, None
    except FileNotFoundError:
        return [], "File not found: " + path
    except PermissionError:
        return [], "No permission to read: " + path
    except OSError as err:
        return [], "Could not read file: " + str(err)


# ======================================================================
# SECTION 3: CLEANING AND VALIDATION (Q2 and Q3)
# ======================================================================
def to_whole_number(text):
    """Convert text to int. Return None if it is not a whole number."""
    digits = text
    negative = False
    if digits.startswith("-"):
        negative = True
        digits = digits[1:]
    if not digits.isdigit():
        return None
    try:
        value = int(digits)
    except ValueError:
        return None
    if negative:
        value = -value
    return value


def validate_line(line, records):
    """
    Check one line of the file.
    Returns (record_dict, None) if valid, or (None, reason) if rejected.
    'records' holds the already accepted records (used for duplicates).
    """
    # --- split and clean every field ---
    parts = line.split(",")
    if len(parts) != 5:
        return None, "Missing or extra fields (expected 5, found " + str(len(parts)) + ")"

    fields = []
    for p in parts:
        fields.append(p.strip())

    # --- missing (empty) fields ---
    for i in range(5):
        if fields[i] == "":
            return None, "Missing field: " + FIELD_NAMES[i]

    meter, name, prev_text, curr_text, area = fields

    # --- duplicate meter number ---
    if meter.upper() in records:
        return None, "Duplicate meter number: " + meter

    # --- non-numeric readings ---
    previous = to_whole_number(prev_text)
    if previous is None:
        return None, "Non-numeric previous reading: '" + prev_text + "'"
    current = to_whole_number(curr_text)
    if current is None:
        return None, "Non-numeric current reading: '" + curr_text + "'"

    # --- negative readings ---
    if previous < 0:
        return None, "Negative previous reading: " + str(previous)
    if current < 0:
        return None, "Negative current reading: " + str(current)

    # --- reversed readings ---
    if current < previous:
        return None, ("Current reading (" + str(current) +
                      ") is below previous reading (" + str(previous) + ")")

    record = {"meter": meter, "name": name, "area": area,
              "previous": previous, "current": current,
              "usage": 0, "charge": 0.0, "category": ""}
    return record, None


def load_records(lines):
    """
    Validate every line. Returns (records_dict, rejected_list).
    rejected_list items are dictionaries: line number, raw text, reason.
    """
    records = {}
    rejected = []
    line_number = 0
    for raw in lines:
        line_number += 1
        text = raw.strip()
        if text == "":
            rejected.append({"line": line_number, "text": "", "reason": "Blank line"})
            continue
        record, reason = validate_line(text, records)
        if record is None:
            rejected.append({"line": line_number, "text": text, "reason": reason})
        else:
            records[record["meter"].upper()] = record
    return records, rejected


# ======================================================================
# SECTION 4: CALCULATIONS (Q4, Q5, Q6)
# ======================================================================
def calculate_usage(previous, current):
    """Q4: monthly consumption in kL."""
    return current - previous


def calculate_charge(usage):
    """Q5: progressive tariff. 0-6 free, 6-20 at R8.50, above 20 at R12.00."""
    if usage <= FREE_LIMIT:
        charge = 0.0
    elif usage <= BAND2_LIMIT:
        charge = (usage - FREE_LIMIT) * BAND2_RATE
    else:
        band2_kl = BAND2_LIMIT - FREE_LIMIT          # 14 kL
        charge = band2_kl * BAND2_RATE + (usage - BAND2_LIMIT) * BAND3_RATE
    return charge


def classify_usage(usage):
    """Q6: LOW / MODERATE / HIGH."""
    if usage <= LOW_LIMIT:
        return "LOW"
    elif usage <= MODERATE_LIMIT:
        return "MODERATE"
    else:
        return "HIGH"


def apply_calculations(records):
    """Fill usage, charge and category for every accepted household."""
    for key in records:
        rec = records[key]
        rec["usage"] = calculate_usage(rec["previous"], rec["current"])
        rec["charge"] = calculate_charge(rec["usage"])
        rec["category"] = classify_usage(rec["usage"])


# ======================================================================
# SECTION 5: MANUAL RANKING OF TOP FIVE (Q7) - no sorted(), max(), min()
# ======================================================================
def rank_top_five(records):
    """
    Repeatedly scan all households for the highest usage that has not
    been picked yet. Ties: the household that appears first in the file wins.
    """
    chosen_keys = []
    for rank in range(5):
        best_key = None
        for key in records:
            if key in chosen_keys:
                continue
            if best_key is None or records[key]["usage"] > records[best_key]["usage"]:
                best_key = key
        if best_key is None:          # fewer than five households
            break
        chosen_keys.append(best_key)

    top = []
    for key in chosen_keys:
        top.append(records[key])
    return top


# ======================================================================
# SECTION 6: SUMMARY AND REPORT WRITING (Q8)
# ======================================================================
def money(amount):
    return "R{:,.2f}".format(amount)


def build_summary(records, rejected, total_lines):
    """Totals calculated with loops (no sum())."""
    total_usage = 0
    total_billed = 0.0
    low = 0
    moderate = 0
    high = 0
    for key in records:
        rec = records[key]
        total_usage = total_usage + rec["usage"]
        total_billed = total_billed + rec["charge"]
        if rec["category"] == "LOW":
            low = low + 1
        elif rec["category"] == "MODERATE":
            moderate = moderate + 1
        else:
            high = high + 1

    accepted = len(records)
    average = total_usage / accepted if accepted > 0 else 0.0
    return {"lines": total_lines, "accepted": accepted, "rejected": len(rejected),
            "usage": total_usage, "billed": total_billed, "average": average,
            "low": low, "moderate": moderate, "high": high}


def summary_text(s):
    lines = [
        "Total lines read      : " + str(s["lines"]),
        "Accepted records      : " + str(s["accepted"]),
        "Rejected records      : " + str(s["rejected"]),
        "Total consumption     : " + str(s["usage"]) + " kL",
        "Average consumption   : {:.2f} kL".format(s["average"]),
        "Total amount billed   : " + money(s["billed"]),
        "LOW households       : " + str(s["low"]),
        "MODERATE households  : " + str(s["moderate"]),
        "HIGH households      : " + str(s["high"]),
    ]
    return "\n".join(lines)


def write_billing_report(path, records, top_five, summary):
    """Write billing_report.txt."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("COMMUNITY WATER BILLING REPORT\n")
        f.write("=" * 96 + "\n\n")
        f.write("1. HOUSEHOLD BILLING AND CONSUMPTION CATEGORIES\n")
        f.write("-" * 96 + "\n")
        f.write("{:<8}{:<22}{:<18}{:>6}{:>6}{:>8}{:>12}  {}\n".format(
            "Meter", "Household", "Area", "Prev", "Curr", "kL", "Charge", "Category"))
        f.write("-" * 96 + "\n")
        for key in records:
            r = records[key]
            f.write("{:<8}{:<22}{:<18}{:>6}{:>6}{:>8}{:>12}  {}\n".format(
                r["meter"], r["name"], r["area"], r["previous"], r["current"],
                r["usage"], money(r["charge"]), r["category"]))

        f.write("\n2. TOP FIVE HIGHEST-CONSUMING HOUSEHOLDS\n")
        f.write("-" * 96 + "\n")
        position = 0
        for r in top_five:
            position = position + 1
            f.write("{}. {:<8}{:<22}{:<18}{:>6} kL  {:>12}\n".format(
                position, r["meter"], r["name"], r["area"], r["usage"], money(r["charge"])))

        f.write("\n3. SUMMARY\n")
        f.write("-" * 96 + "\n")
        f.write(summary_text(summary) + "\n")


def write_error_log(path, rejected):
    """Write errors.log with one entry per rejected record."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("REJECTED RECORDS LOG\n")
        f.write("=" * 70 + "\n")
        for item in rejected:
            f.write("Line " + str(item["line"]) + ": " + item["text"] + "\n")
            f.write("    Reason: " + item["reason"] + "\n")
        f.write("=" * 70 + "\n")
        f.write("Total rejected: " + str(len(rejected)) + "\n")


# ======================================================================
# SECTION 7: MAIN PROCESSING PIPELINE (used by the GUI)
# ======================================================================
def run_billing(input_path):
    """
    Run the full process. Returns a result dictionary.
    result["error"] is set (and nothing else) if the file cannot be read.
    """
    lines, error = read_lines(input_path)
    if error is not None:
        return {"error": error}

    records, rejected = load_records(lines)
    apply_calculations(records)
    top_five = rank_top_five(records)
    summary = build_summary(records, rejected, len(lines))

    folder = os.path.dirname(os.path.abspath(input_path))
    report_path = os.path.join(folder, REPORT_FILE)
    error_path = os.path.join(folder, ERROR_FILE)
    try:
        write_billing_report(report_path, records, top_five, summary)
        write_error_log(error_path, rejected)
    except OSError as err:
        return {"error": "Could not write report files: " + str(err)}

    return {"error": None, "records": records, "rejected": rejected,
            "top_five": top_five, "summary": summary,
            "report_path": report_path, "error_path": error_path}


# ======================================================================
# SECTION 8: GRAPHICAL USER INTERFACE
# ======================================================================
def default_input_path():
    """Look for water_readings.txt next to this program."""
    try:
        folder = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        folder = os.getcwd()
    return os.path.join(folder, INPUT_FILE)


def open_with_system(path):
    """Open a file or folder with the computer's default program."""
    try:
        if not os.path.exists(path):
            messagebox.showinfo("Not available yet",
                                "That file has not been created yet.\n"
                                "Click 'Process File' first.")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as err:
        messagebox.showerror("Could not open", str(err))


def bill_breakdown(usage):
    """Return a plain-language, band-by-band explanation of a bill."""
    if usage <= FREE_LIMIT:
        free_kl = usage
        band2_kl = 0
        band3_kl = 0
    elif usage <= BAND2_LIMIT:
        free_kl = FREE_LIMIT
        band2_kl = usage - FREE_LIMIT
        band3_kl = 0
    else:
        free_kl = FREE_LIMIT
        band2_kl = BAND2_LIMIT - FREE_LIMIT
        band3_kl = usage - BAND2_LIMIT

    cost2 = band2_kl * BAND2_RATE
    cost3 = band3_kl * BAND3_RATE
    lines = [
        "Free band     : {:>3} kL x R0.00   = {:>10}".format(free_kl, money(0)),
        "Band 2 (R8.50): {:>3} kL x R8.50   = {:>10}".format(band2_kl, money(cost2)),
        "Band 3 (R12)  : {:>3} kL x R12.00  = {:>10}".format(band3_kl, money(cost3)),
        "-" * 43,
        "TOTAL CHARGE  : {:>27}".format(money(cost2 + cost3)),
    ]
    return "\n".join(lines)


HELP_TEXT = """HOW TO USE THIS PROGRAM

1. Make sure water_readings.txt is in the same folder as this program
   (or click 'Browse' and choose it).
2. Click 'Process File' (or press F5).
3. Look through the tabs:
     Billing        - every valid household and its bill
     Rejected       - records with errors and the reason why
     Top 5          - the five highest water users
     Summary        - totals for the whole municipality
     Tariff Tester  - try any kL value and see the charge
4. Two files are saved automatically in the same folder:
     billing_report.txt   and   errors.log
   Use the buttons at the bottom to open them.

TIPS
  * Type in the search box to find a household, meter or area.
  * Use the category drop-down to show only LOW, MODERATE or HIGH users.
  * Double-click any household to see how its bill was worked out.

TARIFF (progressive)
  First 6 kL ............ Free
  Next 14 kL (6 to 20) .. R8.50 per kL
  Above 20 kL ........... R12.00 per kL

CATEGORIES
  LOW       0 to 20 kL
  MODERATE  above 20 up to 50 kL
  HIGH      above 50 kL

KEYBOARD SHORTCUTS
  F5 = Process file      Ctrl+O = Browse for a file
"""


class WaterBillingApp:
    # colour palette
    BLUE = "#0b5394"
    LIGHT = "#f3f6fa"
    GREEN = "#2e7d32"
    RED = "#c62828"
    ORANGE = "#ef6c00"
    PURPLE = "#6a1b9a"

    def __init__(self, root):
        self.root = root
        self.result = None
        root.title("Community Water Billing Management System")
        root.geometry("1080x720")
        root.minsize(920, 620)
        root.configure(bg=self.LIGHT)

        self.file_var = tk.StringVar(value=default_input_path())
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")
        self.count_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Welcome! Click 'Process File' to begin.")

        self.setup_style()
        self.build_header()
        self.build_file_bar()
        self.build_cards()
        self.build_status_bar()      # bottom items are packed before the tabs
        self.build_action_bar()
        self.build_tabs()

        # live search / filter
        self.search_var.trace_add("write", lambda *args: self.refresh_billing())
        self.filter_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_billing())

        # keyboard shortcuts
        root.bind("<F5>", lambda e: self.process())
        root.bind("<Control-o>", lambda e: self.browse())

        if os.path.exists(self.file_var.get()):
            self.process()
        else:
            self.status_var.set("Could not find " + INPUT_FILE +
                                " next to the program. Click 'Browse' to choose it.")

    # ---------- styling ----------
    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TNotebook.Tab", padding=(14, 6), font=("Segoe UI", 10, "bold"))
        style.configure("Main.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.configure("TButton", font=("Segoe UI", 10), padding=5)

    # ---------- layout ----------
    def build_header(self):
        header = tk.Frame(self.root, bg=self.BLUE)
        header.pack(fill="x")
        tk.Label(header, text="Community Water Billing", bg=self.BLUE, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=(10, 0))
        tk.Label(header, text="Check meter readings, calculate bills and find high water users",
                 bg=self.BLUE, fg="#cfe3f7", font=("Segoe UI", 10)).pack(
                     anchor="w", padx=16, pady=(0, 10))

    def build_file_bar(self):
        bar = tk.Frame(self.root, bg=self.LIGHT)
        bar.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(bar, text="Step 1:  Readings file", bg=self.LIGHT,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        entry = ttk.Entry(bar, textvariable=self.file_var, font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True, padx=8)
        entry.bind("<Return>", lambda e: self.process())
        ttk.Button(bar, text="Browse...", command=self.browse).pack(side="left")
        tk.Label(bar, text="   Step 2:", bg=self.LIGHT,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(bar, text="Process File  \u25b6", style="Main.TButton",
                   command=self.process).pack(side="left", padx=(8, 0))

    def make_card(self, parent, title, colour):
        """A coloured summary box. Returns the StringVar that holds its value."""
        value = tk.StringVar(value="-")
        card = tk.Frame(parent, bg=colour)
        card.pack(side="left", fill="x", expand=True, padx=5)
        tk.Label(card, textvariable=value, bg=colour, fg="white",
                 font=("Segoe UI", 20, "bold")).pack(pady=(8, 0))
        tk.Label(card, text=title, bg=colour, fg="white",
                 font=("Segoe UI", 9)).pack(pady=(0, 8))
        return value

    def build_cards(self):
        row = tk.Frame(self.root, bg=self.LIGHT)
        row.pack(fill="x", padx=9, pady=8)
        self.card_accepted = self.make_card(row, "ACCEPTED HOUSEHOLDS", self.GREEN)
        self.card_rejected = self.make_card(row, "REJECTED RECORDS", self.RED)
        self.card_usage = self.make_card(row, "TOTAL WATER USED", self.BLUE)
        self.card_billed = self.make_card(row, "TOTAL BILLED", self.PURPLE)

    def build_status_bar(self):
        tk.Label(self.root, textvariable=self.status_var, anchor="w", bg="#dde6f0",
                 font=("Segoe UI", 9), padx=10, pady=5).pack(fill="x", side="bottom")

    def build_action_bar(self):
        bar = tk.Frame(self.root, bg=self.LIGHT)
        bar.pack(fill="x", side="bottom", padx=14, pady=6)
        tk.Label(bar, text="Saved files:", bg=self.LIGHT,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(bar, text="Open Billing Report", command=self.open_report).pack(
            side="left", padx=6)
        ttk.Button(bar, text="Open Error Log", command=self.open_errors).pack(side="left")
        ttk.Button(bar, text="Open Folder", command=self.open_folder).pack(
            side="left", padx=6)
        ttk.Button(bar, text="Help", command=lambda: self.tabs.select(self.help_tab)).pack(
            side="right")

    def build_tabs(self):
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        # ----- Billing tab -----
        t1 = ttk.Frame(self.tabs, padding=6)
        self.tabs.add(t1, text="  Billing  ")
        tools = ttk.Frame(t1)
        tools.pack(fill="x", pady=(0, 6))
        ttk.Label(tools, text="Search:").pack(side="left")
        ttk.Entry(tools, textvariable=self.search_var, width=28).pack(side="left", padx=6)
        ttk.Button(tools, text="Clear", command=lambda: self.search_var.set("")).pack(
            side="left")
        ttk.Label(tools, text="   Show:").pack(side="left")
        self.filter_box = ttk.Combobox(tools, textvariable=self.filter_var, width=12,
                                       state="readonly",
                                       values=["All", "LOW", "MODERATE", "HIGH"])
        self.filter_box.pack(side="left", padx=6)
        ttk.Label(tools, textvariable=self.count_var,
                  foreground="#555555").pack(side="right")
        cols = ("Meter", "Household", "Area", "Previous", "Current", "kL used",
                "Charge", "Category")
        self.billing_table = self.make_table(
            t1, cols, (70, 190, 150, 80, 80, 80, 100, 100))
        self.billing_table.tag_configure("LOW", background="#e8f5e9")
        self.billing_table.tag_configure("MODERATE", background="#fff8e1")
        self.billing_table.tag_configure("HIGH", background="#fde2e2")
        self.billing_table.bind("<Double-1>", self.show_bill_details)
        ttk.Label(t1, foreground="#555555",
                  text="Green = LOW    Yellow = MODERATE    Red = HIGH    "
                       "(double-click a household to see its bill breakdown)").pack(
                           anchor="w", pady=(6, 0))

        # ----- Rejected tab -----
        t2 = ttk.Frame(self.tabs, padding=6)
        self.tabs.add(t2, text="  Rejected  ")
        ttk.Label(t2, foreground="#555555",
                  text="These records were not billed. Fix them in the file and process again."
                  ).pack(anchor="w", pady=(0, 6))
        self.error_table = self.make_table(t2, ("Line", "Record", "Why it was rejected"),
                                           (60, 340, 450))

        # ----- Top 5 tab -----
        t3 = ttk.Frame(self.tabs, padding=6)
        self.tabs.add(t3, text="  Top 5  ")
        ttk.Label(t3, foreground="#555555",
                  text="The five households that used the most water this month."
                  ).pack(anchor="w", pady=(0, 6))
        self.top_table = self.make_table(
            t3, ("Rank", "Meter", "Household", "Area", "kL used", "Charge"),
            (60, 80, 220, 160, 90, 110))
        self.top_table.tag_configure("HIGH", background="#fde2e2")
        self.top_table.bind("<Double-1>", self.show_bill_details)

        # ----- Summary tab -----
        t4 = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(t4, text="  Summary  ")
        self.summary_box = tk.Text(t4, font=("Consolas", 12), state="disabled",
                                   bg="white", relief="flat", padx=14, pady=14)
        self.summary_box.pack(fill="both", expand=True)

        # ----- Tariff tester tab -----
        t5 = ttk.Frame(self.tabs, padding=20)
        self.tabs.add(t5, text="  Tariff Tester  ")
        ttk.Label(t5, text="Type a water usage in kL to see what it would cost:",
                  font=("Segoe UI", 11)).pack(anchor="w")
        self.test_var = tk.StringVar()
        entry = ttk.Entry(t5, textvariable=self.test_var, width=14, font=("Segoe UI", 14))
        entry.pack(anchor="w", pady=10)
        entry.bind("<KeyRelease>", lambda e: self.test_tariff())
        self.test_result = tk.Label(t5, text="", justify="left", anchor="w",
                                    font=("Consolas", 12))
        self.test_result.pack(anchor="w", pady=6)

        # ----- Help tab -----
        self.help_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.help_tab, text="  Help  ")
        help_box = tk.Text(self.help_tab, font=("Consolas", 10), bg="white",
                           relief="flat", padx=12, pady=12)
        help_box.insert("end", HELP_TEXT)
        help_box.configure(state="disabled")
        help_box.pack(fill="both", expand=True)

    def make_table(self, parent, columns, widths):
        """Create a Treeview with scrollbars."""
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        table = ttk.Treeview(frame, columns=columns, show="headings")
        for i in range(len(columns)):
            table.heading(columns[i], text=columns[i])
            table.column(columns[i], width=widths[i], anchor="w")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return table

    # ---------- actions ----------
    def browse(self):
        path = filedialog.askopenfilename(
            title="Select the water readings file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self.file_var.set(path)
            self.process()

    def process(self):
        path = self.file_var.get().strip()
        self.status_var.set("Processing...")
        self.root.update_idletasks()
        result = run_billing(path)
        if result["error"] is not None:
            self.status_var.set("Problem: " + result["error"])
            messagebox.showerror(
                "Could not process the file",
                result["error"] + "\n\nTip: make sure " + INPUT_FILE +
                " is in the same folder as this program, or click 'Browse' to find it.")
            return
        self.result = result
        self.show_results()

    def clear_table(self, table):
        for item in table.get_children():
            table.delete(item)

    def refresh_billing(self):
        """Fill the Billing table, applying the search box and category filter."""
        self.clear_table(self.billing_table)
        if self.result is None:
            return
        words = self.search_var.get().strip().lower()
        wanted = self.filter_var.get()
        records = self.result["records"]
        shown = 0
        total = 0
        for key in records:
            r = records[key]
            total = total + 1
            if wanted != "All" and r["category"] != wanted:
                continue
            text = (r["meter"] + " " + r["name"] + " " + r["area"]).lower()
            if words != "" and words not in text:
                continue
            self.billing_table.insert("", "end", iid=key, tags=(r["category"],), values=(
                r["meter"], r["name"], r["area"], r["previous"], r["current"],
                r["usage"], money(r["charge"]), r["category"]))
            shown = shown + 1
        self.count_var.set("Showing " + str(shown) + " of " + str(total) + " households")

    def show_results(self):
        result = self.result
        s = result["summary"]

        # summary cards
        self.card_accepted.set(str(s["accepted"]))
        self.card_rejected.set(str(s["rejected"]))
        self.card_usage.set(str(s["usage"]) + " kL")
        self.card_billed.set(money(s["billed"]))

        # tables
        self.refresh_billing()

        self.clear_table(self.error_table)
        for item in result["rejected"]:
            self.error_table.insert("", "end",
                                    values=(item["line"], item["text"], item["reason"]))

        self.clear_table(self.top_table)
        rank = 0
        for r in result["top_five"]:
            rank = rank + 1
            self.top_table.insert("", "end", iid=r["meter"].upper(), tags=(r["category"],),
                                  values=(rank, r["meter"], r["name"], r["area"],
                                          r["usage"], money(r["charge"])))

        self.summary_box.configure(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end", "\n" + summary_text(s))
        self.summary_box.configure(state="disabled")

        self.status_var.set("Done!  " + str(s["accepted"]) + " accepted, " +
                            str(s["rejected"]) + " rejected.  Saved " + REPORT_FILE +
                            " and " + ERROR_FILE + ".")

    def show_bill_details(self, event):
        """Pop up a bill breakdown for the household that was double-clicked."""
        table = event.widget
        selected = table.selection()
        if self.result is None or len(selected) == 0:
            return
        key = selected[0]
        records = self.result["records"]
        if key not in records:
            return
        r = records[key]
        text = (r["name"] + "  (" + r["meter"] + ", " + r["area"] + ")\n\n" +
                "Previous reading : " + str(r["previous"]) + " kL\n" +
                "Current reading  : " + str(r["current"]) + " kL\n" +
                "Water used       : " + str(r["usage"]) + " kL  (" + r["category"] + ")\n\n" +
                bill_breakdown(r["usage"]))
        messagebox.showinfo("Bill breakdown", text)

    def test_tariff(self):
        typed = self.test_var.get().strip()
        if typed == "":
            self.test_result.configure(text="", fg="black")
            return
        usage = to_whole_number(typed)
        if usage is None or usage < 0:
            self.test_result.configure(
                text="Please type a whole number of 0 or more (for example 25).", fg=self.RED)
            return
        self.test_result.configure(
            text="Usage: " + str(usage) + " kL     Category: " + classify_usage(usage) +
                 "\n\n" + bill_breakdown(usage), fg="black")

    def open_report(self):
        if self.result is not None:
            open_with_system(self.result["report_path"])
        else:
            open_with_system(os.path.join(os.path.dirname(self.file_var.get()), REPORT_FILE))

    def open_errors(self):
        if self.result is not None:
            open_with_system(self.result["error_path"])
        else:
            open_with_system(os.path.join(os.path.dirname(self.file_var.get()), ERROR_FILE))

    def open_folder(self):
        open_with_system(os.path.dirname(os.path.abspath(self.file_var.get())))


# ======================================================================
# SECTION 9: PROGRAM START
# ======================================================================
def main():
    root = tk.Tk()
    WaterBillingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

