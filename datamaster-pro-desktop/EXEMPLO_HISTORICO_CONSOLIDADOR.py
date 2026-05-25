"""
EXEMPLO: Integração de Histórico no Consolidador

Este arquivo mostra exatamente como integrar o sistema de histórico
em uma ferramenta existente (neste caso, Consolidador).

USE ESTE COMO TEMPLATE PARA AS OUTRAS 12 FERRAMENTAS!
"""

# ============================================
# PASSO 1: Adicionar imports (no início do arquivo)
# ============================================

import customtkinter as ctk
import os
import sys
import threading
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.gui.pages.tool_page import ToolPage
from src.tools.consolidador.consolidador_v2 import Consolidador
from src.utils.task_helper import TaskHelper
from src.gui.helpers.execution_helper import ExecutionHelper

# ✨ NOVO: Importar HistoryButton
from src.gui.components.history_button import HistoryButton


# ============================================
# PASSO 2: Classe já tem ExecutionHelper (feito)
# ============================================

class ConsolidadorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.consolidador = Consolidador()
        self.task_helper = TaskHelper("consolidador")
        # ✨ JÁ TEM ExecutionHelper!
        self.execution = ExecutionHelper("consolidador", "Consolidador", user_id)
        super().__init__(master, "consolidador", "Consolidador", on_back, execution_tracker, user_id)
        self._check_task_state()
    
    # ... outros métodos ...


# ============================================
# PASSO 3: Adicionar botão na UI
# ============================================

def _create_content(self):
    content = ctk.CTkScrollableFrame(self, fg_color="transparent")
    content.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
    content.grid_columnconfigure(0, weight=1)

    # ... UI EXISTENTE ...
    
    self.action_btn = self._create_action_button(
        content, 
        "Consolidar Arquivos", 
        self._run_consolidate
    )

    self.status_label = ctk.CTkLabel(
        content,
        text="",
        font=ctk.CTkFont(size=12),
        text_color=config.Colors.TEXT_SECONDARY
    )
    self.status_label.pack(pady=10)
    
    # ✨ NOVO: Adicionar botão de histórico
    history_btn = HistoryButton(
        content,
        tool_name="consolidador",
        tool_display_name="Consolidador"
    )
    history_btn.pack(fill="x", padx=20, pady=10)


# ============================================
# PASSO 4: Registrar arquivos gerados
# ============================================

def _worker(self):
    """Worker que processa consolidação"""
    try:
        # Log de início
        self.execution.add_log("Iniciando consolidação...")
        
        output_path = "/path/to/consolidado.xlsx"
        
        # Processar arquivos
        for i, arquivo in enumerate(self.uploaded_files):
            # Verificar cancelamento
            if self.execution.is_cancelled():
                self.execution.add_log("Cancelado pelo usuário")
                return
            
            # Processar
            self.consolidador.processar(arquivo)
            
            # Atualizar progresso
            percent = int((i + 1) / len(self.uploaded_files) * 100)
            self.execution.update_progress(
                percent,
                f"Processado {i+1}/{len(self.uploaded_files)}"
            )
        
        # Salvar resultado
        self.consolidador.salvar_para(output_path)
        self.execution.add_log(f"Arquivo salvo: {output_path}")
        
        # ✨ REGISTRAR ARQUIVO NO HISTÓRICO
        self.execution.register_generated_file(output_path)
        
        # ✨ FINALIZAR (salva automaticamente no histórico)
        self.execution.complete({
            "arquivos_consolidados": len(self.uploaded_files),
            "arquivo_saida": os.path.basename(output_path),
            "total_linhas": sum(len(df) for df in self.dfs),
            "status": "sucesso"
        })
        
        self.execution.add_log("✅ Consolidação concluída com sucesso!")
        
    except Exception as e:
        error_msg = str(e)
        self.execution.add_log(f"❌ Erro: {error_msg}")
        # ✨ FALHAR (salva automaticamente no histórico)
        self.execution.fail(error_msg)


# ============================================
# RESUMO: O QUE MUDOU
# ============================================

"""
MUDANÇAS NECESSÁRIAS:

1. Adicionar import:
   from src.gui.components.history_button import HistoryButton

2. Em _create_content, após botão principal:
   history_btn = HistoryButton(
       content,
       tool_name="consolidador",
       tool_display_name="Consolidador"
   )
   history_btn.pack(fill="x", padx=20, pady=10)

3. Em _worker, antes de complete():
   self.execution.register_generated_file(output_path)

4. Em complete():
   Adicionar resultado_data com informações relevantes

5. Em fail():
   Já captura erro automaticamente

Pronto! Agora o Consolidador tem histórico completo ✨
"""


# ============================================
# RESULTADO FINAL
# ============================================

"""
Após integração, o usuário pode:

1. ✅ Ver histórico de todas as consolidações
2. ✅ Acessar resultados de execuções passadas
3. ✅ Baixar arquivos gerados
4. ✅ Ver estatísticas (taxa sucesso, tempo médio, etc)
5. ✅ Ver logs de cada execução
6. ✅ Saber exatamente quanto tempo levou cada execução

Histórico é salvo automaticamente em: .execution_history/consolidador/

TEMPLATE REUTILIZÁVEL PARA TODAS AS 13 FERRAMENTAS!
"""
