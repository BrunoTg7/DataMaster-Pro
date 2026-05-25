"""
GUIA DE INTEGRAÇÃO - Limites de Plano DataMaster Pro
======================================================

Este documento descreve como integrar os novos sistemas de limitação de plano
ao código existente da aplicação.

Componentes Criados:
1. plan_limits_manager.py - Validação de limites por plano
2. concurrent_limiter.py - Controle de tarefas simultâneas
3. roi_logger.py - Rastreamento de ROI e execuções
4. task_scheduler.py - Agendamento de tarefas com Cron
5. plan_enforcement_ui.py - Modals para exibir restrições
6. excel_styler.py (modificado) - Força tema + marca d'água
7. excel_theme_selector.py (modificado) - Bloqueia temas por plano

================================================================================
INTEGRAÇÃO 1: Validação de Temas (CRÍTICO)
================================================================================

Arquivo: src/gui/pages/tool_page.py
Local: Antes de chamar save_premium_excel()

ANTES:
    from src.utils.excel_styler import save_premium_excel
    
    save_premium_excel(
        df=resultado_df,
        output_path=output_file,
        theme_name=theme_selected,
        ...
    )

DEPOIS:
    from src.utils.excel_styler import save_premium_excel
    from src.core.plan_limits_manager import PlanLimitValidator
    
    # Criar validador com plano do usuário
    validator = PlanLimitValidator(self.user_data.get("plan", "gratis"))
    
    # Forçar tema correto (save_premium_excel também faz isso)
    # Mas pode validar antecipadamente:
    can_use_theme, error_msg = validator.validate_theme_access(theme_selected)
    if not can_use_theme:
        messagebox.showerror("Acesso Restrito", error_msg)
        return
    
    # Agora é seguro chamar
    save_premium_excel(
        df=resultado_df,
        output_path=output_file,
        theme_name=theme_selected,
        user_plan=self.user_data.get("plan", "gratis"),  # NOVO
        ...
    )

================================================================================
INTEGRAÇÃO 2: Validação de Tamanho de Arquivo (CRÍTICO)
================================================================================

Arquivo: src/gui/pages/tool_page.py
Local: No método _create_drop_zone() ou antes de processar arquivo

ANTES:
    def on_file_selected(file_path):
        df = pd.read_excel(file_path)
        # processar...

DEPOIS:
    from src.core.plan_limits_manager import PlanLimitValidator
    from src.gui.components.plan_enforcement_ui import show_file_size_limit
    import os
    
    def on_file_selected(file_path):
        # Validar tamanho
        validator = PlanLimitValidator(self.user_data.get("plan", "gratis"))
        file_size = os.path.getsize(file_path)
        
        is_valid, error_msg = validator.validate_file_size(file_size)
        if not is_valid:
            file_size_mb = file_size / (1024 * 1024)
            max_size_mb = validator.limits.get("max_file_size_mb", 5)
            show_file_size_limit(self, file_size_mb, max_size_mb, self.user_data.get("plan"))
            return
        
        # Agora é seguro processar
        df = pd.read_excel(file_path)
        # processar...

================================================================================
INTEGRAÇÃO 3: Controle de Execuções Simultâneas (CRÍTICO)
================================================================================

Arquivo: src/gui/pages/tool_page.py
Local: No método que inicia execução da ferramenta

ANTES:
    def on_execute_button_click():
        resultado = self.ferramenta.executar(dados)
        self.mostrar_resultado(resultado)

DEPOIS:
    from src.core.concurrent_limiter import get_task_limiter
    from src.core.plan_limits_manager import PlanLimitValidator
    from src.gui.components.plan_enforcement_ui import show_concurrent_limit
    import uuid
    
    def on_execute_button_click():
        # Validar limite de concorrência
        limiter = get_task_limiter()
        validator = PlanLimitValidator(self.user_data.get("plan", "gratis"))
        
        current_tasks = limiter.get_active_task_count(self.user_id)
        can_start, error_msg = validator.can_start_concurrent_task(current_tasks)
        
        if not can_start:
            show_concurrent_limit(
                self,
                current_tasks,
                validator.limits["max_concurrent_tasks"],
                self.user_data.get("plan")
            )
            return
        
        # Registrar tarefa
        task_id = str(uuid.uuid4())
        limiter.register_task(self.user_id, task_id, self.tool_name)
        
        try:
            start_time = time.time()
            resultado = self.ferramenta.executar(dados)
            duration = time.time() - start_time
            
            self.mostrar_resultado(resultado)
            
            # Log ROI (ver seção 4)
            # ...
            
        finally:
            limiter.complete_task(self.user_id, task_id, "completed")

================================================================================
INTEGRAÇÃO 4: Rastreamento de ROI (IMPORTANTE)
================================================================================

Arquivo: src/gui/pages/tool_page.py
Local: Após executar uma ferramenta com sucesso

ANTES:
    resultado = self.ferramenta.executar(dados)
    self.mostrar_resultado(resultado)

DEPOIS:
    from src.core.roi_logger import get_roi_manager
    import time
    
    roi_manager = get_roi_manager(storage_manager=self._storage)  # passar storage do app
    
    start_time = time.time()
    resultado = self.ferramenta.executar(dados)
    duration_seconds = time.time() - start_time
    
    # Registrar log
    roi_manager.log_execution(
        user_id=self.user_id,
        tool_name=self.tool_name,
        duration_seconds=duration_seconds,
        lines_processed=len(resultado.get("df", [])),
        file_size_bytes=os.path.getsize(uploaded_file),
        status="success"
    )
    
    # Sincronizar com cloud se online
    roi_manager.sync_to_cloud()
    
    self.mostrar_resultado(resultado)

Para adicionar ao Dashboard:
    # No dashboard_page.py:
    roi_manager = get_roi_manager()
    roi_summary = roi_manager.get_roi_summary(user_id)
    
    # Exibir métricas:
    # - total_executions
    # - total_time_saved_minutes
    # - average_roi_percentage
    # - by_tool (detalhes por ferramenta)

================================================================================
INTEGRAÇÃO 5: Agendamento de Tarefas (OPTIONAL - PRÓXIMA VERSÃO)
================================================================================

Este é um recurso mais avançado. Aqui está como usar quando implementar:

from src.core.task_scheduler import get_task_scheduler

scheduler = get_task_scheduler(storage_manager=self._storage)

# Criar tarefa agendada
task = scheduler.create_task(
    user_id=user_id,
    tool_name="consolidador",
    tool_action="consolidate",
    input_files=["/path/to/file1.xlsx", "/path/to/file2.xlsx"],
    frequency="daily",
    time_of_day="09:00"
)

# Registrar callback para executar
def execute_consolidation(task):
    print(f"Executando: {task.tool_name}")
    # Chamar a ferramenta com task.input_files

scheduler.register_task_callback("consolidador", execute_consolidation)

# Verificar tarefas devidas (chamar periodicamente)
due_tasks = scheduler.get_due_tasks(user_id)
for task in due_tasks:
    scheduler.execute_task(task)

================================================================================
INTEGRAÇÃO 6: Storage Manager - Novas Tabelas (IMPORTANTE)
================================================================================

O storage_manager.py precisa ser atualizado para suportar as novas tabelas.

Novas tabelas SQL necessárias:

1. execution_logs (para ROI):
    CREATE TABLE execution_logs (
        execution_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        duration_seconds REAL NOT NULL,
        lines_processed INTEGER NOT NULL,
        file_size_bytes INTEGER NOT NULL,
        status TEXT NOT NULL,
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

2. scheduled_tasks (para agendamento):
    CREATE TABLE scheduled_tasks (
        task_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        tool_action TEXT NOT NULL,
        input_files TEXT NOT NULL,  # JSON array
        schedule_frequency TEXT NOT NULL,
        cron_expression TEXT,
        time_of_day TEXT,
        day_of_week INTEGER,
        day_of_month INTEGER,
        enabled BOOLEAN DEFAULT 1,
        last_run TEXT,
        next_run TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        config TEXT,  # JSON
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

3. tool_configurations (para salvar configs):
    CREATE TABLE tool_configurations (
        config_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        tool_id TEXT NOT NULL,
        config_name TEXT NOT NULL,
        config_data TEXT NOT NULL,  # JSON
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

================================================================================
INTEGRAÇÃO 7: Verificação - Exemplo Completo
================================================================================

Aqui está um exemplo de como integrar tudo em um tool_page:

    from src.core.plan_limits_manager import get_plan_validator
    from src.core.concurrent_limiter import get_task_limiter
    from src.core.roi_logger import get_roi_manager
    from src.gui.components.plan_enforcement_ui import (
        show_concurrent_limit,
        show_file_size_limit
    )
    import time
    import uuid
    import os
    
    class MyToolPage(ToolPage):
        def on_execute(self):
            # 1. Validar arquivo
            validator = get_plan_validator(self.user_data.get("plan", "gratis"))
            file_size = os.path.getsize(self.uploaded_files[0])
            
            is_valid, error = validator.validate_file_size(file_size)
            if not is_valid:
                show_file_size_limit(self, file_size / (1024*1024), 5, self.user_data.get("plan"))
                return
            
            # 2. Validar concorrência
            limiter = get_task_limiter()
            current_tasks = limiter.get_active_task_count(self.user_id)
            
            can_start, error = validator.can_start_concurrent_task(current_tasks)
            if not can_start:
                show_concurrent_limit(self, current_tasks, 1, self.user_data.get("plan"))
                return
            
            # 3. Registrar tarefa
            task_id = str(uuid.uuid4())
            limiter.register_task(self.user_id, task_id, self.tool_name)
            
            try:
                # 4. Executar ferramenta
                start = time.time()
                resultado = self.ferramenta.executar(self.uploaded_files[0])
                duration = time.time() - start
                
                # 5. Registrar ROI
                roi_mgr = get_roi_manager(self._storage)
                roi_mgr.log_execution(
                    user_id=self.user_id,
                    tool_name=self.tool_name,
                    duration_seconds=duration,
                    lines_processed=len(resultado.get("df", [])),
                    file_size_bytes=file_size,
                    status="success"
                )
                
                # 6. Exibir resultado
                self.mostrar_resultado(resultado)
                
            except Exception as e:
                roi_mgr = get_roi_manager(self._storage)
                roi_mgr.log_execution(
                    user_id=self.user_id,
                    tool_name=self.tool_name,
                    duration_seconds=time.time() - start,
                    lines_processed=0,
                    file_size_bytes=file_size,
                    status="failed",
                    error_message=str(e)
                )
                raise
                
            finally:
                limiter.complete_task(self.user_id, task_id, "completed")

================================================================================
PRÓXIMOS PASSOS
================================================================================

1. Adicionar as 3 novas tabelas ao storage_manager.py
2. Integrar validações nos arquivos de ferramentas existentes
3. Testar cada integração
4. Atualizar dashboard com métricas de ROI
5. Implementar UI de agendamento (v2)

================================================================================
"""
