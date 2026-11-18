"""Expense Tracker GUI - a themed Tkinter front end for the SQLite tracker.

Run normally:   python expense_tracker_gui.py
Run with demo:  python expense_tracker_gui.py --demo   (sample data, not saved)
"""
import math
import sqlite3
import sys
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

DB_FILE = "expenses.db"
CURRENCY = "KSh"
NAVY = "#1B2A41"
NAVY_LIGHT = "#324A5F"
BG = "#F1F4F9"
CARD = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#6B7280"
BORDER = "#E2E8F0"
ACCENT = "#2563EB"
ACCENT_DARK = "#1D4ED8"
DANGER = "#DC2626"
DANGER_DARK = "#B91C1C"
ROW_ALT = "#F8FAFC"
BAR_COLORS = ["#2563EB", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#06B6D4", "#EC4899"]

FONT = "Segoe UI"
DEFAULT_CATEGORIES = ["Food", "Transport", "Airtime", "Books", "Rent", "Health", "Other"]

class ExpenseTracker:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS expenses (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date TEXT NOT NULL,
                   category TEXT NOT NULL,
                   description TEXT,
                   amount REAL NOT NULL CHECK (amount > 0)
               )"""
        )
        self.conn.commit()

    def add(self, category, amount, description="", when=None):
        category = category.strip()
        if not category:
            raise ValueError("Category cannot be empty.")
        when = when or date.today().isoformat()
        date.fromisoformat(when)  # raises ValueError on bad dates
        amount = float(amount)
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("Amount must be a positive number.")
        cur = self.conn.execute(
            "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
            (when, category.title(), description.strip(), amount),
        )
        self.conn.commit()
        return cur.lastrowid

    def delete(self, expense_id):
        cur = self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def list_all(self):
        return self.conn.execute(
            "SELECT id, date, category, description, amount FROM expenses ORDER BY date DESC, id DESC"
        ).fetchall()

    def totals_by_category(self):
        return self.conn.execute(
            "SELECT category, SUM(amount) FROM expenses GROUP BY category ORDER BY SUM(amount) DESC"
        ).fetchall()

    def grand_total(self):
        return self.conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses").fetchone()[0]

    def month_total(self):
        prefix = date.today().strftime("%Y-%m") + "-%"
        return self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date LIKE ?", (prefix,)
        ).fetchone()[0]

    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]

class App(tk.Tk):
    def __init__(self, tracker):
        super().__init__()
        self.t = tracker
        self.title("Expense Tracker")
        self.geometry("1100x700")
        self.minsize(960, 620)
        self.configure(bg=BG)
        self._setup_styles()
        self._build_header()
        self._build_cards()
        self._build_body()
        self.refresh()


    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=30, borderwidth=0, font=(FONT, 10))
        s.configure("Treeview.Heading", background=NAVY, foreground="white",
                    font=(FONT, 10, "bold"), relief="flat", padding=(8, 7))
        s.map("Treeview.Heading", background=[("active", NAVY_LIGHT)])
        s.map("Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", TEXT)])
        s.configure("Accent.TButton", background=ACCENT, foreground="white",
                    font=(FONT, 10, "bold"), padding=(12, 9), borderwidth=0)
        s.map("Accent.TButton", background=[("active", ACCENT_DARK)])
        s.configure("Danger.TButton", background=DANGER, foreground="white",
                    font=(FONT, 10, "bold"), padding=(12, 8), borderwidth=0)
        s.map("Danger.TButton", background=[("active", DANGER_DARK)])
        s.configure("TEntry", padding=6, fieldbackground="white", bordercolor=BORDER)
        s.configure("TCombobox", padding=6, fieldbackground="white", bordercolor=BORDER)
        s.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG, borderwidth=0)

    def _build_header(self):
        bar = tk.Frame(self, bg=NAVY, height=70)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="💰  Expense Tracker", bg=NAVY, fg="white",
                 font=(FONT, 20, "bold")).pack(side="left", padx=24)
        tk.Label(bar, text=date.today().strftime("%A, %d %B %Y"), bg=NAVY, fg="#9FB3C8",
                 font=(FONT, 11)).pack(side="right", padx=24)

    def _build_cards(self):
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=(18, 8))
        self.card_vars = {}
        specs = [("total", "TOTAL SPENT", ACCENT), ("month", "THIS MONTH", "#10B981"),
                 ("count", "TRANSACTIONS", "#F59E0B"), ("top", "TOP CATEGORY", "#8B5CF6")]
        for i, (key, title, color) in enumerate(specs):
            row.columnconfigure(i, weight=1, uniform="cards")
            card = tk.Frame(row, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            tk.Frame(card, bg=color, width=5).pack(side="left", fill="y")
            inner = tk.Frame(card, bg=CARD)
            inner.pack(side="left", padx=16, pady=12, fill="x")
            tk.Label(inner, text=title, bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w")
            var = tk.StringVar()
            tk.Label(inner, textvariable=var, bg=CARD, fg=TEXT,
                     font=(FONT, 16, "bold")).pack(anchor="w", pady=(2, 0))
            self.card_vars[key] = var

    def _panel(self, parent, title):
        frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(frame, text=title, bg=CARD, fg=NAVY, font=(FONT, 12, "bold"),
                 anchor="w").pack(fill="x", padx=18, pady=(14, 6))
        return frame

    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(4, 20))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # --- left: add form ---
        form = self._panel(body, "Add Expense")
        form.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        inner = tk.Frame(form, bg=CARD)
        inner.pack(fill="x", padx=18, pady=(0, 18))

        def label(text):
            tk.Label(inner, text=text, bg=CARD, fg=MUTED, font=(FONT, 9, "bold"),
                     anchor="w").pack(fill="x", pady=(10, 3))

        label("DATE (YYYY-MM-DD)")
        self.date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(inner, textvariable=self.date_var, width=26).pack(fill="x")

        label("CATEGORY")
        self.cat_var = tk.StringVar()
        self.cat_box = ttk.Combobox(inner, textvariable=self.cat_var, values=DEFAULT_CATEGORIES)
        self.cat_box.pack(fill="x")

        label("DESCRIPTION")
        self.desc_var = tk.StringVar()
        ttk.Entry(inner, textvariable=self.desc_var).pack(fill="x")

        label(f"AMOUNT ({CURRENCY})")
        self.amt_var = tk.StringVar()
        amt = ttk.Entry(inner, textvariable=self.amt_var)
        amt.pack(fill="x")
        amt.bind("<Return>", lambda e: self.add_expense())

        ttk.Button(inner, text="+  Add Expense", style="Accent.TButton",
                   command=self.add_expense).pack(fill="x", pady=(20, 0))
        

        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)
        right.columnconfigure(0, weight=1)

        table = self._panel(right, "Recent Expenses")
        table.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        wrap = tk.Frame(table, bg=CARD)
        wrap.pack(fill="both", expand=True, padx=18, pady=(0, 6))
        cols = ("id", "date", "category", "description", "amount")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        for col, text, w, anchor in [("id", "ID", 50, "center"), ("date", "Date", 100, "w"),
                                     ("category", "Category", 110, "w"),
                                     ("description", "Description", 220, "w"),
                                     ("amount", f"Amount ({CURRENCY})", 120, "e")]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor=anchor, stretch=(col == "description"))
        self.tree.tag_configure("alt", background=ROW_ALT)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Delete>", lambda e: self.delete_selected())

        foot = tk.Frame(table, bg=CARD)
        foot.pack(fill="x", padx=18, pady=(0, 12))
        ttk.Button(foot, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_selected).pack(side="right")

        chart = self._panel(right, "Spending by Category")
        chart.grid(row=1, column=0, sticky="nsew")
        self.canvas = tk.Canvas(chart, bg=CARD, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        self.canvas.bind("<Configure>", lambda e: self.draw_chart())

    
    def add_expense(self):
        try:
            self.t.add(self.cat_var.get(), self.amt_var.get() or "x",
                       self.desc_var.get(), self.date_var.get().strip())
        except ValueError as err:
            msg = str(err)
            if "could not convert" in msg or "Invalid isoformat" in msg:
                msg = ("Please enter a valid date (YYYY-MM-DD) and a numeric amount."
                       if "isoformat" in msg else "Amount must be a number.")
            messagebox.showerror("Invalid input", msg)
            return
        self.amt_var.set("")
        self.desc_var.set("")
        self.refresh()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select an expense first.")
            return
        values = self.tree.item(sel[0], "values")
        if messagebox.askyesno("Confirm delete", f"Delete expense #{values[0]} ({values[3] or values[2]})?"):
            self.t.delete(int(values[0]))
            self.refresh()

    
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for n, (i, d, c, desc, a) in enumerate(self.t.list_all()):
            self.tree.insert("", "end", values=(i, d, c, desc or "", f"{a:,.2f}"),
                             tags=("alt",) if n % 2 else ())
        cats = self.t.totals_by_category()
        self.card_vars["total"].set(f"{CURRENCY} {self.t.grand_total():,.2f}")
        self.card_vars["month"].set(f"{CURRENCY} {self.t.month_total():,.2f}")
        self.card_vars["count"].set(str(self.t.count()))
        self.card_vars["top"].set(cats[0][0] if cats else "-")
        known = sorted(set(DEFAULT_CATEGORIES) | {c for c, _ in cats})
        self.cat_box["values"] = known
        self.draw_chart()

    def draw_chart(self):
        cv = self.canvas
        cv.delete("all")
        data = self.t.totals_by_category()
        total = self.t.grand_total()
        if not data:
            cv.create_text(cv.winfo_width() / 2, cv.winfo_height() / 2, fill=MUTED,
                           text="No expenses yet. Add one to see your breakdown.",
                           font=(FONT, 11))
            return
        width = max(cv.winfo_width(), 400)
        label_w, amt_w = 100, 190
        bar_x0, bar_x1 = label_w, width - amt_w
        row_h = 34
        for n, (cat, amt) in enumerate(data[:7]):
            y = n * row_h + 18
            pct = amt / total
            color = BAR_COLORS[n % len(BAR_COLORS)]
            cv.create_text(0, y, text=cat, anchor="w", fill=TEXT, font=(FONT, 10, "bold"))
            cv.create_rectangle(bar_x0, y - 8, bar_x1, y + 8, fill="#EEF2F7", outline="")
            cv.create_rectangle(bar_x0, y - 8, bar_x0 + (bar_x1 - bar_x0) * pct, y + 8,
                                fill=color, outline="")
            cv.create_text(width, y, text=f"{CURRENCY} {amt:,.2f}  ({pct * 100:.0f}%)",
                           anchor="e", fill=MUTED, font=(FONT, 10))


def load_demo(t):
    t.add("food", 350, "Lunch at campus", "2026-11-02")
    t.add("transport", 120, "Matatu fare", "2026-11-02")
    t.add("airtime", 100, "Data bundles", "2026-11-03")
    t.add("food", 500, "Groceries", "2026-11-05")
    t.add("books", 1200, "BCS311 textbook", "2026-11-06")
    t.add("transport", 150, "Matatu fare", "2026-11-09")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        tracker = ExpenseTracker(":memory:")
        load_demo(tracker)
    else:
        tracker = ExpenseTracker()
    App(tracker).mainloop()