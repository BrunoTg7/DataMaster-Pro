import re

with open('src/gui/components/task_bar.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_code = '''    def _create_task_card(self, task: dict) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            self.scroll_frame,
            width=260,
            corner_radius=8,
            fg_color="#18181b", # Escuro fixo
            border_width=1,
            border_color="#3498db" if task.get("status") in ("running", "pending") else "#27272a"
        )
        
        tool_name = task.get("tool_name", "Desconhecido")
        status = task.get("status", "pending")
        progress = task.get("progress_percent", 0)
        message = task.get("progress_message", "")
        task_id = task.get("id")

        icon_map = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "interrupted": "⚠️"
        }
        
        # Cabeçalho com Nome + Botão Fechar em Linha Horizontal
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            header_frame,
            text=f"{icon_map.get(status, '•')} {tool_name.capitalize()}",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        if status in ["pending", "running", "interrupted"]:
            ctk.CTkButton(
                header_frame,
                text="✕",
                width=24,
                height=24,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                hover_color="#e74c3c",
                text_color="#a0a0a0",
                corner_radius=4,
                command=lambda: self._cancel_task(task_id)
            ).pack(side="right")

        # Corpo/Detalhes do Card (Empilhamento Vertical Simples)
        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="x", padx=10, pady=(0, 10))

        if status == "running":
            pb = ctk.CTkProgressBar(body, height=6, progress_color="#3498db")
            pb.pack(fill="x", pady=(5, 5))
            pb.set(progress / 100)
            frame.progress_bar = pb

            pt = ctk.CTkLabel(body, text=f"{progress}% - {message}", font=ctk.CTkFont(size=10), text_color="#a0a0a0")
            pt.pack(anchor="w")
            frame.progress_text = pt

        elif status == "completed":
            ctk.CTkLabel(body, text=f"✅ Concluído ({task.get('rows_processed', 0)} linhas)", font=ctk.CTkFont(size=11), text_color="#2ecc71").pack(anchor="w", pady=5)
            
        elif status == "failed":
            ctk.CTkLabel(body, text=f"Erro: {task.get('error_message', 'Desconhecido')}", font=ctk.CTkFont(size=10), text_color="#e74c3c", wraplength=220, justify="left").pack(anchor="w", pady=5)

        elif status == "interrupted":
            ctk.CTkLabel(body, text="A execução anterior parou.", font=ctk.CTkFont(size=11), text_color="#95a5a6").pack(anchor="w", pady=(0, 5))
            ctk.CTkButton(
                body,
                text="▶ Continuar Processo",
                height=30,
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                fg_color="#d48214",
                hover_color="#b5690f",
                corner_radius=6,
                command=lambda: self._restart_task(task_id)
            ).pack(fill="x", pady=2)

        return frame

    def _update_task_card(self, frame: ctk.CTkFrame, task: dict):
        status = task.get("status")
        progress = task.get("progress_percent", 0)
        message = task.get("progress_message", "")

        if status == "running" and hasattr(frame, "progress_bar"):
            frame.progress_bar.set(progress / 100)
            frame.progress_text.configure(text=f"{progress}% - {message}")'''

updated_content = re.sub(
    r'    def _create_task_card\(self, task: dict\) -> ctk\.CTkFrame:.*?(?=    def )',
    new_code + '\n\n',
    content,
    flags=re.DOTALL
)

with open('src/gui/components/task_bar.py', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("SUBSTITUÍDA TASK_BAR")
