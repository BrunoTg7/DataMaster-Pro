"""
Task Bar - Overlay modal global de tarefas em execução
Mostra todas as execuções em tempo real, uma abaixo da outra
Integrado com GlobalExecutor para tasks rodarem independente de página

Correções:
- Bug 1 (duplicação): _get_all_tasks usava IDs do global_executor que podem mudar entre
  calls; agora usa um set de deduplicação estável por (tool_name + created_at).
- Bug 2 (trava em "execução"): _update_card_content destruía o body e recriava sempre,
  mas não atualizava a barra de progresso existente — ao destruir/recriar o frame dentro
  do loop de update causava re-layout que bloqueava o estado visual em "running".
  Corrigido: só recria body se o status mudou; senão, atualiza widgets existentes direto.
- Bug 3 (progresso não atualiza): a ProgressBar e os Labels dentro do body eram recriados
  a cada ciclo, mas o widget antigo ainda estava na tela por um frame. Agora armazenamos
  referências por task_id e atualizamos os valores diretamente sem destruir nada.
"""
import customtkinter as ctk
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.core.tasks.task_manager import task_manager
from src.core.tasks.global_executor import global_executor, TaskStatus


class TaskBar(ctk.CTkFrame):
    def __init__(self, master, width=250, height=100):
        super().__init__(
            master,
            width=width,
            height=height,
            corner_radius=10,
            fg_color=config.Colors.CARD,
            border_width=1,
            border_color=config.Colors.BORDER
        )

        self._empty_label = None
        self._expanded = True
        self._task_frames: Dict[str, ctk.CTkFrame] = {}       # task_id -> frame
        self._task_widgets: Dict[str, dict] = {}               # task_id -> {pb, pct_label, msg_label, status}
        self._last_active_time = None
        self._cooldown_seconds = 30

        self._setup_ui()

        # Posicionamento fixo no canto inferior esquerdo
        self.place(relx=0, rely=1.0, anchor="sw", x=10, y=-50)
        self.lift()

        # Registrar callback para ser notificado quando nova task iniciar
        global_executor.on_new_task(self._on_new_task)

        self._start_polling()

    def _on_new_task(self):
        """Chamado pelo GlobalExecutor quando uma nova task é criada"""
        if self.winfo_exists():
            self.after(0, self._force_show)

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="#d48214", height=28, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="📋 Tarefas",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color="#ffffff"
        ).grid(row=0, column=0, padx=8, pady=4, sticky="w")

        today = datetime.now()
        data_str = f"{today.day:02d}/{today.month:02d}"
        ctk.CTkLabel(
            header,
            text=data_str,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color="#14d482"
        ).grid(row=0, column=1, padx=(2, 4), pady=4, sticky="e")

        self._toggle_btn = ctk.CTkButton(
            header,
            text="−",
            width=20,
            height=20,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            hover_color="#40d414",
            border_width=1,
            border_color="#14d482",
            text_color="#14d482",
            corner_radius=3,
            command=self._toggle_expand
        )
        self._toggle_btn.grid(row=0, column=2, padx=(4, 6), pady=4, sticky="e")

        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            orientation="vertical",
            fg_color=config.Colors.CARD,
            width=250,
            height=80
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
        """Força atualização imediata da taskbar (chamado quando nova task inicia)"""
        if not self.winfo_exists():
            return
        self._update_tasks()

    def _start_polling(self):
        if self.winfo_exists():
            try:
                has_active = self._update_tasks()
            except Exception as e:
                import traceback
                print(f"[TaskBar] Erro ao atualizar: {e}")
                traceback.print_exc()
                has_active = False
            finally:
                if has_active:
                    self._last_active_time = datetime.now()
                    interval = 1000  # polling mais rápido enquanto há tasks ativas
                elif self._last_active_time:
                    elapsed = (datetime.now() - self._last_active_time).total_seconds()
                    if elapsed < self._cooldown_seconds:
                        interval = 2000
                    else:
                        interval = 300000
                else:
                    interval = 300000
                self.after(interval, self._start_polling)

    def _get_all_tasks(self):
        """
        Junta tasks do TaskManager (storage) com GlobalExecutor.

        CORREÇÃO BUG 1 (duplicação): o merge original usava apenas o ID do global_executor
        como chave, mas tasks persistidas no task_manager às vezes têm IDs diferentes para
        a mesma execução. Agora priorizamos tasks do global_executor (que têm o estado
        mais atualizado) e dedupliacamos pelo par (tool_name, created_at) para evitar
        duplicatas quando os sistemas usam IDs distintos para a mesma tarefa.
        """
        global_tasks = global_executor.get_tasks()
        stored = task_manager.get_tasks()

        # Índice de tasks do global_executor — estado mais atualizado
        merged: Dict[str, dict] = {t["id"]: t for t in global_tasks}

        # Chave de deduplicação: tool_name + created_at (primeiros 16 chars = minuto)
        def _dedup_key(t: dict) -> str:
            name = t.get("tool_name", "") or t.get("tool_display_name", "")
            ts = (t.get("created_at") or "")[:16]
            return f"{name}|{ts}"

        global_dedup = {_dedup_key(t) for t in global_tasks}

        for t in stored:
            tid = t["id"]
            # Já existe pelo mesmo ID → só adiciona se o global não tiver estado mais novo
            if tid in merged:
                # Preferir global_executor (mais atualizado), mas copiar campos extras
                for k, v in t.items():
                    if k not in merged[tid] or merged[tid][k] is None:
                        merged[tid][k] = v
                continue

            # Verifica se já existe pelo par (tool_name, created_at) — mesmo task, IDs diferentes
            if _dedup_key(t) in global_dedup:
                continue

            merged[tid] = t

        return list(merged.values())

    def _update_tasks(self):
        try:
            if not self.winfo_exists():
                return False

            all_tasks = self._get_all_tasks()

            status_priority = {
                "running": 0, "pending": 1, "interrupted": 2,
                "completed": 3, "failed": 4, "cancelled": 5
            }
            tasks_to_show = [
                t for t in all_tasks
                if t.get("status") in ["pending", "running", "completed", "failed", "interrupted", "cancelled"]
            ]
            tasks_to_show.sort(key=lambda t: (
                status_priority.get(t.get("status", ""), 99),
                t.get("created_at", "")[::-1]
            ))

            has_active = any(t.get("status") in ("pending", "running") for t in tasks_to_show)
            grouped = self._group_by_date(tasks_to_show)
            seen_ids = set()

            row = 0
            for section_key, section_label, section_tasks in grouped:
                if not self.scroll_frame.winfo_exists():
                    return has_active

                # Header do grupo (ex: "📍 Hoje — 3")
                section_key = f"_section_{section_key}"
                if section_key in self._task_frames:
                    sec_frame = self._task_frames[section_key]
                    if sec_frame.winfo_exists():
                        sec_frame.grid(row=row, column=0, sticky="ew", padx=3, pady=(6, 0))
                    else:
                        self._task_frames.pop(section_key, None)
                        sec_frame = ctk.CTkLabel(
                            self.scroll_frame, text=section_label,
                            font=ctk.CTkFont(size=11, weight="bold"),
                            text_color="#a0a0a0"
                        )
                        self._task_frames[section_key] = sec_frame
                        sec_frame.grid(row=row, column=0, sticky="ew", padx=6, pady=(6, 0))
                else:
                    sec_frame = ctk.CTkLabel(
                        self.scroll_frame, text=section_label,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color="#a0a0a0"
                    )
                    self._task_frames[section_key] = sec_frame
                    sec_frame.grid(row=row, column=0, sticky="ew", padx=6, pady=(6, 0))
                seen_ids.add(section_key)
                row += 1

                for task in section_tasks:
                    if not self.scroll_frame.winfo_exists():
                        return has_active
                    tid = task.get("id", "")
                    seen_ids.add(tid)

                    if tid in self._task_frames:
                        frame = self._task_frames[tid]
                        if frame.winfo_exists():
                            self._update_card_content(frame, task)
                            frame.grid(row=row, column=0, sticky="ew", padx=3, pady=3)
                            row += 1
                            continue
                        else:
                            self._task_frames.pop(tid, None)
                            self._task_widgets.pop(tid, None)

                    try:
                        frame = self._create_task_card(task)
                        self._task_frames[tid] = frame
                        frame.grid(row=row, column=0, sticky="ew", padx=3, pady=3)
                        row += 1
                    except Exception as e:
                        print(f"[TaskBar] Erro ao criar card: {e}")

            # Remover frames que não existem mais
            for tid in list(self._task_frames.keys()):
                if tid not in seen_ids:
                    frame = self._task_frames.pop(tid, None)
                    self._task_widgets.pop(tid, None)
                    if frame and frame.winfo_exists():
                        frame.destroy()

            if not tasks_to_show:
                if not self._empty_label or not self._empty_label.winfo_exists():
                    self._empty_label = ctk.CTkLabel(
                        self.scroll_frame,
                        text="Nenhuma execução em andamento",
                        font=ctk.CTkFont(family="Inter", size=12),
                        text_color=config.Colors.TEXT_SECONDARY
                    )
                self._empty_label.grid(row=0, column=0, sticky="ew", padx=12, pady=20)
            else:
                if self._empty_label and self._empty_label.winfo_exists():
                    self._empty_label.grid_remove()

            return has_active

        except Exception as e:
            import traceback
            print(f"[TaskBar] Erro em _update_tasks: {e}")
            traceback.print_exc()
            return False

    def _group_by_date(self, tasks):
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        groups = {"today": [], "yesterday": [], "older": []}
        for t in tasks:
            created = t.get("created_at", "")
            try:
                dt = datetime.fromisoformat(created).date()
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

    def _create_task_card(self, task: dict) -> ctk.CTkFrame:
        """
        Cria o card visual de uma task E armazena referências dos widgets
        dinâmicos em self._task_widgets para atualização direta posterior.
        """
        frame = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=6,
            fg_color=config.Colors.CARD_TASK,
            border_width=1,
            border_color="#3498db" if task.get("status") in ("running", "pending") else config.Colors.BORDER
        )
        frame.grid_columnconfigure(0, weight=1)

        tool_name = (task.get("tool_display_name") or task.get("tool_name") or "Desconhecido").capitalize()
        status = task.get("status", "pending")
        progress = task.get("progress_percent", 0)
        message = task.get("progress_message", "")
        task_id = task.get("id")

        icon_map = {
            "pending": "⏳", "running": "🔄", "completed": "✅",
            "failed": "❌", "interrupted": "⚠️", "cancelled": "🚫",
        }

        # ── Header ─────────────────────────────────────────────────────────
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        header_frame.grid_columnconfigure(0, weight=1)

        icon_label = ctk.CTkLabel(
            header_frame,
            text=f"{icon_map.get(status, '•')} {tool_name}",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#ffffff"
        )
        icon_label.grid(row=0, column=0, sticky="w")

        cancel_btn = None
        if status in ("pending", "running"):
            cancel_btn = ctk.CTkButton(
                header_frame,
                text="✕", width=18, height=18,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent", hover_color="#e74c3c",
                text_color="#a0a0a0", corner_radius=3,
                command=lambda tid=task_id: self._cancel_task(tid)
            )
            cancel_btn.grid(row=0, column=1, sticky="e", padx=(6, 0))

        # ── Body ───────────────────────────────────────────────────────────
        body = ctk.CTkFrame(frame, fg_color="transparent")
        body._is_body = True
        body.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        body.grid_columnconfigure(0, weight=1)

        # Widgets dinâmicos (só existem em certos estados)
        pb: Optional[ctk.CTkProgressBar] = None
        pct_label: Optional[ctk.CTkLabel] = None
        msg_label: Optional[ctk.CTkLabel] = None

        if status == "running":
            pb = ctk.CTkProgressBar(body, height=4, progress_color="#3498db")
            pb.grid(row=0, column=0, sticky="ew", pady=(0, 3))
            pb.set(progress / 100)

            pct_label = ctk.CTkLabel(body, text=f"{progress}%",
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color="#a0a0a0")
            pct_label.grid(row=1, column=0, sticky="w", pady=(0, 1))

            msg_label = ctk.CTkLabel(body, text=message,
                                     font=ctk.CTkFont(size=12),
                                     text_color="#a0a0a0", wraplength=300, justify="left")
            msg_label.grid(row=2, column=0, sticky="ew", pady=(0, 2))

        elif status == "completed":
            rows = task.get("rows_processed", 0)
            ctk.CTkLabel(body,
                         text=f"✅ {rows} linhas processadas" if rows else "✅ Concluído",
                         font=ctk.CTkFont(size=9), text_color="#2ecc71",
                         wraplength=300, justify="left"
                         ).grid(row=0, column=0, sticky="ew", pady=2)

        elif status == "failed":
            ctk.CTkLabel(body,
                         text=f"❌ {task.get('error_message', 'Erro')}",
                         font=ctk.CTkFont(size=12), text_color="#e74c3c",
                         wraplength=300, justify="left"
                         ).grid(row=0, column=0, sticky="ew", pady=2)

        elif status == "cancelled":
            ctk.CTkLabel(body, text="🚫 Cancelado",
                         font=ctk.CTkFont(size=9), text_color="#95a5a6"
                         ).grid(row=0, column=0, sticky="ew", pady=2)

        elif status == "interrupted":
            ctk.CTkLabel(body, text="⚠️ Parou",
                         font=ctk.CTkFont(size=9), text_color="#95a5a6"
                         ).grid(row=0, column=0, sticky="w", pady=(0, 4))

            ctk.CTkButton(
                body, text="▶ Continuar", height=24,
                font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                fg_color="#d48214", hover_color="#b5690f", corner_radius=4,
                command=lambda tid=task_id: self._restart_task(tid)
            ).grid(row=1, column=0, sticky="ew")

        elif status == "pending":
            ctk.CTkLabel(body, text="⏳ Aguardando...",
                         font=ctk.CTkFont(size=9), text_color="#95a5a6"
                         ).grid(row=0, column=0, sticky="ew", pady=2)

        # Guarda referências para atualização sem recriar widgets
        self._task_widgets[task_id] = {
            "frame": frame,
            "header_frame": header_frame,
            "icon_label": icon_label,
            "cancel_btn": cancel_btn,
            "body": body,
            "pb": pb,
            "pct_label": pct_label,
            "msg_label": msg_label,
            "status": status,
        }

        return frame

    def _update_card_content(self, frame: ctk.CTkFrame, task: dict):
        """
        Atualiza o conteúdo do card.

        CORREÇÃO BUG 2 + BUG 3:
        - Enquanto o status for "running", apenas atualiza os valores dos widgets
          existentes (pb.set, label.configure) SEM destruir/recriar nada.
          Isso evita o travamento visual e garante que o progresso seja refletido
          imediatamente a cada ciclo de polling.
        - Só reconstrói o body quando o status MUDA (ex: running → completed).
        """
        try:
            if not frame.winfo_exists():
                return

            task_id = task.get("id", "")
            status = task.get("status", "pending")
            progress = task.get("progress_percent", 0)
            message = task.get("progress_message", "")
            tool_name = (task.get("tool_display_name") or task.get("tool_name") or "Desconhecido").capitalize()

            icon_map = {
                "pending": "⏳", "running": "🔄", "completed": "✅",
                "failed": "❌", "interrupted": "⚠️", "cancelled": "🚫",
            }

            refs = self._task_widgets.get(task_id, {})
            prev_status = refs.get("status")

            # Atualiza borda do card
            frame.configure(
                border_color="#3498db" if status in ("running", "pending") else config.Colors.BORDER
            )

            # Atualiza ícone + nome no header
            icon_label = refs.get("icon_label")
            if icon_label and icon_label.winfo_exists():
                icon_label.configure(text=f"{icon_map.get(status, '•')} {tool_name}")

            # Gerencia botão cancelar
            header_frame = refs.get("header_frame")
            cancel_btn = refs.get("cancel_btn")
            if header_frame and header_frame.winfo_exists():
                if status in ("pending", "running"):
                    if not cancel_btn or not cancel_btn.winfo_exists():
                        cancel_btn = ctk.CTkButton(
                            header_frame,
                            text="✕", width=18, height=18,
                            font=ctk.CTkFont(size=12, weight="bold"),
                            fg_color="transparent", hover_color="#e74c3c",
                            text_color="#a0a0a0", corner_radius=3,
                            command=lambda tid=task_id: self._cancel_task(tid)
                        )
                        cancel_btn.grid(row=0, column=1, sticky="e", padx=(6, 0))
                        if task_id in self._task_widgets:
                            self._task_widgets[task_id]["cancel_btn"] = cancel_btn
                    else:
                        cancel_btn.grid()
                else:
                    if cancel_btn and cancel_btn.winfo_exists():
                        cancel_btn.grid_remove()

            # ── Caso mais importante: status ainda é "running" ──────────────
            # Atualiza progresso diretamente nos widgets existentes sem recriar nada
            if status == "running" and prev_status == "running":
                pb = refs.get("pb")
                pct_label = refs.get("pct_label")
                msg_label = refs.get("msg_label")

                if pb and pb.winfo_exists():
                    pb.set(max(0.0, min(1.0, progress / 100)))
                if pct_label and pct_label.winfo_exists():
                    pct_label.configure(text=f"{progress}%")
                if msg_label and msg_label.winfo_exists():
                    msg_label.configure(text=message)

                # Atualiza status salvo
                if task_id in self._task_widgets:
                    self._task_widgets[task_id]["status"] = status
                return

            # ── Status mudou (ou primeira vez): reconstrói body ────────────
            body = refs.get("body")
            if body and body.winfo_exists():
                try:
                    body.destroy()
                except Exception:
                    pass

            if not frame.winfo_exists():
                return

            body = ctk.CTkFrame(frame, fg_color="transparent")
            body._is_body = True
            body.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
            body.grid_columnconfigure(0, weight=1)

            pb = None
            pct_label = None
            msg_label = None

            if status == "running":
                pb = ctk.CTkProgressBar(body, height=4, progress_color="#3498db")
                pb.grid(row=0, column=0, sticky="ew", pady=(0, 3))
                pb.set(max(0.0, min(1.0, progress / 100)))

                pct_label = ctk.CTkLabel(body, text=f"{progress}%",
                                         font=ctk.CTkFont(size=12, weight="bold"),
                                         text_color="#a0a0a0")
                pct_label.grid(row=1, column=0, sticky="w", pady=(0, 1))

                msg_label = ctk.CTkLabel(body, text=message,
                                         font=ctk.CTkFont(size=12),
                                         text_color="#a0a0a0", wraplength=300, justify="left")
                msg_label.grid(row=2, column=0, sticky="ew", pady=(0, 2))

            elif status == "completed":
                rows = task.get("rows_processed", 0)
                ctk.CTkLabel(body,
                             text=f"✅ {rows} linhas processadas" if rows else "✅ Concluído",
                             font=ctk.CTkFont(size=9), text_color="#2ecc71",
                             wraplength=300, justify="left"
                             ).grid(row=0, column=0, sticky="ew", pady=2)

            elif status == "failed":
                ctk.CTkLabel(body,
                             text=f"❌ {task.get('error_message', 'Erro')}",
                             font=ctk.CTkFont(size=12), text_color="#e74c3c",
                             wraplength=300, justify="left"
                             ).grid(row=0, column=0, sticky="ew", pady=2)

            elif status == "cancelled":
                ctk.CTkLabel(body, text="🚫 Cancelado",
                             font=ctk.CTkFont(size=9), text_color="#95a5a6"
                             ).grid(row=0, column=0, sticky="ew", pady=2)

            elif status == "interrupted":
                ctk.CTkLabel(body, text="⚠️ Parou",
                             font=ctk.CTkFont(size=9), text_color="#95a5a6"
                             ).grid(row=0, column=0, sticky="w", pady=(0, 4))

                ctk.CTkButton(
                    body, text="▶ Continuar", height=24,
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    fg_color="#d48214", hover_color="#b5690f", corner_radius=4,
                    command=lambda tid=task_id: self._restart_task(tid)
                ).grid(row=1, column=0, sticky="ew")

            elif status == "pending":
                ctk.CTkLabel(body, text="⏳ Aguardando...",
                             font=ctk.CTkFont(size=9), text_color="#95a5a6"
                             ).grid(row=0, column=0, sticky="ew", pady=2)

            # Atualiza referências salvas
            if task_id in self._task_widgets:
                self._task_widgets[task_id].update({
                    "body": body,
                    "pb": pb,
                    "pct_label": pct_label,
                    "msg_label": msg_label,
                    "status": status,
                })

        except Exception as e:
            import traceback
            print(f"[TaskBar] Erro ao atualizar card: {e}")
            traceback.print_exc()

    def _restart_task(self, task_id: str):
        error = None
        new_id = None

        global_task = global_executor.get_task(task_id)
        if global_task:
            tool_name = global_task.get("tool_name")
            tool_display = global_task.get("tool_display_name", tool_name)

            stored = task_manager.get_task(task_id)
            if stored:
                new_id, error = task_manager.restart_task(task_id)
            else:
                error = "Tarefa original não encontrada"

            if not error:
                from tkinter import messagebox
                messagebox.showinfo("Reiniciado", f"{tool_display.capitalize()} foi reenviado para execução.")
        else:
            new_id, error = task_manager.restart_task(task_id)

        if error:
            from tkinter import messagebox
            messagebox.showerror("Erro", error)

    def _cancel_task(self, task_id: str):
        global_executor.cancel_task(task_id)
        task_manager.cancel_task(task_id)

    def destroy(self):
        super().destroy()


class TaskBadge(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            text="0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white",
            bg_color=config.Colors.PRIMARY,
            corner_radius=10,
            width=20,
            height=20,
            **kwargs
        )
        self._start_polling()

    def _start_polling(self):
        self._update_count()
        self.after(3000, self._start_polling)

    def _update_count(self):
        try:
            all_tasks = task_manager.get_tasks()
            global_tasks = global_executor.get_tasks()
            seen = set()
            combined = []
            for t in all_tasks + global_tasks:
                tid = t.get("id")
                if tid not in seen:
                    seen.add(tid)
                    combined.append(t)
            active = [t for t in combined if t.get("status") in ["pending", "running"]]
            count = len(active)
            self.configure(text=str(count) if count > 0 else "")
        except Exception:
            pass