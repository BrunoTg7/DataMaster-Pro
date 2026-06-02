"""
Script de Integração - Adiciona ExecutionManager a todas as 15 ferramentas

Executer: python datamaster-pro-desktop/INTEGRAR_TODAS_FERRAMENTAS.py
"""

import os
import re

# Lista das 15 ferramentas
FERRAMENTAS = [
    ("consolidador", "src/gui/pages/tools/consolidador_page.py", "Consolidador"),
    ("categorizador", "src/gui/pages/tools/categorizador_page.py", "Categorizador"),
    ("minerador", "src/gui/pages/tools/minerador_page.py", "Minerador"),
    ("orcamentos", "src/gui/pages/tools/orcamentos_page.py", "Orçamentos"),
    ("conciliador", "src/gui/pages/tools/conciliador_page.py", "Conciliador"),
    ("validador_links", "src/gui/pages/tools/validador_links_page.py", "Validador de Links"),
    ("extrator_reviews", "src/gui/pages/tools/extrator_reviews_page.py", "Extrator de Reviews"),
    ("calculadora_lucratividade", "src/gui/pages/tools/calculadora_lucratividade_page.py", "Calculadora de Lucratividade"),
    ("analista_tendencias", "src/gui/pages/tools/analista_tendencias_page.py", "Analista de Tendências"),
    ("data_sanitizer", "src/gui/pages/tools/data_sanitizer_page.py", "Data Sanitizer"),
    ("conversor_ocr", "src/gui/pages/tools/conversor_ocr_page.py", "Conversor OCR"),
    ("gerador_laudos", "src/gui/pages/tools/gerador_laudos_page.py", "Gerador de Laudos"),
    ("comissoes", "src/gui/pages/tools/comissoes_page.py", "Comissões"),
]

def check_if_integrated(file_path):
    """Verifica se já tem ExecutionHelper integrado"""
    if not os.path.exists(file_path):
        return False, "Arquivo não existe"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'ExecutionHelper' in content:
            return True, "✓ Já integrado"
        else:
            return False, "✗ Não integrado"

def generate_integration_snippet(tool_key, tool_display_name):
    """Gera o código de integração"""
    return f'''
# ============ INTEGRAÇÃO EXECUTION MANAGER ============
from src.gui.helpers.execution_helper import ExecutionHelper

# Em __init__, adicionar:
# self.execution = ExecutionHelper(
#     tool_key="{tool_key}",
#     tool_display_name="{tool_display_name}",
#     user_id=self.user_id
# )

# Exemplo de uso em método de execução:
# def _execute_action(self):
#     task_id, error = self.execution.create_task(
#         on_progress=self._on_progress,
#         on_log=self._on_log
#     )
#     if error:
#         messagebox.showerror("Erro", error)
#         return
#     
#     threading.Thread(target=self._worker, daemon=True).start()
#
# def _worker(self):
#     try:
#         self.execution.add_log("Iniciando processamento...")
#         for i in range(total):
#             if self.execution.is_cancelled():
#                 return
#             self.execution.update_progress(i, f"Processando {{i}}/{{total}}")
#             # ... fazer trabalho ...
#         self.execution.complete({{"output": "..."}})
#     except Exception as e:
#         self.execution.fail(str(e))
# ======================================================
'''

def main():
    print("=" * 60)
    print("INTEGRAÇÃO: ExecutionManager em 15 ferramentas")
    print("=" * 60)
    print()
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    for tool_key, relative_path, tool_display_name in FERRAMENTAS:
        file_path = os.path.join(base_path, relative_path)
        
        # Verificar se integrado
        is_integrated, status = check_if_integrated(file_path)
        
        print(f"{status.ljust(20)} | {tool_display_name.ljust(25)} | {tool_key}")
        
        if not is_integrated:
            print(f"  → Caminho: {relative_path}")
            print()
    
    print()
    print("=" * 60)
    print("INSTRUÇÕES DE INTEGRAÇÃO")
    print("=" * 60)
    print("""
Para cada ferramenta não integrada:

1. ABRIR o arquivo
2. ADICIONAR import:
   from src.gui.helpers.execution_helper import ExecutionHelper

3. EM __init__, ADICIONAR:
   self.execution = ExecutionHelper(
       tool_key="<tool_key>",
       tool_display_name="<tool_display_name>",
       user_id=self.user_id
   )

4. NO MÉTODO DE EXECUÇÃO, ANTES DE LANÇAR THREAD:
   task_id, error = self.execution.create_task(
       on_progress=self._on_progress_callback,
       on_log=self._on_log_callback
   )
   if error:
       messagebox.showerror("Erro", error)
       return

5. NO WORKER (em thread):
   - Chamar: self.execution.add_log("mensagem")
   - Atualizar: self.execution.update_progress(percent, "mensagem")
   - Verificar: if self.execution.is_cancelled(): return
   - Finalizar: self.execution.complete({...}) ou self.execution.fail(...)

EXEMPLO COMPLETO:
""")
    
    # Mostrar exemplo para primeira ferramenta
    tool_key, _, tool_display_name = FERRAMENTAS[0]
    print(generate_integration_snippet(tool_key, tool_display_name))
    
    print()
    print("=" * 60)
    print("STATUS DE INTEGRAÇÃO")
    print("=" * 60)
    
    total = len(FERRAMENTAS)
    integrated = sum(1 for tool_key, path, _ in FERRAMENTAS if check_if_integrated(os.path.join(base_path, path))[0])
    
    print(f"Integradas: {integrated}/{total}")
    print(f"Faltam: {total - integrated}/{total}")
    
    # Mostrar progressbar
    bar_length = 40
    filled = int((integrated / total) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"Progresso: [{bar}] {(integrated/total)*100:.0f}%")
    
    print()
    print("✓ Integração manual necessária em cada ferramenta")
    print("✓ Use este script para verificar progresso")

if __name__ == "__main__":
    main()
