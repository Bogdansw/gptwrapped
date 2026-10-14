"""
gui.py - Modern Desktop GUI for GPT Wrapped.

Provides a user-friendly graphical interface built with CustomTkinter.
Allows users to attach their ChatGPT export ZIP file with a file browser dialog,
select the year, and generate/view their Wrapped report with a single click.
"""

from datetime import datetime
import os
from pathlib import Path
import sys
import threading
import webbrowser

import customtkinter as ctk
from tkinter import filedialog, messagebox

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from analyzer import analyze_export
from parser import parse_export_zip
from report import render_html_report

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class GptWrappedApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GPT Wrapped - Local ChatGPT Recap")
        self.geometry("640x470")
        self.minsize(560, 430)
        self.configure(fg_color="#141414")

        self.selected_zip_path = None
        self.parsed_export = None
        self.generated_report_path = None

        self._build_ui()

    def _build_ui(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 12))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="GPT Wrapped",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e8e8e8"
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Builds a yearly recap from your ChatGPT export. Runs offline.",
            font=ctk.CTkFont(size=12),
            text_color="#8f8f8f"
        )
        self.subtitle_label.pack(anchor="w", pady=(3, 0))

        # Attachment area
        self.attach_frame = ctk.CTkFrame(
            self,
            fg_color="#1c1c1c",
            border_width=1,
            border_color="#333333",
            corner_radius=4
        )
        self.attach_frame.pack(fill="x", padx=20, pady=10)

        self.attach_title = ctk.CTkLabel(
            self.attach_frame,
            text="ChatGPT export (ZIP file or unzipped folder)",
            font=ctk.CTkFont(size=13),
            text_color="#dcdcdc"
        )
        self.attach_title.pack(anchor="w", padx=16, pady=(14, 4))

        self.file_info_label = ctk.CTkLabel(
            self.attach_frame,
            text="No file selected.",
            font=ctk.CTkFont(size=12),
            text_color="#7a7a7a"
        )
        self.file_info_label.pack(anchor="w", padx=16, pady=(0, 12))

        # Buttons row
        self.btn_row = ctk.CTkFrame(self.attach_frame, fg_color="transparent")
        self.btn_row.pack(anchor="w", padx=16, pady=(0, 16))

        self.browse_zip_btn = ctk.CTkButton(
            self.btn_row,
            text="Browse ZIP file",
            command=self._choose_zip_file,
            width=140,
            height=30,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=12),
            corner_radius=4
        )
        self.browse_zip_btn.pack(side="left", padx=(0, 8))

        self.browse_folder_btn = ctk.CTkButton(
            self.btn_row,
            text="Browse folder",
            command=self._choose_folder,
            width=140,
            height=30,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=12),
            corner_radius=4
        )
        self.browse_folder_btn.pack(side="left")

        # Period selection
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=20, pady=(4, 8))

        self.year_label = ctk.CTkLabel(
            self.options_frame,
            text="Period:",
            font=ctk.CTkFont(size=12),
            text_color="#dcdcdc"
        )
        self.year_label.pack(side="left", padx=(2, 10))

        self.year_menu = ctk.CTkOptionMenu(
            self.options_frame,
            values=["Auto-Detect (Latest Year)"],
            width=210,
            height=30,
            corner_radius=4,
            fg_color="#2a2a2a",
            button_color="#3a3a3a",
            button_hover_color="#4a4a4a",
            font=ctk.CTkFont(size=12)
        )
        self.year_menu.pack(side="left")

        # Action button
        self.generate_btn = ctk.CTkButton(
            self,
            text="Generate report",
            command=self._start_generation,
            height=36,
            fg_color="#3568a8",
            hover_color="#2c5687",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13),
            corner_radius=4,
            state="disabled"
        )
        self.generate_btn.pack(fill="x", padx=20, pady=(12, 8))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self,
            orientation="horizontal",
            mode="indeterminate",
            height=4,
            corner_radius=2,
            progress_color="#8f8f8f"
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(2, 6))
        self.progress_bar.set(0)

        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Select your ChatGPT export to begin.",
            font=ctk.CTkFont(size=12),
            text_color="#7a7a7a",
            justify="left"
        )
        self.status_label.pack(anchor="w", padx=20, pady=(0, 8))

        # Output actions (hidden until a report exists)
        self.result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.result_frame.pack(fill="x", padx=20, pady=4)

        self.open_report_btn = ctk.CTkButton(
            self.result_frame,
            text="Open report",
            command=self._open_report,
            height=30,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=12),
            corner_radius=4
        )

        self.open_folder_btn = ctk.CTkButton(
            self.result_frame,
            text="Open output folder",
            command=self._open_output_folder,
            height=30,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            font=ctk.CTkFont(size=12),
            corner_radius=4
        )

    def _choose_zip_file(self):
        filepath = filedialog.askopenfilename(
            title="Select ChatGPT Export ZIP",
            filetypes=[("ZIP Archives", "*.zip"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        p = Path(filepath)
        self.selected_zip_path = str(p.resolve())
        size_mb = p.stat().st_size / (1024 * 1024)
        self.file_info_label.configure(
            text=f"Selected ZIP: {p.name} ({size_mb:.1f} MB)",
            text_color="#8fbf8f"
        )
        self._inspect_path(self.selected_zip_path)

    def _choose_folder(self):
        folderpath = filedialog.askdirectory(
            title="Select Unzipped ChatGPT Export Folder"
        )
        if not folderpath:
            return

        p = Path(folderpath)
        self.selected_zip_path = str(p.resolve())
        self.file_info_label.configure(
            text=f"Selected Folder: {p.name}",
            text_color="#8fbf8f"
        )
        self._inspect_path(self.selected_zip_path)

    def _inspect_path(self, target_path: str):
        self.status_label.configure(
            text="Inspecting export files...",
            text_color="#dcdcdc"
        )
        self.progress_bar.start()
        threading.Thread(target=self._inspect_zip_worker, daemon=True).start()

    def _inspect_zip_worker(self):
        try:
            self.parsed_export = parse_export_zip(self.selected_zip_path)
            self.after(0, self._on_inspect_success)
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_inspect_error(err))

    def _on_inspect_success(self):
        self.progress_bar.stop()
        self.progress_bar.set(0)

        total_chats = len(self.parsed_export.conversations)
        years = self.parsed_export.available_years

        menu_values = ["Auto-Detect (Latest Year)"]
        for y in years:
            menu_values.append(str(y))
        menu_values.append("All-Time Combined")

        self.year_menu.configure(values=menu_values)
        self.year_menu.set(menu_values[0])

        self.status_label.configure(
            text=f"Found {total_chats:,} conversation(s) across {len(years)} year(s). Ready.",
            text_color="#8fbf8f"
        )
        self.generate_btn.configure(state="normal")

    def _on_inspect_error(self, err_msg: str):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.status_label.configure(
            text=f"Could not read export: {err_msg}",
            text_color="#c96f6f"
        )
        messagebox.showerror("Error Opening Export", f"Could not read the ZIP archive:\n\n{err_msg}")

    def _start_generation(self):
        if not self.parsed_export:
            return

        self.generate_btn.configure(state="disabled")
        self.browse_zip_btn.configure(state="disabled")
        self.browse_folder_btn.configure(state="disabled")
        self.year_menu.configure(state="disabled")
        self.status_label.configure(
            text="Generating report...",
            text_color="#dcdcdc"
        )
        self.progress_bar.start()

        # Hide any previous action buttons
        self.open_report_btn.pack_forget()
        self.open_folder_btn.pack_forget()

        selected_val = self.year_menu.get()
        target_year = None
        if selected_val == "Auto-Detect (Latest Year)":
            target_year = self.parsed_export.available_years[0] if self.parsed_export.available_years else None
        elif selected_val == "All-Time Combined":
            target_year = None
        else:
            try:
                target_year = int(selected_val)
            except ValueError:
                target_year = None

        threading.Thread(target=self._generation_worker, args=(target_year,), daemon=True).start()

    def _generation_worker(self, target_year: int | None):
        try:
            stats = analyze_export(self.parsed_export.conversations, target_year)
            year_label = str(target_year) if target_year else "all_time"

            output_dir = Path("./output")
            output_dir.mkdir(parents=True, exist_ok=True)
            out_file = output_dir / f"gpt_wrapped_{year_label}.html"

            saved_path = render_html_report(stats, self.parsed_export.available_years, str(out_file))
            self.generated_report_path = saved_path

            # Launch browser automatically
            try:
                webbrowser.open(Path(saved_path).as_uri())
            except Exception:
                pass

            self.after(0, self._on_generation_success)
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_generation_error(err))

    def _on_generation_success(self):
        self.progress_bar.stop()
        self.progress_bar.set(1.0)
        self.generate_btn.configure(state="normal")
        self.browse_zip_btn.configure(state="normal")
        self.browse_folder_btn.configure(state="normal")
        self.year_menu.configure(state="normal")

        self.status_label.configure(
            text="Report written to the output folder and opened in your browser.",
            text_color="#8fbf8f"
        )

        # Show action buttons
        self.open_report_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.open_folder_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _on_generation_error(self, err_msg: str):
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.generate_btn.configure(state="normal")
        self.browse_zip_btn.configure(state="normal")
        self.browse_folder_btn.configure(state="normal")
        self.year_menu.configure(state="normal")

        self.status_label.configure(
            text=f"Failed to generate report: {err_msg}",
            text_color="#c96f6f"
        )
        messagebox.showerror("Generation Error", f"An error occurred while generating the report:\n\n{err_msg}")

    def _open_report(self):
        if self.generated_report_path and Path(self.generated_report_path).exists():
            webbrowser.open(Path(self.generated_report_path).as_uri())

    def _open_output_folder(self):
        if self.generated_report_path:
            folder = Path(self.generated_report_path).parent.resolve()
            if sys.platform == "win32":
                os.startfile(str(folder))
            else:
                webbrowser.open(folder.as_uri())


def main():
    app = GptWrappedApp()
    app.mainloop()


if __name__ == "__main__":
    main()
