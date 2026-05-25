#!/usr/bin/env python3
"""
Script para adicionar register_generated_file() e complete() nas ferramentas
Procura pelos padrões de task_helper.complete e task_helper.fail para inserir chamadas de histórico
"""

import os
import re

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
TOOLS_PATH = os.path.join(BASE_PATH, "src/gui/pages/tools")

ferramentas = [
    {
        'file': 'conciliador_page.py',
        'tool_key': 'conciliador',
        'search_pattern': r'(self\.task_helper\.complete\(output_path,)',
        'register_call': 'self.execution.register_generated_file(output_path)',
        'complete_call': 'self.execution.complete({"linhas": lines})'
    },
    {
        'file': 'validador_links_page.py',
        'tool_key': 'validador_links',
        'search_pattern': r'(self\.task_helper\.complete\()',
        'register_call': 'self.execution.register_generated_file(output_path)',
        'complete_call': 'self.execution.complete({"links": total})'
    },
    {
        'file': 'extrator_reviews_page.py',
        'tool_key': 'extrator_reviews',
        'search_pattern': r'(self\.task_helper\.complete\()',
        'register_call': 'self.execution.register_generated_file(output_path)',
        'complete_call': 'self.execution.complete({"reviews": count})'
    },
    {
        'file': 'data_sanitizer_page.py',
        'tool_key': 'data_sanitizer',
        'search_pattern': r'(self\.task_helper\.complete\()',
        'register_call': 'self.execution.register_generated_file(output_path)',
        'complete_call': 'self.execution.complete({"registros": rows})'
    },
    {
        'file': 'conversor_ocr_page.py',
        'tool_key': 'conversor_ocr',
        'search_pattern': r'(self\.task_helper\.complete\()',
        'register_call': 'self.execution.register_generated_file(output_path)',
        'complete_call': 'self.execution.complete({"arquivos": count})'
    },
]

def adicionar_historico_em_ferramentas(filename, tool_key, search_pattern, register_call, complete_call):
    """Adiciona chamadas de histórico em uma ferramenta"""
    filepath = os.path.join(TOOLS_PATH, filename)
    
    if not os.path.exists(filepath):
        print(f"❌ {filename}: Arquivo não encontrado")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se já tem execute.complete - se tiver, não é necessário adicionar
        if "self.execution.complete(" in content:
            print(f"⚠️  {filename}: Já possui chamadas de histórico")
            return False
        
        # Procurar por task_helper.complete e adicionar chamadas antes dele
        if re.search(r'self\.task_helper\.complete\(', content):
            # Padrão: if result.get("success"): ... task_helper.complete
            # Adicionar ANTES de task_helper.complete
            
            pattern = r'(\s+)(self\.task_helper\.complete\()'
            replacement = f'\\1{register_call}\n\\1{complete_call}\n\\1\\2'
            
            new_content = re.sub(pattern, replacement, content, count=1)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ {filename}: register + complete adicionados")
                return True
            else:
                print(f"⚠️  {filename}: Não conseguiu adicionar automaticamente")
                return False
        else:
            print(f"⚠️  {filename}: task_helper.complete não encontrado")
            return False
            
    except Exception as e:
        print(f"❌ {filename}: Erro - {str(e)}")
        return False

def main():
    print("🔄 Adicionando register_generated_file() e complete() em ferramentas...\n")
    
    sucesso = 0
    for tool in ferramentas:
        if adicionar_historico_em_ferramentas(
            tool['file'],
            tool['tool_key'],
            tool['search_pattern'],
            tool['register_call'],
            tool['complete_call']
        ):
            sucesso += 1
    
    print(f"\n✅ Total: {sucesso}/{len(ferramentas)} ferramentas com histórico completo")

if __name__ == "__main__":
    main()
