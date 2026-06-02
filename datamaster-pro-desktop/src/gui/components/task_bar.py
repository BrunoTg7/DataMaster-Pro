"""
Task Bar - Overlay modal global de tarefas em execução
Mostra todas as execuções em tempo real, agrupadas por data.
"""
import customtkinter as ctk
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

log = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.tasks.task_executor import task_executor

ICON_MAP = {
    "pending": "⏳", "running": "🔄", "completed": "✅",
    "failed": "❌", "interrupted": "⚠️", "cancelled": "🚫",
}


class TaskBar(ctk.CTkFrame):
    def __init__(self, master, width=250, height=100):
        super().__init__(
            master, width=width, height=height,
            corner_radius=10, fg_color=config.Colors.CARD,
            border_width=1, border_color=config.Colors.BORDER
        )
        self._empty_label = None
        self._expanded = True
        self._task_frames: Dict[str, ctk.CTkFrame] = {}
        self._task_widgets: Dict[str, dict] = {}
        self._last_active_time = None
        self._cooldown_seconds = 30
        self._poll_after_id = None
        self._force_show_after_id = None

        self._setup_ui()
        self.place(relx=0, rely=1.0, anchor="sw", x=10, y=-50)
        self.lift()
        task_executor.on_new_task(self._on_new_task)
        task_executor.register_state_change_callback(self._on_state_change)
        self._start_polling()

    def _on_new_task(self):
        if self.winfo_exists():
            self.after(0, self._schedule_force_show)

    def _on_state_change(self, active_tasks):
        if self.winfo_exists():
            self.after(0, self._schedule_force_show)

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="#d48214", height=28, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="📋 Tarefas",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, padx=8, pady=4, sticky="w")

        today = datetime.now()
        ctk.CTkLabel(
            header, text=f"{today.day:02d}/{today.month:02d}",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color="#14d482"
        ).grid(row=0, column=1, padx=(2, 4), pady=4, sticky="e")

        self._toggle_btn = ctk.CTkButton(
            header, text="−", width=20, height=20,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent", hover_color="#40d414",
            border_width=1, border_color="#14d482",
            text_color="#14d482", corner_radius=3,
            command=self._toggle_expand
        )
        self._toggle_btn.grid(row=0, column=2, padx=(4, 6), pady=4, sticky="e")

        self.scroll_frame = ctk.CTkScrollableFrame(
            self, orientation="vertical",
            fg_color=config.Colors.CARD, width=250, height=80
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

    def _toggle_expand(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.scroll_frame.grid()
            self._toggle_btn.configure(text="−")
        else:
            self.scroll_frame.grid_remove()
            self._toggle_btn.configure(text="+")

    def _force_show(self):
        if self.winfo_exists():
            self._update_tasks()

    def _schedule_force_show(self):
        if self._force_show_after_id:
            try:
                self.after_cancel(self._force_show_after_id)
            except Exception:
                pass
        self._force_show_after_id = self.after(100, self._force_show)

    def _start_polling(self):
        if not self.winfo_exists():
            return
        try:
            has_active = self._update_tasks()
        except Exception as e:
            import traceback
            log.error("Erro ao atualizar: %s", e, exc_info=True)
            has_active = False
        finally:
            if has_active:
                self._last_active_time = datetime.now()
                interval = 1000
            elif self._last_active_time:
                elapsed = (datetime.now() - self._last_active_time).total_seconds()
                interval = 2000 if elapsed < self._cooldown_seconds else 60000
            else:
                interval = 5000
            self._poll_after_id = self.after(interval, self._start_polling)

    def _update_tasks(self):
        try:
            if not self.winfo_exists():
                return False

            all_tasks = task_executor.get_tasks()
            has_active = any(t.get("status") in ("pending", "running") for t in all_tasks)

            active = [t for t in all_tasks if t.get("status") in ("pending", "running")]
            done = [t for t in all_tasks if t.get("status") not in ("pending", "running")]
            active.sort(key=lambda t: t.get("created_at", "") or "", reverse=True)
            done.sort(key=lambda t: t.get("created_at", "") or "", reverse=True)
            tasks = active + done

            sections = self._group_by_date(tasks)
            seen = set()

            row = 0
            for key, label, items in sections:
                if not self.scroll_frame.winfo_exists():
                    return has_active
                row = self._render_section(key, label, items, row, seen)
                if row < 0:
                    return has_active

            for tid in list(self._task_frames.keys()):
                if tid not in seen:
                    frame = self._task_frames.pop(tid, None)
                    self._task_widgets.pop(tid, None)
                    if frame and frame.winfo_exists():
                        frame.destroy()

            if not tasks:
                if not self._empty_label or not self._empty_label.winfo_exists():
                    self._empty_label = ctk.CTkLabel(
                        self.scroll_frame, text="Nenhuma execução em andamento",
                        font=ctk.CTkFont(family="Inter", size=12),
                        text_color=config.Colors.TEXT_SECONDARY
                    )
                self._empty_label.grid(row=0, column=0, sticky="ew", padx=12, pady=20)
            else:
                if self._empty_label and self._empty_label.winfo_exists():
                    self._empty_label.grid_remove()

            return has_active

        except Exception as e:
            log.error("Erro em _update_tasks: %s", e, exc_info=True)
            return False

    def _render_section(self, key, label, items, row, seen):
        sk = f"_sec_{key}"
        if sk in self._task_frames:
            sf = self._task_frames[sk]
            if sf.winfo_exists():
                sf.configure(text=label)
                sf.grid(row=row, column=0, sticky="ew", padx=3, pady=(6, 0))
            else:
                self._task_frames.pop(sk, None)
                sf = self._make_section_label(label)
                self._task_frames[sk] = sf
                sf.grid(row=row, column=0, sticky="ew", padx=6, pady=(6, 0))
        else:
            sf = self._make_section_label(label)
            self._task_frames[sk] = sf
            sf.grid(row=row, column=0, sticky="ew", padx=6, pady=(6, 0))
        seen.add(sk)
        row += 1

        for t in items:
            if not self.scroll_frame.winfo_exists():
                return -1
            tid = t.get("id", "")
            seen.add(tid)

            if tid in self._task_frames:
                frame = self._task_frames[tid]
                if frame.winfo_exists():
                    self._update_card(frame, t)
                    frame.grid(row=row, column=0, sticky="ew", padx=3, pady=3)
                    row += 1
                    continue
                else:
                    self._task_frames.pop(tid, None)
                    self._task_widgets.pop(tid, None)

            try:
                frame = self._create_card(t)
                self._task_frames[tid] = frame
                frame.grid(row=row, column=0, sticky="ew", padx=3, pady=3)
                row += 1
            except Exception as e:
                log.error("Erro ao criar card: %s", e)
        return row

    def _make_section_label(self, text):
        return ctk.CTkLabel(
            self.scroll_frame, text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#a0a0a0"
        )

    def _group_by_date(self, tasks):
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        groups = {"today": [], "yesterday": [], "older": []}
        for t in tasks:
            try:
                dt = datetime.fromisoformat(t.get("created_at", "")).date()
            except Exception:
                dt = today
            if dt == today:
                groups["today"].append(t)
            elif dt == yesterday:
                groups["yesterday"].append(t)
            else:
                groups["older"].append(t)

        result = []
        if groups["today"]:
            result.append(("today", f"📍 Hoje — {len(groups['today'])}", groups["today"]))
        if groups["yesterday"]:
            result.append(("yesterday", f"📅 Ontem — {len(groups['yesterday'])}", groups["yesterday"]))
        if groups["older"]:
            result.append(("older", f"📦 Anteriores — {len(groups['older'])}", groups["older"]))
        return result

    def update_colors(self):
        self.configure(fg_color=config.Colors.CARD, border_color=config.Colors.BORDER)
        self.scroll_frame.configure(fg_color=config.Colors.CARD)

    def _create_card(self, task: dict) -> ctk.CTkFrame:
        status = task.get("status", "pending")
        task_id = task.get("id")
        tool_name = (task.get("tool_display_name") or task.get("tool_name") or "Desconhecido").capitalize()
        progress = task.get("progress_percent", 0)
        message = task.get("progress_message", "")

        frame = ctk.CTkFrame(
            self.scroll_frame, corner_radius=6,
            fg_color=config.Colors.CARD_TASK, border_width=1,
            border_color="#3498db" if status in ("running", "pending") else config.Colors.BORDER
        )
        frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        header.grid_columnconfigure(0, weight=1)

        icon = ctk.CTkLabel(
            header, text=f"{ICON_MAP.get(status, '•')} {tool_name}",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#ffffff"
        )
        icon.grid(row=0, column=0, sticky="w")

        cancel = None
        if status in ("pending", "running"):
            cancel = ctk.CTkButton(
                header, text="✕", width=18, height=18,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent", hover_color="#e74c3c",
                text_color="#a0a0a0", corner_radius=3,
                command=lambda tid=task_id: self._cancel_task(tid)
            )
            cancel.grid(row=0, column=1, sticky="e", padx=(6, 0))

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        body.grid_columnconfigure(0, weight=1)
        pb, pct, msg = self._build_body(body, task, status)

        self._task_widgets[task_id] = {
            "frame": frame, "header": header, "icon": icon, "cancel": cancel,
            "body": body, "pb": pb, "pct": pct, "msg": msg, "status": status,
        }
        return frame

    def _update_card(self, frame: ctk.CTkFrame, task: dict):
        try:
            if not frame.winfo_exists():
                return
            task_id = task.get("id", "")
            status = task.get("status", "pending")
            progress = task.get("progress_percent", 0)
            message = task.get("progress_message", "")
            tool_name = (task.get("tool_display_name") or task.get("tool_name") or "Desconhecido").capitalize()
            refs = self._task_widgets.get(task_id, {})
            prev = refs.get("status")

            frame.configure(
                border_color="#3498db" if status in ("running", "pending") else config.Colors.BORDER
            )

            icon = refs.get("icon")
            if icon and icon.winfo_exists():
                icon.configure(text=f"{ICON_MAP.get(status, '•')} {tool_name}")

            header = refs.get("header")
            cancel = refs.get("cancel")
            if header and header.winfo_exists():
                if status in ("pending", "running"):
                    if not cancel or not cancel.winfo_exists():
                        cancel = ctk.CTkButton(
                            header, text="✕", width=18, height=18,
                            font=ctk.CTkFont(size=12, weight="bold"),
                            fg_color="transparent", hover_color="#e74c3c",
                            text_color="#a0a0a0", corner_radius=3,
                            command=lambda tid=task_id: self._cancel_task(tid)
                        )
                        cancel.grid(row=0, column=1, sticky="e", padx=(6, 0))
                        if task_id in self._task_widgets:
                            self._task_widgets[task_id]["cancel"] = cancel
                    else:
                        cancel.grid()
                else:
                    if cancel and cancel.winfo_exists():
                        cancel.grid_remove()

            # Running -> Running: update widgets in place
            if status == "running" and prev == "running":
                pb = refs.get("pb")
                pct = refs.get("pct")
                msg = refs.get("msg")
                if pb and pb.winfo_exists():
                    pb.set(max(0.0, min(1.0, progress / 100)))
                if pct and pct.winfo_exists():
                    pct.configure(text=f"{progress}%")
                if msg and msg.winfo_exists():
                    msg.configure(text=message)
                if task_id in self._task_widgets:
                    self._task_widgets[task_id]["status"] = status
                return

            # Status changed: rebuild body
            body = refs.get("body")
            if body and body.winfo_exists():
                try:
                    body.destroy()
                except Exception:
                    pass
            if not frame.winfo_exists():
                if task_id in self._task_widgets:
                    self._task_widgets[task_id]["status"] = status
                return

            body = ctk.CTkFrame(frame, fg_color="transparent")
            body.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
            body.grid_columnconfigure(0, weight=1)
            try:
                pb, pct, msg = self._build_body(body, task, status)
            except Exception as e:
                log.error("Erro em _build_body: %s", e)
                pb = pct = msg = None

            if task_id in self._task_widgets:
                self._task_widgets[task_id].update({
                    "body": body, "pb": pb, "pct": pct, "msg": msg, "status": status,
                })

        except Exception as e:
            log.error("Erro ao atualizar card: %s", e, exc_info=True)

    def _build_body(self, parent, task: dict, status: str):
        """Popula o body frame com widgets conforme o status. Retorna (pb, pct, msg)."""
        pb = pct = msg = None
        progress = task.get("progress_percent", 0)
        message = task.get("progress_message", "")

        if status == "running":
            pb = ctk.CTkProgressBar(parent, height=4, progress_color="#3498db")
            pb.grid(row=0, column=0, sticky="ew", pady=(0, 3))
            pb.set(max(0.0, min(1.0, progress / 100)))

            pct = ctk.CTkLabel(parent, text=f"{progress}%",
                               font=ctk.CTkFont(size=12, weight="bold"),
                               text_color="#a0a0a0")
            pct.grid(row=1, column=0, sticky="w", pady=(0, 1))

            msg = ctk.CTkLabel(parent, text=message,
                               font=ctk.CTkFont(size=12),
                               text_color="#a0a0a0", wraplength=300, justify="left")
            msg.grid(row=2, column=0, sticky="ew", pady=(0, 2))

        elif status == "completed":
            rows = task.get("rows_processed", 0)
            ctk.CTkLabel(parent,
                         text=f"✅ {rows} linhas processadas" if rows else "✅ Concluído",
                         font=ctk.CTkFont(size=9), text_color="#2ecc71",
                         wraplength=300, justify="left"
                         ).grid(row=0, column=0, sticky="ew", pady=2)

        elif status == "failed":
            ctk.CTkLabel(parent,
                         text=f"❌ {task.get('error_message', 'Erro')}",
                         font=ctk.CTkFont(size=12), text_color="#e74c3c",
                         wraplength=300, justify="left"
                         ).grid(row=0, column=0, sticky="ew", pady=2)

        elif status == "cancelled":
            ctk.CTkLabel(parent, text="🚫 Cancelado",
                         font=ctk.CTkFont(size=9), text_color="#95a5a6"
                         ).grid(row=0, column=0, sticky="ew", pady=2)

        elif status == "interrupted":
            ctk.CTkLabel(parent, text="⚠️ Parou",
                         font=ctk.CTkFont(size=9), text_color="#95a5a6"
                         ).grid(row=0, column=0, sticky="w", pady=(0, 4))
            ctk.CTkButton(
                parent, text="▶ Continuar", height=24,
                font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                fg_color="#d48214", hover_color="#b5690f", corner_radius=4,
                command=lambda tid=task.get("id"): self._restart_task(tid)
            ).grid(row=1, column=0, sticky="ew")

        elif status == "pending":
            ctk.CTkLabel(parent, text="⏳ Aguardando...",
                         font=ctk.CTkFont(size=9), text_color="#95a5a6"
                         ).grid(row=0, column=0, sticky="ew", pady=2)

        return pb, pct, msg

    def _restart_task(self, task_id: str):
        task = task_executor.get_task(task_id)
        if task:
            name = (task.get("tool_display_name") or task.get("tool_name") or "").capitalize()
            _, err = task_executor.restart_task(task_id)
            if err:
                from tkinter import messagebox
                messagebox.showerror("Erro", err)
            else:
                from tkinter import messagebox
                messagebox.showinfo("Reiniciado", f"{name} reenviado para execução.")
        else:
            from tkinter import messagebox
            messagebox.showerror("Erro", "Tarefa não encontrada")

    def _cancel_task(self, task_id: str):
        task_executor.cancel_task(task_id)

    def destroy(self):
        if self._poll_after_id:
            try:
                self.after_cancel(self._poll_after_id)
            except Exception:
                pass
        if self._force_show_after_id:
            try:
                self.after_cancel(self._force_show_after_id)
            except Exception:
                pass
        super().destroy()


class TaskBadge(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, text="0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white", bg_color=config.Colors.PRIMARY,
            corner_radius=10, width=20, height=20, **kwargs
        )
        self._poll_after_id = None
        self._start_polling()

    def _start_polling(self):
        self._update_count()
        self._poll_after_id = self.after(3000, self._start_polling)

    def _update_count(self):
        try:
            tasks = task_executor.get_tasks()
            active = [t for t in tasks if t.get("status") in ("pending", "running")]
            self.configure(text=str(len(active)) if active else "")
        except Exception:
            pass

    def destroy(self):
        if self._poll_after_id:
            try:
                self.after_cancel(self._poll_after_id)
            except Exception:
                pass
        super().destroy()
