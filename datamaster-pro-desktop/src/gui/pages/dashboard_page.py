"""
Dashboard Page - Main grid of tools
"""
import customtkinter as ctk
import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, user_data, on_logout, on_open_tool, is_online=True, sync_manager=None, execution_tracker=None, on_settings=None):
        super().__init__(master, fg_color=config.Colors.BACKGROUND)

        if not user_data:
            print("[DASHBOARD] Erro: Dados de usuário ausentes. Redirecionando...")
            if on_logout: on_logout()
            return

        self.user_data = user_data
        self.on_logout = on_logout
        self.on_open_tool = on_open_tool
        self.is_online = is_online
        self.sync_manager = sync_manager
        self.execution_tracker = execution_tracker
        self.on_settings = on_settings

        self._update_banner = None
        self._setup_ui()
        self._check_update_on_entry()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # As ferramentas expandem
        self.grid_rowconfigure(3, weight=0) # O rodapé fica no fundo

        self._create_header()
        self._create_stats_section()
        self._create_tools_grid()
        self._create_footer()

    def _create_header(self):
        header = ctk.CTkFrame(self, fg_color=config.Colors.CARD, height=70, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)

        logo = ctk.CTkLabel(
            header,
            text=config.APP_NAME,
            font=ctk.CTkFont(family="Inter", size=22, weight="bold"),
            text_color=config.Colors.PRIMARY
        )
        logo.grid(row=0, column=0, padx=30, pady=15)

        user_label = ctk.CTkLabel(
            header,
            text=f"Olá, {self.user_data.get('email', 'Usuário')}",
            font=ctk.CTkFont(family="Inter", size=15),
            text_color=config.Colors.TEXT_SECONDARY
        )
        user_label.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        plan_badge = ctk.CTkLabel(
            header,
            text=self.user_data.get("plan", "GRATIS").upper(),
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=config.Colors.BACKGROUND,
            fg_color=config.Colors.PRIMARY,
            corner_radius=12,
            width=80,
            height=28
        )
        plan_badge.grid(row=0, column=2, padx=10, pady=15)

        config_btn = ctk.CTkButton(
            header,
            text="⚙️ Config",
            width=90,
            height=32,
            fg_color="transparent",
            hover_color=config.Colors.BORDER,
            border_width=1,
            border_color=config.Colors.BORDER,
            text_color=config.Colors.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Inter", size=13),
            corner_radius=8,
            command=self.on_settings if self.on_settings else None
        )
        config_btn.grid(row=0, column=3, padx=5, pady=15)

        logout_btn2 = ctk.CTkButton(
            header,
            text="Sair",
            width=90,
            height=32,
            fg_color="transparent",
            hover_color="#EF4444",
            border_width=1,
            border_color="#EF4444",
            text_color="#EF4444",
            font=ctk.CTkFont(family="Inter", size=13),
            corner_radius=8,
            command=self.on_logout
        )
        logout_btn2.grid(row=0, column=4, padx=(5, 30), pady=15)

    def _create_stat_card(self, parent, icon, value, label, col):
        card = ctk.CTkFrame(parent, fg_color=config.Colors.CARD, corner_radius=16, border_width=1, border_color=config.Colors.BORDER)
        card.grid(row=0, column=col, padx=10, pady=0, sticky="nsew")
        
        icon_lbl = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24))
        icon_lbl.pack(pady=(15, 5))
        
        v_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(family="Inter", size=22, weight="bold"), text_color=config.Colors.PRIMARY)
        v_lbl.pack(pady=0)
        
        l_lbl = ctk.CTkLabel(card, text=label, font=ctk.CTkFont(family="Inter", size=11, weight="bold"), text_color=config.Colors.TEXT_SECONDARY)
        l_lbl.pack(pady=(0, 15))
        
        return v_lbl

    def _create_stats_section(self):
        # Container invisível para os cards respirarem
        stats_container = ctk.CTkFrame(self, fg_color="transparent")
        stats_container.grid(row=1, column=0, sticky="ew", padx=30, pady=(20, 0))
        stats_container.grid_columnconfigure((0, 1, 2), weight=1)

        # Card 1: Linhas Processadas
        self.lines_label = self._create_stat_card(stats_container, "📊", "0 / 500", "Linhas Processadas", 0)
        
        # Card 2: Tarefas Realizadas
        self.tasks_label = self._create_stat_card(stats_container, "⚡", "0", "Tarefas Realizadas", 1)
        
        # Card 3: Tempo Poupado
        self.hours_label = self._create_stat_card(stats_container, "⏱️", "0.0h", "Tempo Poupado", 2)

        # Atualizar com dados reais
        self._update_impact_stats()

    def _update_impact_stats(self):
        if not self.execution_tracker or not self.user_data:
            return
            
        user_id = self.user_data.get("id")
        user_plan = self.user_data.get("plan", "gratis")
        
        # Buscar stats (já prioriza online)
        stats = self.execution_tracker.get_user_stats(user_id)
        
        # Filtrar apenas Consolidador e Categorizador
        tools_to_count = ["consolidador", "categorizador"]
        stats_by_tool = stats.get("by_tool", {})
        current_lines = sum(
            stats_by_tool.get(tool, {}).get("lines", 0) 
            for tool in tools_to_count
        )
        current_execs = stats.get("total_executions", 0)
        
        # Limites visuais baseados no plano
        max_lines_text = " / 1200" if user_plan == "gratis" else ""
        max_execs_text = " / 15" if user_plan == "gratis" else ""
        
        self.lines_label.configure(text=f"{current_lines}{max_lines_text}")
        self.tasks_label.configure(text=f"{current_execs}{max_execs_text}")
        self.hours_label.configure(text=f"{stats.get('total_hours', 0.0):.1f}h")

    def _create_tools_grid(self):
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        content.grid(row=2, column=0, sticky="nsew", padx=40, pady=20)
        content.grid_columnconfigure((0, 1, 2), weight=1)

        title = ctk.CTkLabel(
            content,
            text="Suas Ferramentas",
            font=ctk.CTkFont(family="Inter", size=26, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 25), sticky="w")

        user_plan = self.user_data.get("plan", "gratis")
        self._cached_plan_type = config.PlanType[user_plan.upper()]
        allowed_tools = config.PLAN_LIMITS.get(
            self._cached_plan_type,
            config.PLAN_LIMITS[config.PlanType.GRATIS]
        ).get("tools", [])

        stats = self.execution_tracker.get_user_stats(self.user_data.get("id")) if self.execution_tracker else {}

        tools = list(config.TOOLS.items())
        for idx, (tool_key, tool_info) in enumerate(tools):
            row = (idx // 3) + 1
            col = idx % 3
            
            is_coming_soon = tool_info.get("status") == "coming_soon"
            
            # Se for "Em Breve" ou se estiver no plano, mostra o card normal (com lógica interna de bloqueio se necessário)
            if is_coming_soon or allowed_tools == "all" or tool_key in allowed_tools:
                self._create_tool_card(content, tool_key, tool_info, row, col, stats)
            else:
                self._create_locked_card(content, tool_key, tool_info, row, col)

    def _create_tool_card(self, parent, tool_key, tool_info, row, col, stats=None):
        card = ctk.CTkFrame(
            parent,
            fg_color=config.Colors.CARD,
            corner_radius=16,
            border_width=1,
            border_color=config.Colors.BORDER
        )
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        icon_label = ctk.CTkLabel(
            card,
            text=self._get_tool_icon(tool_key),
            font=ctk.CTkFont(size=44),
            text_color=config.Colors.PRIMARY
        )
        icon_label.pack(pady=(20, 5))

        name = ctk.CTkLabel(
            card,
            text=tool_info["name"],
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        name.pack(pady=2)

        # ---- Seção de Limites ----
        user_plan = self.user_data.get("plan", "gratis")
        tool_stats = (stats or {}).get("by_tool", {}).get(tool_key, {"execs": 0, "lines": 0})
        
        plan_limits = config.PLAN_LIMITS.get(self._cached_plan_type, config.PLAN_LIMITS[config.PlanType.GRATIS])
        tool_limit_info = plan_limits.get("tools_limit", {}).get(tool_key, {})
        
        limit_text = ""
        if user_plan == "gratis":
            max_execs = tool_limit_info.get("max_execs")
            max_per_exec = tool_limit_info.get("max_per_exec")
            
            # Só mostra linhas processadas para consolidador e categorizador
            if tool_key in ["consolidador", "categorizador"]:
                if max_execs and max_per_exec:
                    limit_text = f"📊 {tool_stats['lines']}/{max_per_exec} linhas\n⚡ {tool_stats['execs']}/{max_execs} execuções"
                elif max_execs:
                    limit_text = f"⚡ {tool_stats['execs']}/{max_execs} execuções"
                elif max_per_exec:
                    limit_text = f"📊 {tool_stats['lines']}/{max_per_exec} linhas"
            elif tool_key == "orcamentos":
                if max_execs and max_per_exec:
                    limit_text = f"📄 {tool_stats['lines']}/{max_per_exec} documentos\n⚡ {tool_stats['execs']}/{max_execs} execuções"
                elif max_execs:
                    limit_text = f"⚡ {tool_stats['execs']}/{max_execs} execuções"
                elif max_per_exec:
                    limit_text = f"📄 {tool_stats['lines']}/{max_per_exec} documentos"
            elif tool_key == "minerador":
                if max_execs and max_per_exec:
                    limit_text = f"🔗 {tool_stats['lines']}/{max_per_exec} links\n⚡ {tool_stats['execs']}/{max_execs} execuções"
                else:
                    limit_text = f"⚡ {tool_stats['execs']}/{max_execs} execuções"
            elif tool_key == "conciliador":
                limit_text = f"⚡ {tool_stats['execs']}/{max_execs} execuções"
        else:
            limit_text = "✨ Uso Ilimitado (PRO)"

        usage_lbl = ctk.CTkLabel(
            card,
            text=limit_text,
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=config.Colors.PRIMARY if user_plan == "gratis" else "#10B981"
        )
        usage_lbl.pack(pady=5)
        # --------------------------

        desc = ctk.CTkLabel(
            card,
            text=tool_info["description"],
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=config.Colors.TEXT_SECONDARY,
            wraplength=180
        )
        desc.pack(pady=(5, 10), padx=15)

        # ---- Lógica de "Em Breve" (Bloqueio) ----
        is_coming_soon = tool_info.get("status") == "coming_soon"
        
        if is_coming_soon:
            # Lista de funcionalidades futuras
            features_frame = ctk.CTkFrame(card, fg_color="transparent")
            features_frame.pack(pady=5, padx=20, fill="x")
            
            for feature in tool_info.get("features", []):
                f_lbl = ctk.CTkLabel(
                    features_frame,
                    text=f"• {feature}",
                    font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
                    text_color=config.Colors.PRIMARY,
                    anchor="w",
                    justify="left"
                )
                f_lbl.pack(fill="x")
            
            btn_text = "Em Breve"
            btn_state = "disabled"
            btn_fg = config.Colors.BORDER
            btn_text_color = config.Colors.TEXT_SECONDARY
        else:
            btn_text = "Abrir"
            btn_state = "normal"
            btn_fg = config.Colors.PRIMARY
            btn_text_color = "white"

        btn = ctk.CTkButton(
            card,
            text=btn_text,
            state=btn_state,
            width=120,
            height=35,
            fg_color=btn_fg,
            hover_color=config.Colors.PRIMARY_HOVER,
            text_color=btn_text_color,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            corner_radius=8,
            command=lambda tk=tool_key: self._open_tool(tk) if not is_coming_soon else None
        )
        btn.pack(pady=(15, 20))

    def _create_locked_card(self, parent, tool_key, tool_info, row, col):
        card = ctk.CTkFrame(
            parent, 
            fg_color=config.Colors.CARD, 
            corner_radius=16,
            border_width=1,
            border_color=config.Colors.BORDER
        )
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        icon_label = ctk.CTkLabel(
            card,
            text="🔒",
            font=ctk.CTkFont(size=44),
            text_color=config.Colors.TEXT_SECONDARY
        )
        icon_label.pack(pady=(25, 10))

        name = ctk.CTkLabel(
            card,
            text=tool_info["name"],
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=config.Colors.TEXT_SECONDARY
        )
        name.pack(pady=5)

        desc = ctk.CTkLabel(
            card,
            text="Upgrade para Pro",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=config.Colors.ALERT
        )
        desc.pack(pady=(5, 25))

    def _get_tool_icon(self, tool_key):
        icons = {
            "consolidador": "📊",
            "categorizador": "🏷️",
            "orcamentos": "📄",
            "minerador": "🌐",
            "conciliador": "✅",
            "validador_links": "🔗",
            "extrator_reviews": "⭐",
            "calculadora_lucratividade": "💰",
            "analista_tendencias": "📈",
            "data_sanitizer": "🧹",
            "conversor_ocr": "📷",
            "gerador_laudos": "⚖️",
            "comissoes": "💵"
        }
        return icons.get(tool_key, "🔧")

    def _open_tool(self, tool_key):
        self.on_open_tool(tool_key)

    def _create_footer(self):
        footer = ctk.CTkFrame(self, fg_color=config.Colors.CARD, height=40, corner_radius=0)
        footer.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_columnconfigure(3, weight=1)

        status_label = ctk.CTkLabel(
            footer,
            text="Conexão:",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        status_label.grid(row=0, column=0, padx=(20, 5), pady=10)

        self.status_led = ctk.CTkLabel(
            footer,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color="#10B981" if self.is_online else "#EF4444"
        )
        self.status_led.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self.connection_label = ctk.CTkLabel(
            footer,
            text="Online" if self.is_online else "Offline",
            font=ctk.CTkFont(size=11),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.connection_label.grid(row=0, column=2, padx=5, pady=10, sticky="w")

        if self.sync_manager:
            stats = self.sync_manager.get_queue_stats()
            pending = stats.get("pending", 0)
            sync_text = f"Sync: {pending} pendentes" if pending > 0 else "✓ Sincronizado"
            sync_color = config.Colors.ALERT if pending > 0 else "#10B981"
        else:
            sync_text = ""
            sync_color = config.Colors.TEXT_SECONDARY

        self.sync_label = ctk.CTkLabel(
            footer,
            text=sync_text,
            font=ctk.CTkFont(size=11),
            text_color=sync_color
        )
        self.sync_label.grid(row=0, column=3, padx=10, pady=10)

        self.version_footer_label = ctk.CTkLabel(
            footer,
            text=f"v{config.APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color=config.Colors.TEXT_SECONDARY
        )
        self.version_footer_label.grid(row=0, column=4, padx=20, pady=10)

    def update_connection_status(self, is_online: bool):
        """Atualiza o status de conexão"""
        self.is_online = is_online
        self.status_led.configure(text_color="#10B981" if is_online else "#EF4444")
        self.connection_label.configure(text="Online" if is_online else "Offline")

        stats = self.sync_manager.get_queue_stats() if self.sync_manager else {}
        pending = stats.get("pending", 0)

        if pending > 0:
            self.sync_label.configure(text=f"Sync: {pending} pendentes", text_color=config.Colors.ALERT)
        else:
            self.sync_label.configure(text="✓ Sincronizado", text_color="#10B981")

        if self.sync_manager and is_online and pending > 0:
            def async_sync():
                result = self.sync_manager.sync_now()
                if result.get("success"):
                    self.after(0, lambda: self.sync_label.configure(text="✓ Sincronizado", text_color="#10B981"))
                elif result.get("offline"):
                    self.after(0, lambda: self.sync_label.configure(text=f"Sync: {pending} pendentes", text_color=config.Colors.ALERT))
            threading.Thread(target=async_sync, daemon=True).start()

    # ==================== SISTEMA DE ATUALIZAÇÃO ====================
    def _check_update_on_entry(self):
        """Observa o cache global de updates sem fazer novas requisições"""
        if config.SESSION_BANNER_SHOWN:
            return
            
        self._poll_attempts = 0
        
        def poll_cache():
            # Se o resultado já chegou no cache e há update disponível
            if config.LAST_UPDATE_DATA and config.LAST_UPDATE_DATA.get("available"):
                config.SESSION_BANNER_SHOWN = True
                self.after(0, lambda: self._show_update_banner(config.LAST_UPDATE_DATA))
                return
            
            # Se ainda não chegou, tenta de novo por alguns segundos
            self._poll_attempts += 1
            if self._poll_attempts < 10: # Tenta por 5 segundos (500ms * 10)
                self.after(500, poll_cache)
        
        poll_cache()

    def _show_update_banner(self, update_info):
        """Mostra um banner elegante de atualização em tons de laranja/âmbar"""
        if self._update_banner:
            try: self._update_banner.destroy()
            except: pass

        # Cores Premium Orange
        bg_color = "#2a1b0a"      # Fundo âmbar escuro
        border_color = "#f59e0b"  # Borda âmbar vibrante
        text_color = "#fbbf24"    # Texto âmbar claro
        btn_color = "#f59e0b"     # Botão laranja

        banner = ctk.CTkFrame(
            self,
            fg_color=bg_color,
            border_width=2,
            border_color=border_color,
            corner_radius=12,
            height=60
        )
        # POSICIONAMENTO FLUTUANTE (MODAL)
        # Aparece no topo, centralizado horizontalmente, por cima de tudo
        banner.place(relx=0.5, y=90, anchor="n", relwidth=0.9)
        
        banner.grid_columnconfigure(1, weight=1)
        banner.lift() # Garante que fique no topo da pilha visual
        self._update_banner = banner

        # Ícone e Título
        ctk.CTkLabel(
            banner,
            text=f"✨ Nova versão {update_info.get('version', '')} disponível!",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=text_color
        ).grid(row=0, column=0, padx=(25, 15), pady=15, sticky="w")

        # Changelog resumido
        ctk.CTkLabel(
            banner,
            text=f"➜ {update_info.get('changelog', '')[:70]}...",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color="#d4d4d8"
        ).grid(row=0, column=1, padx=5, pady=15, sticky="w")

        # Botão de Ação
        ctk.CTkButton(
            banner,
            text="ATUALIZAR AGORA",
            width=150,
            height=34,
            fg_color=btn_color,
            hover_color="#d97706",
            text_color="#000000",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            corner_radius=8,
            command=lambda: self._start_silent_update(update_info)
        ).grid(row=0, column=2, padx=10, pady=15)

        # Botão Fechar
        ctk.CTkButton(
            banner,
            text="✕",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color="#451a03",
            text_color=text_color,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: self._dismiss_banner()
        ).grid(row=0, column=3, padx=(5, 20), pady=15)

        # Auto-dismiss após 30 segundos
        self.after(30000, self._dismiss_banner)

    def _dismiss_banner(self):
        if self._update_banner:
            try:
                self._update_banner.destroy()
            except:
                pass
            self._update_banner = None

    def _start_silent_update(self, update_info):
        """Baixa e instala a atualização silenciosamente"""
        download_url = update_info.get("download_url", "")
        if not download_url:
            return

        # Transforma o banner em barra de progresso
        if self._update_banner:
            try:
                self._update_banner.destroy()
            except:
                pass

        # POSICIONAMENTO FLUTUANTE (MODAL)
        progress_banner.place(relx=0.5, y=100, anchor="n", relwidth=0.9)
        
        progress_banner.grid_columnconfigure(1, weight=1)
        progress_banner.lift()
        self._update_banner = progress_banner

        status_label = ctk.CTkLabel(
            progress_banner,
            text="📥 Baixando atualização...",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=config.Colors.PRIMARY
        )
        status_label.grid(row=0, column=0, padx=(20, 10), pady=12, sticky="w")

        progress_bar = ctk.CTkProgressBar(
            progress_banner,
            progress_color=config.Colors.PRIMARY,
            fg_color=config.Colors.BORDER,
            height=12,
            corner_radius=6
        )
        progress_bar.grid(row=0, column=1, padx=10, pady=12, sticky="ew")
        progress_bar.set(0)

        percent_label = ctk.CTkLabel(
            progress_banner,
            text="0%",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=config.Colors.TEXT_PRIMARY
        )
        percent_label.grid(row=0, column=2, padx=(5, 20), pady=12)

        def on_progress(percent):
            self.after(0, lambda p=percent: [
                progress_bar.set(p / 100),
                percent_label.configure(text=f"{p}%")
            ])

        def on_complete(file_path, error):
            if error:
                self.after(0, lambda: status_label.configure(text=f"❌ Erro: {error[:50]}", text_color="#EF4444"))
                self.after(5000, self._dismiss_banner)
                return

            self.after(0, lambda: self._prompt_install(file_path, status_label))

        from src.core.update.update_checker import UpdateChecker
        checker = UpdateChecker(config.APP_VERSION)
        checker.download_and_install(download_url, on_progress=on_progress, on_complete=on_complete)

    def _prompt_install(self, file_path, status_label):
        """Pergunta ao usuário se deseja instalar agora"""
        import subprocess
        status_label.configure(text="✅ Download concluído! Instalando...", text_color="#22c55e")

        try:
            # Executa o instalador silenciosamente e fecha o app
            subprocess.Popen([file_path], shell=True)
            self.after(2000, lambda: self.master.destroy())
        except Exception as e:
            status_label.configure(text=f"❌ Erro ao iniciar instalador: {str(e)[:40]}", text_color="#EF4444")
            self.after(5000, self._dismiss_banner)