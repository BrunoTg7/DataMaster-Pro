#!/usr/bin/env python3
"""
Script para integrar HistoryButton automaticamente em todas as ferramentas restantes
"""

import os
import re

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
TOOLS_PATH = os.path.join(BASE_PATH, "src/gui/pages/tools")

ferramentas = [
    ('conciliador_page.py', 'conciliador', 'Conciliador Pro'),
    ('validador_links_page.py', 'validador_links', 'Validador de Links'),
    ('extrator_reviews_page.py', 'extrator_reviews', 'Extrator de Reviews'),
    ('calculadora_lucratividade_page.py', 'calculadora_lucratividade', 'Calculadora de Lucratividade'),
    ('analista_tendencias_page.py', 'analista_tendencias', 'Analista de Tendências'),
    ('data_sanitizer_page.py', 'data_sanitizer', 'Data Sanitizer'),
    ('conversor_ocr_page.py', 'conversor_ocr', 'Conversor OCR Premium'),
    ('gerador_laudos_page.py', 'gerador_laudos', 'Gerador de Laudos'),
    ('comissoes_page.py', 'comissoes', 'Comissões'),
]

def adicionar_import_history_button(content):
    """Adiciona import de HistoryButton se não existir"""
    if "from src.gui.components.history_button import HistoryButton" in content:
        return content, False
    
    # Encontrar o último import de ExecutionHelper
    match = re.search(r'(from src\.gui\.helpers\.execution_helper import ExecutionHelper)', content)
    if match:
        pos = match.end()
        content = content[:pos] + "\nfrom src.gui.components.history_button import HistoryButton" + content[pos:]
        return content, True
    
    return content, False

def adicionar_history_button_na_ui(content, tool_key, tool_name):
    """Adiciona HistoryButton na _create_content após action_btn"""
    # Padrão: encontra action_btn, depois um padrão comum após ele
    
    # Procura por: self.action_btn = ... seguido de self.status_label
    pattern = r'(self\.action_btn = self\._create_action_button\([^)]+\))\n\n(\s+)(self\.status_label = )'
    
    replacement = f'\\1\n\n\\2history_btn = HistoryButton(content, "{tool_key}", "{tool_name}")\n\\2history_btn.pack(fill="x", padx=20, pady=10)\n\n\\2\\3'
    
    new_content = re.sub(pattern, replacement, content)
    
    return new_content, content != new_content

def integrar_ferramenta(filename, tool_key, tool_name):
    """Integra HistoryButton em uma ferramenta"""
    filepath = os.path.join(TOOLS_PATH, filename)
    
    if not os.path.exists(filepath):
        print(f"❌ {filename}: Arquivo não encontrado")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Adicionar import
        content, import_added = adicionar_import_history_button(content)
        
        # 2. Adicionar botão na UI
        content, button_added = adicionar_history_button_na_ui(content, tool_key, tool_name)
        
        # Salvar se houver mudanças
        if import_added or button_added:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            status = []
            if import_added:
                status.append("import")
            if button_added:
                status.append("button")
            
            print(f"✅ {filename}: {', '.join(status)} adicionado(s)")
            return True
        else:
            print(f"⚠️  {filename}: Já possui integração ou não encontrou padrão")
            return False
            
    except Exception as e:
        print(f"❌ {filename}: Erro - {str(e)}")
        return False

def main():
    print("🔄 Integrando HistoryButton nas 9 ferramentas restantes...\n")
    
    sucesso = 0
    for filename, tool_key, tool_name in ferramentas:
        if integrar_ferramenta(filename, tool_key, tool_name):
            sucesso += 1
    
    print(f"\n✅ Total: {sucesso}/9 ferramentas integradas")
    print("\n📝 Próximos passos:")
    print("1. Verificar visualmente cada ferramenta")
    print("2. Testar a execução de cada uma")
    print("3. Validar que o histórico está sendo salvo")

if __name__ == "__main__":
    main()
