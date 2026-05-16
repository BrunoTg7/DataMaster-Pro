#!/usr/bin/env python3
"""
Auditoria Profissional das Ferramentas - DataMaster Pro
Verifica se as 5 ferramentas estão prontas para produção
"""

from pathlib import Path
import ast
import sys

tools = ['consolidador', 'categorizador', 'orcamentos', 'minerador', 'conciliador']
tools_dir = Path('src/tools')

print('='*80)
print('AUDITORIA PROFISSIONAL DAS FERRAMENTAS - DataMaster Pro')
print('='*80)
print()

# Definir critérios profissionais
CRITERIOS = {
    'docstring': 'Documentação (docstring)',
    'error_handling': 'Tratamento de erros (try/except)',
    'logging': 'Sistema de logging',
    'type_hints': 'Type hints (tipagem)',
    'classes': 'Classes bem estruturadas',
    'functions': 'Funções implementadas',
    'imports': 'Imports completos'
}

results = {}
total_score = 0

for tool_name in tools:
    tool_path = tools_dir / tool_name
    main_file = tool_path / f'{tool_name}.py'
    
    if not main_file.exists():
        print(f'[ERROR] {tool_name}: Arquivo nao encontrado')
        continue
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Análise AST
    try:
        tree = ast.parse(content)
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        imports = len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
    except SyntaxError as e:
        print(f'[ERROR] {tool_name}: Syntax error - {e}')
        continue
    
    # Verificar critérios
    checks = {
        'docstring': ast.get_docstring(tree) is not None,
        'error_handling': 'except' in content,
        'logging': 'logging' in content or 'logger' in content,
        'type_hints': '->' in content or ': str' in content or ': int' in content or ': list' in content,
        'classes': classes >= 1,
        'functions': functions >= 2,
        'imports': imports >= 3
    }
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    percentage = (passed / total) * 100
    
    results[tool_name] = {
        'checks': checks,
        'passed': passed,
        'total': total,
        'percentage': percentage,
        'classes': classes,
        'functions': functions,
        'lines': len(content.split('\n')),
        'size': len(content)
    }
    
    total_score += percentage
    
    # Imprimir resultado
    status = '[OK]' if percentage >= 90 else '[WARNING]' if percentage >= 70 else '[FAIL]'
    print(f'{status} {tool_name.upper()}')
    print(f'     Qualidade: {percentage:.0f}% ({passed}/{total} criterios)')
    print(f'     Classes: {classes} | Funcoes: {functions} | Linhas: {len(content.split(chr(10)))}')
    
    for criterion, desc in CRITERIOS.items():
        status_mark = '[OK]' if checks[criterion] else '[XX]'
        print(f'     {status_mark} {desc}')
    print()

# Resumo
print('='*80)
print('RESUMO PROFISSIONAL')
print('='*80)

media = total_score / len(results) if results else 0
print(f'\nQualidade Media: {media:.1f}%')
print(f'Ferramentas: {len(results)}/5')
print(f'Status Geral: {"PRONTO PARA PRODUCAO" if media >= 85 else "REQUER MELHORIAS"}')

# Status detalhado
print('\nDETALHES:')
for tool_name, result in results.items():
    status = 'PRODUCAO' if result['percentage'] >= 90 else 'REVIEW' if result['percentage'] >= 70 else 'FALHO'
    print(f'  {tool_name}: {status} ({result["percentage"]:.0f}%)')

sys.exit(0 if media >= 85 else 1)
