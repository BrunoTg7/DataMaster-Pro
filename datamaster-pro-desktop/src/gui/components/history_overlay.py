import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.tasks.execution_history_manager import get_history_manager
from src.core.tasks.global_executor import global_executor


class HistoryOverlay(ctk.CTkFrame):
    def __init__(self, parent, tool_key: str, tool_display_name: str):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.tool_key = tool_key
        self.tool_display_name = tool_display_name
        self.history_manager = get_history_manager()
        self.current_record = None

        self.overlay = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.modal_card = ctk.CTkFrame(
            self,
            fg_color=config.Colors.CARD,
            border_width=1,
            border_color=config.Colors.BORDER,
            corner_radius=16
        )
        self.modal_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.92)
        self.modal_card.grid_columnconfigure(0, weight=1)
        self.modal_card.grid_rowconfigure(2, weight=1)

        self._create_header()
        self._create_stats()
        self._create_content()
        self._load_history()

    def _create_header(self):
        header = ctk.CTkFrame(self.modal_card, fg_color="transparent", height=50)
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=(15, 5))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=f"📊 Histórico - {self.tool_display_name}",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header,
            text="✕",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_SECONDARY,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.close
        ).grid(row=0, column=1)

    def _create_stats(self):
        self.stats_label = ctk.CTkLabel(
            self.modal_card,
            text="Carregando...",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=config.Colors.TEXT_SECONDARY,
            anchor="w"
        )
        self.stats_label.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 10))

    def _create_content(self):
        self.scroll = ctk.CTkScrollableFrame(
            self.modal_card,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.scroll.grid_columnconfigure(0, weight=1)

    def _load_history(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        history = self.history_manager.get_history_by_tool(self.tool_key, limit=50)
        stats = self.history_manager.get_tool_statistics(self.tool_key)

        if stats:
            total = stats.get("total_executions", 0)
            success_rate = stats.get("success_rate", 0)
            avg_duration = stats.get("average_duration_seconds", 0)
            self.stats_label.configure(
                text=f"Total: {total}  •  Taxa sucesso: {success_rate:.0f}%  •  Tempo médio: {avg_duration:.1f}s"
            )

        row = 0

        running = self._get_running_tasks()
        if running:
            header = ctk.CTkFrame(self.scroll, fg_color="#1e2936", corner_radius=8)
            header.grid(row=row, column=0, sticky="ew", pady=(0, 5))
            ctk.CTkLabel(
                header,
                text="🔄 EM ANDAMENTO",
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color="#ffd700"
            ).pack(anchor="w", padx=12, pady=8)
            row += 1

            for task in running:
                self._create_running_card(task, row)
                row += 1

            sep = ctk.CTkFrame(self.scroll, fg_color=config.Colors.BORDER, height=1)
            sep.grid(row=row, column=0, sticky="ew", pady=8)
            row += 1

        if history:
            section_header = ctk.CTkLabel(
                self.scroll,
                text="📋 Execuções Anteriores",
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color=config.Colors.TEXT_PRIMARY,
                anchor="w"
            )
            section_header.grid(row=row, column=0, sticky="ew", padx=5, pady=(0, 6))
            row += 1

            for record in history:
                self._create_history_card(record, row)
                row += 1
        else:
            empty = ctk.CTkFrame(self.scroll, fg_color=config.Colors.CARD, corner_radius=12)
            empty.grid(row=row, column=0, sticky="ew", pady=20)
            ctk.CTkLabel(
                empty,
                text="📭 Nenhuma execução anterior",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=config.Colors.TEXT_SECONDARY
            ).pack(pady=30)

    def _get_running_tasks(self):
        all_tasks = global_executor.get_tasks()
        return [
            t for t in all_tasks
            if t.get("tool_name") == self.tool_key
            and t.get("status") in ("pending", "running")
        ]

    def _create_running_card(self, task, row):
        card = ctk.CTkFrame(
            self.scroll,
            fg_color=config.Colors.CARD,
            corner_radius=10,
            border_width=2,
            border_color="#3498db"
        )
        card.grid(row=row, column=0, sticky="ew", pady=4)
        card.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text=f"🔄 {task.get('tool_display_name', task.get('tool_name', ''))}",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#3498db"
        ).grid(row=0, column=0, sticky="w")

        pct = task.get("progress_percent", 0)
        ctk.CTkLabel(
            hdr,
            text=f"{pct}%",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=config.Colors.TEXT_SECONDARY
        ).grid(row=0, column=1, sticky="e")

        pb = ctk.CTkProgressBar(card, height=4, progress_color="#3498db")
        pb.grid(row=1, column=0, sticky="ew", padx=12, pady=2)
        pb.set(pct / 100)

        msg = task.get("progress_message", "")
        if msg:
            ctk.CTkLabel(
                card,
                text=msg,
                font=ctk.CTkFont(family="Inter", size=10),
                text_color=config.Colors.TEXT_SECONDARY,
                wraplength=500
            ).grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

    def _create_history_card(self, record, row):
        card = ctk.CTkFrame(
            self.scroll,
            fg_color=config.Colors.CARD,
            corner_radius=10,
            border_width=1,
            border_color=config.Colors.BORDER
        )
        card.grid(row=row, column=0, sticky="ew", pady=4)
        card.grid_columnconfigure(0, weight=1)

        status_emoji = {
            "completed": "✅", "failed": "❌",
            "cancelled": "⏹️", "running": "🔄"
        }.get(record.status, "❓")
        status_color = {
            "completed": "#2ecc71", "failed": "#e74c3c",
            "cancelled": "#f39c12", "running": "#3498db"
        }.get(record.status, "#95a5a6")

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 2))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text=f"{status_emoji} {record.status.upper()}",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=status_color
        ).grid(row=0, column=0, sticky="w")

        data_str = self._format_date(record.completed_at)
        ctk.CTkLabel(
            hdr,
            text=data_str,
            font=ctk.CTkFont(family="Inter", size=10),
            text_color=config.Colors.TEXT_SECONDARY
        ).grid(row=0, column=1, sticky="e")

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=1, column=0, sticky="ew", padx=12, pady=2)
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info,
            text=f"⏱️ {record.duration_seconds:.1f}s  •  {record.status}",
            font=ctk.CTkFont(family="Inter", size=10),
            text_color=config.Colors.TEXT_SECONDARY
        ).pack(side="left", padx=2)

        if record.error_message:
            err = ctk.CTkFrame(card, fg_color="#2a1a1a", corner_radius=6)
            err.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 6))
            ctk.CTkLabel(
                err,
                text=f"❌ {record.error_message}",
                font=ctk.CTkFont(family="Inter", size=9),
                text_color="#e74c3c",
                wraplength=600
            ).pack(anchor="w", padx=8, pady=6)

        if record.result_data:
            res = ctk.CTkFrame(card, fg_color=config.Colors.BACKGROUND, corner_radius=6)
            res.grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 6))
            for key, value in record.result_data.items():
                ctk.CTkLabel(
                    res,
                    text=f"  • {key}: {str(value)[:80]}",
                    font=ctk.CTkFont(family="Inter", size=9),
                    text_color=config.Colors.TEXT_SECONDARY,
                    wraplength=600
                ).pack(anchor="w", padx=8, pady=1)

        if record.generated_files:
            fls = ctk.CTkFrame(card, fg_color=config.Colors.BACKGROUND, corner_radius=6)
            fls.grid(row=4, column=0, sticky="ew", padx=12, pady=(2, 8))
            ctk.CTkLabel(
                fls,
                text=f"📁 {len(record.generated_files)} arquivo(s)",
                font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
                text_color=config.Colors.TEXT_PRIMARY
            ).pack(anchor="w", padx=8, pady=(4, 2))
            for fi in record.generated_files[:5]:
                self._create_file_item(fls, fi)

    def _create_file_item(self, parent, file_info):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=8, pady=2)
        f.grid_columnconfigure(0, weight=1)

        # Suporta tanto dict quanto string direta (path)
        if isinstance(file_info, str):
            name = os.path.basename(file_info)
            size_str = ""
        else:
            name = file_info.get("name", os.path.basename(file_info.get("path", "arquivo")))
            size_str = f" ({self._format_size(file_info.get('size', 0))})"

        ctk.CTkLabel(
            f,
            text=f"  📄 {name}{size_str}",
            font=ctk.CTkFont(family="Inter", size=9),
            text_color="#3498db"
        ).pack(side="left", fill="x", expand=True, anchor="w")

        ctk.CTkButton(
            f,
            text="⬇",
            width=26,
            height=22,
            fg_color="transparent",
            hover_color=config.Colors.BORDER,
            text_color="#3498db",
            font=ctk.CTkFont(size=11),
            command=lambda fi=file_info: self._download_file(fi)
        ).pack(side="right")

    def _download_file(self, file_info):
        try:
            if isinstance(file_info, str):
                src = file_info
                name = os.path.basename(src)
            else:
                src = file_info.get("path", "")
                name = file_info.get("name", "arquivo")
            if not src or not os.path.exists(src):
                messagebox.showerror("Erro", "Arquivo não encontrado (pode ter expirado).")
                return
            dst = filedialog.asksaveasfilename(
                defaultextension=os.path.splitext(name)[1],
                initialfile=name,
                filetypes=[("Todos", "*.*")]
            )
            if dst:
                import shutil
                shutil.copy2(src, dst)
                messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{dst}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao baixar: {str(e)}")

    @staticmethod
    def _format_date(iso_date):
        try:
            dt = datetime.fromisoformat(iso_date)
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            return f"{dt.day} de {meses[dt.month - 1]} • {dt.strftime('%H:%M')}"
        except Exception:
            return iso_date

    @staticmethod
    def _format_size(size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"

    def close(self):
        self.destroy()
