from __future__ import annotations

import os
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .core import generate_deck, split_words
from .validator import OUTPUT_DIR, INPUT_FILE, ensure_directories


class VocabApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Anki Vocab Generator | Daily Vocabulary")
        self.root.geometry("980x760")
        self.root.minsize(860, 680)

        ensure_directories()
        self._build_style()
        self._build_ui()

    def _build_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Hero.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("SubTitle.TLabel", font=("Segoe UI", 10))
        style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Body.TLabel", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", font=("Segoe UI", 9), foreground="#64748b")

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=20)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Anki Vocab Generator", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Daily workflow: paste words, generate one deck, and study the same day.", style="Hero.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(
            header,
            text="Nhập từ mới, chương trình sẽ tự tra nghĩa, tạo audio và file .apkg riêng cho từng lần chạy.",
            style="SubTitle.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(6, 0))

        body = ttk.Frame(self.root, padding=(20, 0, 20, 20))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(3, weight=1)

        entry_card = ttk.Frame(body, padding=18, style="Card.TFrame")
        entry_card.grid(row=0, column=0, sticky="ew")
        entry_card.columnconfigure(0, weight=1)

        ttk.Label(entry_card, text="Step 1. Dán các từ mới, mỗi dòng một từ", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(entry_card, text="Bạn có thể dán trực tiếp, hoặc nạp từ file input/words.csv cho danh sách ngày hôm đó.", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.words_text = ScrolledText(entry_card, height=9, font=("Segoe UI", 11), wrap="word")
        self.words_text.grid(row=2, column=0, sticky="ew", pady=(10, 12))
        self.words_text.insert("1.0", "run\nwalk")

        button_row = ttk.Frame(entry_card)
        button_row.grid(row=3, column=0, sticky="ew")
        button_row.columnconfigure(4, weight=1)

        ttk.Button(button_row, text="Load CSV", command=self._load_csv).grid(row=0, column=0, sticky="w")
        ttk.Button(button_row, text="Sample Day", command=self._load_sample_day).grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.generate_button = ttk.Button(button_row, text="Generate Today's Deck", style="Action.TButton", command=self._start_generation)
        self.generate_button.grid(row=0, column=0, sticky="w")
        self.generate_button.grid_configure(column=2, padx=(10, 0))

        ttk.Button(button_row, text="Open Output", command=self._open_output).grid(row=0, column=3, padx=(10, 0))

        self.clear_after_generate = tk.BooleanVar(value=True)
        ttk.Checkbutton(button_row, text="Clear input after generate", variable=self.clear_after_generate).grid(row=0, column=4, sticky="w", padx=(14, 0))

        self.status_var = tk.StringVar(value=f"Output folder: {OUTPUT_DIR}")
        ttk.Label(body, textvariable=self.status_var, style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=(14, 8))

        recent_card = ttk.Frame(body, padding=18, style="Card.TFrame")
        recent_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        recent_card.columnconfigure(1, weight=1)
        ttk.Label(recent_card, text="Step 2. Kết quả gần đây", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        self.recent_var = tk.StringVar(value="Chưa có file nào được tạo trong phiên này.")
        ttk.Label(recent_card, textvariable=self.recent_var, style="Muted.TLabel", wraplength=760, justify="left").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.output_listbox = tk.Listbox(recent_card, height=4, font=("Consolas", 10), exportselection=False)
        self.output_listbox.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 8))
        self.output_listbox.bind("<Double-1>", lambda _event: self._open_selected_output())
        ttk.Button(recent_card, text="Open Selected", command=self._open_selected_output).grid(row=3, column=0, sticky="w")
        ttk.Button(recent_card, text="Refresh List", command=self._refresh_recent_output).grid(row=3, column=1, sticky="w", padx=(10, 0))

        log_card = ttk.Frame(body, padding=18, style="Card.TFrame")
        log_card.grid(row=3, column=0, sticky="nsew")
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(0, weight=1)

        ttk.Label(log_card, text="Log", style="Body.TLabel").grid(row=0, column=0, sticky="w")
        self.log_box = ScrolledText(log_card, height=14, font=("Consolas", 10), state="disabled")
        self.log_box.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        self._log("Ready.")
        self._refresh_recent_output()

    def _log(self, message: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _refresh_recent_output(self) -> None:
        apkg_files = sorted(OUTPUT_DIR.glob("*.apkg"), key=lambda path: path.stat().st_mtime, reverse=True)
        self.output_listbox.delete(0, "end")
        for apkg_file in apkg_files:
            self.output_listbox.insert("end", apkg_file.name)
        if apkg_files:
            latest = apkg_files[0]
            self.recent_var.set(f"Latest deck: {latest.name}")
        else:
            self.recent_var.set(f"Chưa có file .apkg nào trong {OUTPUT_DIR}.")

    def _open_selected_output(self) -> None:
        selection = self.output_listbox.curselection()
        if not selection:
            messagebox.showinfo("Open Output", "Hãy chọn một file output trước.")
            return

        output_path = OUTPUT_DIR / self.output_listbox.get(selection[0])
        if not output_path.exists():
            self._refresh_recent_output()
            messagebox.showwarning("Missing file", "File output không còn tồn tại.")
            return

        try:
            os.startfile(output_path)
        except Exception as exc:
            messagebox.showerror("Open Output", str(exc))

    def _set_busy(self, busy: bool) -> None:
        self.generate_button.configure(state="disabled" if busy else "normal")

    def _open_output(self) -> None:
        output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(output_dir)
        except Exception as exc:
            messagebox.showerror("Open Output", str(exc))

    def _load_csv(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select words.csv",
            initialdir=str(INPUT_FILE.parent),
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            content = _read_text_file(Path(file_path))
        except OSError as exc:
            messagebox.showerror("Load CSV", str(exc))
            return

        words = split_words(content)
        if not words:
            messagebox.showwarning("Empty file", "File không có từ hợp lệ.")
            return

        self.words_text.delete("1.0", "end")
        self.words_text.insert("1.0", "\n".join(words))
        self.status_var.set(f"Loaded {len(words)} word(s) from {Path(file_path).name}")
        self._log(f"Loaded CSV: {file_path}")

    def _load_sample_day(self) -> None:
        sample = "run\nwalk\nblueprint"
        self.words_text.delete("1.0", "end")
        self.words_text.insert("1.0", sample)
        self.status_var.set("Loaded sample daily list.")
        self._log("Loaded sample day words.")

    def _start_generation(self) -> None:
        words = split_words(self.words_text.get("1.0", "end"))
        if not words:
            messagebox.showwarning("Missing input", "Hãy nhập ít nhất một từ.")
            return

        self._set_busy(True)
        self.status_var.set("Generating... please wait.")
        self._log(f"Start: {len(words)} word(s)")

        def worker() -> None:
            try:
                output_path, entries = generate_deck(words, log=self._thread_log)
                self.root.after(0, lambda: self._generation_done(output_path, entries))
            except Exception as exc:
                self.root.after(0, lambda error=exc: self._generation_failed(error))

        threading.Thread(target=worker, daemon=True).start()

    def _thread_log(self, message: str) -> None:
        self.root.after(0, lambda text=message: self._log(text))

    def _generation_done(self, output_path, entries) -> None:
        self._set_busy(False)
        self.status_var.set(f"Done: {output_path}")
        self._log(f"Done. Created {len(entries)} card set(s).")
        self._refresh_recent_output()
        if self.clear_after_generate.get():
            self.words_text.delete("1.0", "end")
        messagebox.showinfo("Success", f"Generated: {output_path}")

    def _generation_failed(self, exc: Exception) -> None:
        self._set_busy(False)
        self.status_var.set("Generation failed.")
        self._log(f"Error: {exc}")
        messagebox.showerror("Generation failed", str(exc))


def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1258", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def run_app() -> None:
    root = tk.Tk()
    VocabApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
