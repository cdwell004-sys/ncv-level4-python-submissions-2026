"""Learner Register - friendly Tkinter GUI with 7-digit student numbers and averages.

How to use (also shown in the window):
  1. Type a 7-digit student number and a name, then press Enter or click "Add learner".
  2. Type a mark (0-100) and press Enter to record it. Add as many marks as you like.
  3. Click a learner in the table to select them (rename, delete or add marks).
  4. Use the search box to find learners, or "Show ranking" to see the top average first.
Everything is saved automatically to learners.json next to this file.
"""

import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox


# ---------- logic (no GUI code, so it is easy to test) ----------

def valid_student_number(text):
    """A student number must be exactly 7 digits."""
    return len(text) == 7 and all(ch in "0123456789" for ch in text)


def parse_mark(text):
    """Return the mark as a float if it is a number from 0 to 100, else None."""
    try:
        mark = float(text)
    except ValueError:
        return None
    if 0 <= mark <= 100:
        return mark
    return None


def average_of(marks):
    """Return the average of a list of marks (0.0 for an empty list)."""
    if len(marks) == 0:
        return 0.0
    total = 0
    for m in marks:
        total += m
    return total / len(marks)


def add_learner(learners, number, name):
    """Add a learner. Returns (ok, message)."""
    number, name = number.strip(), name.strip()
    if not valid_student_number(number):
        return False, f"Student number must be exactly 7 digits (you typed {len(number)})."
    if name == "":
        return False, "Please type the learner's name."
    if number in learners:
        return False, f"Student number {number} is already used by {learners[number]['name']}."
    learners[number] = {"name": name, "marks": []}
    return True, f"{name} ({number}) was added. Now type their mark."


def add_mark(learners, number, mark_text):
    """Add a mark to an existing learner. Returns (ok, message)."""
    number = number.strip()
    if number == "":
        return False, "Click a learner in the table (or type their student number) first."
    if number not in learners:
        return False, f"No learner has student number {number}."
    mark = parse_mark(mark_text.strip())
    if mark is None:
        return False, "Please type a mark from 0 to 100."
    learners[number]["marks"].append(mark)
    avg = average_of(learners[number]["marks"])
    return True, f"Mark {mark:g} added for {learners[number]['name']}. New average: {avg:.2f}%."


def remove_last_mark(learners, number):
    """Remove the most recent mark (undo a typing mistake). Returns (ok, message)."""
    number = number.strip()
    if number not in learners:
        return False, "Click a learner in the table first."
    if len(learners[number]["marks"]) == 0:
        return False, f"{learners[number]['name']} has no marks to remove."
    removed = learners[number]["marks"].pop()
    return True, f"Removed the last mark ({removed:g}) for {learners[number]['name']}."


def rename_learner(learners, number, new_name):
    """Rename a learner. Returns (ok, message)."""
    number, new_name = number.strip(), new_name.strip()
    if number not in learners:
        return False, "Click a learner in the table first."
    if new_name == "":
        return False, "Please type the new name in the Name box."
    old = learners[number]["name"]
    learners[number]["name"] = new_name
    return True, f"{old} is now called {new_name}."


def delete_learner(learners, number):
    """Delete a learner, testing with 'in' first. Returns (ok, message)."""
    number = number.strip()
    if number in learners:
        name = learners[number]["name"]
        del learners[number]
        return True, f"{name} ({number}) was deleted."
    return False, "Click a learner in the table first."


def find_learners(learners, text):
    """Return the student numbers whose name or number contains text."""
    text = text.strip().lower()
    found = []
    for number in learners:
        if text in learners[number]["name"].lower() or text in number:
            found.append(number)
    return found


def build_ranking(learners):
    """Return (average, number, name, marks) tuples, highest average first (bubble sort)."""
    rows = []
    for number in learners:
        marks = learners[number]["marks"]
        rows.append((average_of(marks), number, learners[number]["name"], marks))
    n = len(rows)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if rows[j][0] < rows[j + 1][0]:
                rows[j], rows[j + 1] = rows[j + 1], rows[j]
                swapped = True
        if not swapped:
            break
    return rows


def class_average(learners):
    """Average of every learner's average (only learners with marks count), or None."""
    averages = []
    for number in learners:
        if len(learners[number]["marks"]) > 0:
            averages.append(average_of(learners[number]["marks"]))
    if len(averages) == 0:
        return None
    return average_of(averages)


def save_learners(learners, path):
    """Save the register to a JSON file. Returns True if it worked."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(learners, f, indent=2)
        return True
    except OSError:
        return False


def load_learners(path):
    """Load the register from a JSON file (empty register if missing or damaged)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


# ---------- GUI ----------

NAVY, BLUE, GOLD = "#1B2A41", "#005596", "#FDB515"
OK_BG, OK_FG = "#E6F4EA", "#1E8E3E"
BAD_BG, BAD_FG = "#FDECEE", "#C3092B"
INFO_BG, INFO_FG = "#EEF5FA", "#1B2A41"


class RegisterApp:
    def __init__(self, root):
        self.root = root
        self.save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learners.json")
        self.learners = load_learners(self.save_path)
        self.mode = "all"  # "all" or "ranking"

        root.title("Learner Register")
        root.geometry("1020x650")
        root.minsize(900, 600)
        root.configure(bg="#F6F8FB")
        root.protocol("WM_DELETE_WINDOW", self.on_quit)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#F6F8FB")
        style.configure("TLabel", background="#F6F8FB", font=("Segoe UI", 10))
        style.configure("TLabelframe", background="#F6F8FB")
        style.configure("TLabelframe.Label", background="#F6F8FB", foreground=BLUE, font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Primary.TButton", background=BLUE, foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#0a6cb8")])
        style.configure("Danger.TButton", foreground=BAD_FG)
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=NAVY, foreground="white")
        style.map("Treeview.Heading", background=[("active", NAVY)])

        self.build_header()
        self.build_body()
        self.build_status_bar()

        self.number_var.trace_add("write", self.update_counter)
        self.search_var.trace_add("write", lambda *_: self.refresh())
        self.update_counter()
        self.refresh()
        if self.learners:
            self.say("info", f"Welcome back! {len(self.learners)} learner(s) loaded.")
        else:
            self.say("info", "Welcome! Start by typing a student number and a name on the left.")
        self.number_entry.focus_set()

    # --- building the window ---
    def build_header(self):
        header = tk.Frame(self.root, bg=NAVY)
        header.pack(fill="x")
        tk.Label(header, text="📋  Learner Register", bg=NAVY, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=(10, 0))
        tk.Label(header, text="Add learners, record marks and see who is top of the class.",
                 bg=NAVY, fg="#cfe0f5", font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(0, 10))

    def build_body(self):
        body = ttk.Frame(self.root, padding=12)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="y", padx=(0, 12))
        right = ttk.Frame(body)
        right.pack(side="right", fill="both", expand=True)

        digits_ok = (self.root.register(lambda p: p == "" or (p.isdigit() and len(p) <= 7)), "%P")
        mark_ok = (self.root.register(lambda p: re.fullmatch(r"\d{0,3}(\.\d{0,2})?", p) is not None), "%P")

        # Step 1: learner
        box1 = ttk.LabelFrame(left, text="  Step 1 · Learner  ", padding=10)
        box1.pack(fill="x", pady=(0, 10))
        ttk.Label(box1, text="Student number (7 digits)").pack(anchor="w")
        self.number_var = tk.StringVar()
        self.number_entry = ttk.Entry(box1, textvariable=self.number_var, width=28,
                                      validate="key", validatecommand=digits_ok, font=("Segoe UI", 11))
        self.number_entry.pack(anchor="w")
        self.counter = ttk.Label(box1, text="")
        self.counter.pack(anchor="w", pady=(0, 6))
        ttk.Label(box1, text="Name").pack(anchor="w")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(box1, textvariable=self.name_var, width=28, font=("Segoe UI", 11))
        self.name_entry.pack(anchor="w", pady=(0, 8))
        ttk.Button(box1, text="➕  Add learner", style="Primary.TButton", command=self.on_add_learner).pack(fill="x")
        row = ttk.Frame(box1)
        row.pack(fill="x", pady=(6, 0))
        ttk.Button(row, text="✏  Rename", command=self.on_rename).pack(side="left", expand=True, fill="x", padx=(0, 3))
        ttk.Button(row, text="🗑  Delete", style="Danger.TButton", command=self.on_delete).pack(side="left", expand=True, fill="x", padx=(3, 0))

        # Step 2: marks
        box2 = ttk.LabelFrame(left, text="  Step 2 · Marks  ", padding=10)
        box2.pack(fill="x", pady=(0, 10))
        self.selected_label = ttk.Label(box2, text="No learner selected", foreground=BLUE, font=("Segoe UI", 10, "bold"))
        self.selected_label.pack(anchor="w", pady=(0, 4))
        ttk.Label(box2, text="Mark (0 to 100)").pack(anchor="w")
        self.mark_var = tk.StringVar()
        self.mark_entry = ttk.Entry(box2, textvariable=self.mark_var, width=28,
                                    validate="key", validatecommand=mark_ok, font=("Segoe UI", 11))
        self.mark_entry.pack(anchor="w", pady=(0, 8))
        ttk.Button(box2, text="✔  Add mark", style="Primary.TButton", command=self.on_add_mark).pack(fill="x")
        ttk.Button(box2, text="↶  Undo last mark", command=self.on_undo_mark).pack(fill="x", pady=(6, 0))

        ttk.Button(left, text="🧹  Clear the boxes", command=self.clear_boxes).pack(fill="x")
        ttk.Button(left, text="🚪  Quit", command=self.on_quit).pack(fill="x", pady=(6, 0))

        self.number_entry.bind("<Return>", lambda e: self.name_entry.focus_set())
        self.name_entry.bind("<Return>", lambda e: self.on_add_learner())
        self.mark_entry.bind("<Return>", lambda e: self.on_add_mark())

        # right side: search, table, summary
        top = ttk.Frame(right)
        top.pack(fill="x")
        ttk.Label(top, text="🔍 Search:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.search_var, width=22, font=("Segoe UI", 11)).pack(side="left", padx=6)
        ttk.Button(top, text="Show all", command=self.on_show_all).pack(side="left", padx=(0, 4))
        ttk.Button(top, text="🏆 Show ranking", style="Primary.TButton", command=self.on_ranking).pack(side="left")

        self.table_title = ttk.Label(right, text="", font=("Segoe UI", 12, "bold"), foreground=BLUE)
        self.table_title.pack(anchor="w", pady=(10, 4))

        wrap = ttk.Frame(right)
        wrap.pack(fill="both", expand=True)
        columns = ("rank", "number", "name", "marks", "average")
        self.table = ttk.Treeview(wrap, columns=columns, show="headings", selectmode="browse")
        for col, label, width, anchor in [("rank", "Rank", 55, "center"), ("number", "Student no.", 95, "center"),
                                          ("name", "Name", 150, "w"), ("marks", "Marks", 190, "w"),
                                          ("average", "Average", 80, "center")]:
            self.table.heading(col, text=label)
            self.table.column(col, width=width, anchor=anchor)
        bar = ttk.Scrollbar(wrap, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=bar.set)
        self.table.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.table.tag_configure("odd", background="#f1f5fa")
        self.table.tag_configure("top", background="#FFF3C4")
        self.table.bind("<<TreeviewSelect>>", self.on_select)

        self.summary = ttk.Label(right, text="", font=("Segoe UI", 10, "bold"))
        self.summary.pack(anchor="w", pady=(8, 0))
        ttk.Label(right, text="Tip: click a learner in the table to select them.", foreground="#5b6675").pack(anchor="w")

    def build_status_bar(self):
        self.status = tk.Label(self.root, text="", anchor="w", padx=14, pady=8, font=("Segoe UI", 10, "bold"))
        self.status.pack(fill="x", side="bottom")

    # --- small helpers ---
    def say(self, kind, message):
        colours = {"ok": (OK_BG, OK_FG, "✔  "), "bad": (BAD_BG, BAD_FG, "✘  "), "info": (INFO_BG, INFO_FG, "ℹ  ")}
        bg, fg, icon = colours[kind]
        self.status.config(text=icon + message, bg=bg, fg=fg)

    def update_counter(self, *_):
        count = len(self.number_var.get())
        if count == 7:
            self.counter.config(text="✔ 7 / 7 digits", foreground=OK_FG)
        else:
            self.counter.config(text=f"{count} / 7 digits", foreground="#5b6675")

    def save(self):
        if not save_learners(self.learners, self.save_path):
            self.say("bad", "Could not save to learners.json (is the folder read-only?).")

    def refresh(self):
        """Redraw the table for the current view (all or ranking) and search text."""
        text = self.search_var.get().strip()
        ranked = build_ranking(self.learners)
        ranks = {row[1]: i for i, row in enumerate(ranked, start=1)}
        if self.mode == "ranking":
            numbers = [row[1] for row in ranked]
            self.table_title.config(text="🏆 Ranking: highest average first")
        else:
            numbers = list(self.learners)
            self.table_title.config(text="All learners")
        if text:
            matches = find_learners(self.learners, text)
            numbers = [n for n in numbers if n in matches]
            self.table_title.config(text=self.table_title.cget("text") + f'   (search: "{text}")')

        keep = self.number_var.get()
        self.table.delete(*self.table.get_children())
        for index, number in enumerate(numbers):
            info = self.learners[number]
            marks = info["marks"]
            avg = average_of(marks)
            tags = ["odd"] if index % 2 else []
            if self.mode == "ranking" and ranks[number] == 1 and marks:
                tags.append("top")
            self.table.insert("", "end", iid=number, tags=tags, values=(
                ranks[number] if self.mode == "ranking" else "",
                number, info["name"],
                ", ".join(f"{m:g}" for m in marks) if marks else "no marks yet",
                f"{avg:.2f}%" if marks else "-"))
        if keep in self.learners and self.table.exists(keep):
            self.table.selection_set(keep)
            self.table.see(keep)

        if not self.learners:
            self.summary.config(text="No learners yet. Add your first one on the left!")
        else:
            avg = class_average(self.learners)
            self.summary.config(text=f"Learners: {len(self.learners)}    |    Class average: "
                                     + (f"{avg:.2f}%" if avg is not None else "-"))

    def after_change(self, ok, message, focus=None):
        self.say("ok" if ok else "bad", message)
        if ok:
            self.save()
            self.refresh()
        if focus is not None:
            focus.focus_set()

    # --- button handlers ---
    def on_select(self, _event):
        chosen = self.table.selection()
        if chosen:
            number = chosen[0]
            self.number_var.set(number)
            self.name_var.set(self.learners[number]["name"])
            self.selected_label.config(text=f"Selected: {self.learners[number]['name']} ({number})")

    def on_add_learner(self):
        ok, msg = add_learner(self.learners, self.number_var.get(), self.name_var.get())
        self.after_change(ok, msg, self.mark_entry if ok else self.number_entry)
        if ok:
            self.selected_label.config(text=f"Selected: {self.name_var.get().strip()} ({self.number_var.get().strip()})")
            self.table.selection_set(self.number_var.get().strip())

    def on_add_mark(self):
        ok, msg = add_mark(self.learners, self.number_var.get(), self.mark_var.get())
        if ok:
            self.mark_var.set("")
        self.after_change(ok, msg, self.mark_entry)

    def on_undo_mark(self):
        ok, msg = remove_last_mark(self.learners, self.number_var.get())
        self.after_change(ok, msg)

    def on_rename(self):
        ok, msg = rename_learner(self.learners, self.number_var.get(), self.name_var.get())
        self.after_change(ok, msg)
        if ok:
            self.selected_label.config(text=f"Selected: {self.name_var.get().strip()} ({self.number_var.get().strip()})")

    def on_delete(self):
        number = self.number_var.get().strip()
        if number in self.learners:
            name = self.learners[number]["name"]
            if not messagebox.askyesno("Delete learner",
                                       f"Delete {name} ({number}) and all their marks?\nThis cannot be undone."):
                self.say("info", "Delete cancelled.")
                return
        ok, msg = delete_learner(self.learners, number)
        if ok:
            self.clear_boxes(silent=True)
        self.after_change(ok, msg)

    def clear_boxes(self, silent=False):
        self.number_var.set("")
        self.name_var.set("")
        self.mark_var.set("")
        self.table.selection_remove(self.table.selection())
        self.selected_label.config(text="No learner selected")
        self.number_entry.focus_set()
        if not silent:
            self.say("info", "Boxes cleared. Ready for the next learner.")

    def on_show_all(self):
        self.mode = "all"
        self.search_var.set("")
        self.refresh()
        self.say("info", "Showing all learners.")

    def on_ranking(self):
        if not self.learners:
            self.say("bad", "There is nothing to rank yet. Add some learners and marks first.")
            return
        self.mode = "ranking"
        self.refresh()
        self.say("info", "Ranking shown: learners with the highest average are at the top.")

    def on_quit(self):
        if messagebox.askyesno("Goodbye?", "Close the register?\nYour learners are saved automatically."):
            self.root.destroy()


def main():
    root = tk.Tk()
    RegisterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
