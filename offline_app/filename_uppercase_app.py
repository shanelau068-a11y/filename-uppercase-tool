"""Windows offline app for uppercasing ASCII lowercase letters in file names."""

from __future__ import annotations

import re
import secrets
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


def uppercase_ascii(name: str) -> str:
    """Keep every character except ASCII lowercase letters unchanged."""
    return re.sub(r"[a-z]", lambda match: match.group(0).upper(), name)


class RenameApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("文件名大写转换（离线版）")
        self.geometry("900x590")
        self.minsize(680, 430)
        self.folder: Path | None = None
        self.items: list[tuple[Path, str]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="文件名大写转换", font=("Microsoft YaHei UI", 20, "bold")).pack(anchor=tk.W)
        ttk.Label(frame, text="离线运行：只把文件名中的 a–z 改成 A–Z，不会改动文件内容或子文件夹。", foreground="#596780").pack(anchor=tk.W, pady=(8, 18))

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X)
        ttk.Button(controls, text="选择文件夹", command=self.choose_folder).pack(side=tk.LEFT)
        self.folder_label = ttk.Label(controls, text="尚未选择文件夹")
        self.folder_label.pack(side=tk.LEFT, padx=14)

        columns = ("before", "after", "status")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=17)
        self.tree.heading("before", text="原文件名")
        self.tree.heading("after", text="改为")
        self.tree.heading("status", text="状态")
        self.tree.column("before", width=360, anchor=tk.W)
        self.tree.column("after", width=360, anchor=tk.W)
        self.tree.column("status", width=110, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=18)
        scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(relx=1, rely=0, relheight=1, anchor=tk.NE)

        bottom = ttk.Frame(frame)
        bottom.pack(fill=tk.X)
        self.status_label = ttk.Label(bottom, text="请选择需要处理的文件夹。")
        self.status_label.pack(side=tk.LEFT)
        self.rename_button = ttk.Button(bottom, text="确认改名", command=self.rename_files, state=tk.DISABLED)
        self.rename_button.pack(side=tk.RIGHT)

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="选择需要处理的文件夹")
        if not selected:
            return
        self.folder = Path(selected)
        self.items = []
        self.tree.delete(*self.tree.get_children())
        for path in self.folder.iterdir():
            if not path.is_file():
                continue
            new_name = uppercase_ascii(path.name)
            if new_name != path.name:
                self.items.append((path, new_name))
                self.tree.insert("", tk.END, values=(path.name, new_name, "待处理"))
        self.folder_label.config(text=str(self.folder))
        count = len(self.items)
        self.status_label.config(text=f"已找到 {count} 个需要改名的文件。" if count else "这个文件夹里的文件名已经全部符合要求。")
        self.rename_button.config(state=tk.NORMAL if count else tk.DISABLED)

    def rename_files(self) -> None:
        if not self.folder or not self.items:
            return
        if not messagebox.askyesno("确认改名", f"确定要改名 {len(self.items)} 个文件吗？\n\n此操作只修改文件名。"):
            return
        self.rename_button.config(state=tk.DISABLED)
        staged: list[tuple[Path, Path, str]] = []
        failures = 0
        # Temporarily rename first, so case-only changes work reliably on Windows.
        for index, (original, final_name) in enumerate(self.items):
            try:
                temporary = original.with_name(f".__rename_tmp_{secrets.token_hex(12)}")
                original.rename(temporary)
                staged.append((temporary, original, final_name))
            except OSError as error:
                failures += 1
                self.tree.item(self.tree.get_children()[index], values=(original.name, final_name, f"失败：{error}"))
        completed = 0
        for temporary, original, final_name in staged:
            index = next(i for i, (path, _) in enumerate(self.items) if path == original)
            try:
                temporary.rename(temporary.with_name(final_name))
                completed += 1
                self.tree.item(self.tree.get_children()[index], values=(original.name, final_name, "已完成"))
            except OSError as error:
                failures += 1
                # Retain the original name when the final rename cannot be completed.
                try:
                    temporary.rename(original)
                except OSError:
                    pass
                self.tree.item(self.tree.get_children()[index], values=(original.name, final_name, f"失败：{error}"))
        self.status_label.config(text=f"处理完成：{completed} 个已改名" + (f"，{failures} 个失败。" if failures else "。"))
        self.items = []


if __name__ == "__main__":
    RenameApp().mainloop()
