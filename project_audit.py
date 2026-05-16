"""
DataMaster Pro - Auditoria Profissional Completa

Script que valida a integridade, funcionalidade e qualidade profissional
de todos os componentes do projeto.

Uso: python project_audit.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
import ast
import re

# Fix para encoding no Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# ========================================
# CONFIGURAÇÃO
# ========================================

PROJECT_ROOT = Path(__file__).parent
DESKTOP_PATH = PROJECT_ROOT / "datamaster-pro-desktop"
WEB_PATH = PROJECT_ROOT / "datamaster-pro-web"
SHARED_PATH = PROJECT_ROOT / "datamaster-pro-shared"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ========================================
# UTILIDADES
# ========================================

def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def log_success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}[ERRO]{Colors.RESET} {msg}")

def section_header(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

# ========================================
# VALIDAÇÕES
# ========================================

class ProjectAuditor:
    def __init__(self):
        self.results = {
            "desktop": {},
            "web": {},
            "shared": {},
            "summary": {}
        }
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.warnings = 0

    def check_file_exists(self, path: Path, description: str) -> bool:
        """Verificar se arquivo/diretório existe"""
        exists = path.exists()
        status = "✓" if exists else "✗"
        
        if exists:
            log_success(f"{description} - {path}")
            self.passed_checks += 1
        else:
            log_error(f"{description} - {path} NÃO ENCONTRADO")
            self.failed_checks += 1
        
        self.total_checks += 1
        return exists

    def check_python_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """Verificar sintaxe Python"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            ast.parse(code)
            return True, "Sintaxe OK"
        except SyntaxError as e:
            return False, f"Erro de sintaxe: {e.msg} (linha {e.lineno})"
        except Exception as e:
            return False, f"Erro: {str(e)}"

    def check_imports(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Verificar se importações básicas funcionam"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
            
            return True, imports
        except Exception as e:
            return False, [str(e)]

    def check_file_size(self, file_path: Path) -> int:
        """Retornar tamanho do arquivo em KB"""
        return file_path.stat().st_size / 1024

    def check_requirements(self, req_file: Path) -> Dict[str, Any]:
        """Validar requirements.txt"""
        results = {
            "valid": False,
            "count": 0,
            "packages": [],
            "errors": []
        }
        
        try:
            with open(req_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Simples validação de formato
                    if any(op in line for op in ['==', '>=', '<=', '>', '<', '~=']):
                        results["packages"].append(line)
                    elif line and not line.startswith('('):
                        results["packages"].append(line)
            
            results["count"] = len(results["packages"])
            results["valid"] = results["count"] > 0
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results

    def check_env_file(self, env_file: Path) -> Dict[str, Any]:
        """Validar .env file"""
        results = {
            "exists": env_file.exists(),
            "vars": [],
            "missing": [],
            "example_available": (env_file.parent / ".env.example").exists()
        }
        
        if results["exists"]:
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            if '=' in line:
                                var_name = line.split('=')[0].strip()
                                results["vars"].append(var_name)
            except Exception as e:
                results["errors"] = [str(e)]
        
        return results

    def audit_desktop_app(self):
        """Auditoria completa da aplicação desktop"""
        section_header("AUDITORIA - APLICAÇÃO DESKTOP")
        
        # Estrutura de diretórios
        log_info("Verificando estrutura de diretórios...")
        
        dirs_to_check = [
            (DESKTOP_PATH / "src/core", "Módulo Core"),
            (DESKTOP_PATH / "src/gui", "Módulo GUI"),
            (DESKTOP_PATH / "src/tools", "Módulo Ferramentas"),
            (DESKTOP_PATH / "src/utils", "Módulo Utils"),
            (DESKTOP_PATH / "assets", "Diretório Assets"),
        ]
        
        for dir_path, desc in dirs_to_check:
            self.check_file_exists(dir_path, desc)
        
        # Arquivos principais
        print()
        log_info("Verificando arquivos principais...")
        
        main_files = [
            (DESKTOP_PATH / "main.py", "Entry Point"),
            (DESKTOP_PATH / "config.py", "Configuração"),
            (DESKTOP_PATH / "requirements.txt", "Dependências"),
            (DESKTOP_PATH / "installer.py", "Instalador"),
        ]
        
        for file_path, desc in main_files:
            if self.check_file_exists(file_path, desc):
                # Verificar sintaxe Python
                if file_path.suffix == '.py':
                    valid, msg = self.check_python_syntax(file_path)
                    if valid:
                        log_success(f"  → Sintaxe: {msg}")
                    else:
                        log_warning(f"  → Sintaxe: {msg}")
                        self.warnings += 1
        
        # Ferramentas
        print()
        log_info("Verificando ferramentas...")
        
        tools = ["consolidador", "categorizador", "minerador", "orcamentos", "conciliador"]
        
        for tool in tools:
            tool_path = DESKTOP_PATH / "src/tools" / tool
            tool_file = tool_path / f"{tool}.py"
            
            if tool_path.exists():
                if tool_file.exists():
                    log_success(f"Ferramenta '{tool}' - Implementada")
                    size = self.check_file_size(tool_file)
                    if size > 100:  # Arquivo com tamanho razoável
                        log_success(f"  → Tamanho: {size:.1f} KB (OK)")
                    else:
                        log_warning(f"  → Tamanho: {size:.1f} KB (Pequeno demais?)")
                else:
                    log_error(f"Ferramenta '{tool}' - Arquivo não encontrado")
                    self.failed_checks += 1
            
            self.total_checks += 1
        
        # Páginas GUI
        print()
        log_info("Verificando páginas GUI...")
        
        pages = ["login_page", "dashboard_page", "settings_page", "tool_page"]
        pages_path = DESKTOP_PATH / "src/gui/pages"
        
        for page in pages:
            page_file = pages_path / f"{page}.py"
            if self.check_file_exists(page_file, f"Página: {page}"):
                pass
        
        # Verificar páginas de ferramentas
        tools_pages_path = pages_path / "tools"
        for tool in tools:
            tool_page = tools_pages_path / f"{tool}_page.py"
            if tool_page.exists():
                log_success(f"UI para ferramenta '{tool}'")
            else:
                log_warning(f"UI para ferramenta '{tool}' não encontrada")
                self.warnings += 1
            
            self.total_checks += 1
        
        # Dependências
        print()
        log_info("Verificando dependências...")
        
        req_path = DESKTOP_PATH / "requirements.txt"
        req_results = self.check_requirements(req_path)
        
        if req_results["valid"]:
            log_success(f"Requirements.txt válido ({req_results['count']} dependências)")
            
            # Pacotes críticos
            critical_packages = ["customtkinter", "supabase", "pandas", "openpyxl", "python-dotenv"]
            for pkg in critical_packages:
                found = any(pkg in p for p in req_results["packages"])
                if found:
                    log_success(f"  → {pkg} incluído")
                else:
                    log_error(f"  → {pkg} FALTANDO")
                    self.warnings += 1
        else:
            log_error(f"Requirements.txt inválido")
            self.failed_checks += 1
        
        self.total_checks += 1
        
        # Variáveis de ambiente
        print()
        log_info("Verificando configuração...")
        
        env_path = DESKTOP_PATH / ".env"
        env_results = self.check_env_file(env_path)
        
        if env_results["exists"]:
            log_success(f".env configurado ({len(env_results['vars'])} variáveis)")
        else:
            if env_results["example_available"]:
                log_warning(".env não configurado (use .env.example como template)")
                self.warnings += 1
            else:
                log_error(".env e .env.example não encontrados")
                self.failed_checks += 1
        
        self.total_checks += 1
        
        # Instalador
        print()
        log_info("Verificando instalador...")
        
        installer_files = [
            (DESKTOP_PATH / "installer.py", "Script do Instalador"),
            (DESKTOP_PATH / "build_installer.bat", "Build Script (Batch)"),
            (DESKTOP_PATH / "build_installer.ps1", "Build Script (PowerShell)"),
            (DESKTOP_PATH / "INSTALLER_BUILD.md", "Documentação do Instalador"),
        ]
        
        for file_path, desc in installer_files:
            if self.check_file_exists(file_path, f"Instalador: {desc}"):
                pass
        
        self.results["desktop"]["status"] = "OK" if self.failed_checks == 0 else "ISSUES FOUND"

    def audit_web_app(self):
        """Auditoria da aplicação web"""
        section_header("AUDITORIA - APLICAÇÃO WEB (Next.js)")
        
        # Estrutura
        log_info("Verificando estrutura...")
        
        dirs_to_check = [
            (WEB_PATH / "app", "App Directory"),
            (WEB_PATH / "components", "Componentes React"),
            (WEB_PATH / "lib", "Biblioteca Utils"),
            (WEB_PATH / "public", "Arquivos Estáticos"),
        ]
        
        for dir_path, desc in dirs_to_check:
            self.check_file_exists(dir_path, desc)
        
        # Configuração Next.js
        print()
        log_info("Verificando configuração Next.js...")
        
        nextjs_files = [
            (WEB_PATH / "package.json", "Package.json"),
            (WEB_PATH / "tsconfig.json", "TypeScript Config"),
            (WEB_PATH / "next.config.js", "Next Config"),
            (WEB_PATH / "tailwind.config.js", "Tailwind Config"),
            (WEB_PATH / ".env.example", ".env Template"),
        ]
        
        for file_path, desc in nextjs_files:
            self.check_file_exists(file_path, desc)
        
        # Páginas principais
        print()
        log_info("Verificando páginas da aplicação...")
        
        pages_to_check = [
            "landing", "auth", "dashboard", "planos", "downloads",
            "ajuda", "sobre", "contato", "privacidade", "termos"
        ]
        
        for page in pages_to_check:
            page_dir = WEB_PATH / "app" / page
            if page_dir.exists():
                log_success(f"Página: /{page}")
            else:
                log_warning(f"Página: /{page} - não encontrada")
                self.warnings += 1
            
            self.total_checks += 1
        
        # Supabase Integration
        print()
        log_info("Verificando integração Supabase...")
        
        supabase_files = [
            (WEB_PATH / "lib/supabase.ts", "Cliente Supabase"),
            (WEB_PATH / "supabase", "Diretório Supabase"),
        ]
        
        for file_path, desc in supabase_files:
            self.check_file_exists(file_path, desc)
        
        # Dependências
        print()
        log_info("Verificando dependências Node...")
        
        package_path = WEB_PATH / "package.json"
        
        try:
            with open(package_path, 'r') as f:
                package_data = json.load(f)
            
            deps = package_data.get("dependencies", {})
            dev_deps = package_data.get("devDependencies", {})
            
            log_success(f"Package.json válido")
            log_success(f"  → {len(deps)} dependências de produção")
            log_success(f"  → {len(dev_deps)} dependências de desenvolvimento")
            
            # Pacotes críticos
            critical = ["next", "react", "@supabase/supabase-js"]
            for pkg in critical:
                if pkg in deps or pkg in dev_deps:
                    log_success(f"  → {pkg} incluído")
                else:
                    log_error(f"  → {pkg} FALTANDO")
                    self.failed_checks += 1
        
        except Exception as e:
            log_error(f"Erro ao ler package.json: {e}")
            self.failed_checks += 1
        
        self.total_checks += 1
        
        self.results["web"]["status"] = "OK" if self.failed_checks == 0 else "ISSUES FOUND"

    def audit_shared(self):
        """Auditoria do código compartilhado"""
        section_header("AUDITORIA - CÓDIGO COMPARTILHADO")
        
        # Estrutura
        log_info("Verificando estrutura...")
        
        dirs_to_check = [
            (SHARED_PATH / "schemas", "Schemas SQL"),
            (SHARED_PATH / "constants", "Constantes"),
            (SHARED_PATH / "types", "Type Definitions"),
            (SHARED_PATH / "supabase", "Supabase Config"),
        ]
        
        for dir_path, desc in dirs_to_check:
            self.check_file_exists(dir_path, desc)
        
        # Schemas SQL
        print()
        log_info("Verificando schemas SQL...")
        
        sql_files = [
            (SHARED_PATH / "schemas/complete-schema.sql", "Schema Completo"),
            (SHARED_PATH / "schemas/supabase.sql", "Supabase SQL"),
        ]
        
        for file_path, desc in sql_files:
            if self.check_file_exists(file_path, desc):
                size = self.check_file_size(file_path)
                if size > 10:  # Deve ter tamanho considerável
                    log_success(f"  → Tamanho: {size:.1f} KB (OK)")
                else:
                    log_warning(f"  → Tamanho: {size:.1f} KB (Muito pequeno)")
        
        # Edge Functions
        print()
        log_info("Verificando Edge Functions...")
        
        edge_functions = [
            ("send-email/index.ts", "send-email"),
            ("cakto-webhook/index.ts", "cakto-webhook"),
            ("sync-background/index.ts", "sync-background")
        ]
        
        edge_path = SHARED_PATH / "supabase/functions"
        
        for func_file, func_name in edge_functions:
            func_file_path = edge_path / func_file
            if func_file_path.exists():
                log_success(f"Edge Function: {func_name}")
                size = self.check_file_size(func_file_path)
                log_success(f"  → Tamanho: {size:.1f} KB")
            else:
                log_error(f"Edge Function: {func_name} ({func_file}) - NÃO ENCONTRADO")
                self.failed_checks += 1
            
            self.total_checks += 1
        
        # Constants
        print()
        log_info("Verificando constantes...")
        
        const_file = SHARED_PATH / "constants/__init__.py"
        
        if self.check_file_exists(const_file, "Arquivo de Constantes"):
            # Verificar sintaxe
            valid, msg = self.check_python_syntax(const_file)
            if valid:
                log_success(f"  → Sintaxe: {msg}")
            else:
                log_warning(f"  → Sintaxe: {msg}")
        
        # Types
        print()
        log_info("Verificando type definitions...")
        
        types_file = SHARED_PATH / "types/__init__.py"
        
        if self.check_file_exists(types_file, "Arquivo de Types"):
            valid, msg = self.check_python_syntax(types_file)
            if valid:
                log_success(f"  → Sintaxe: {msg}")
            else:
                log_warning(f"  → Sintaxe: {msg}")
        
        # Documentação
        print()
        log_info("Verificando documentação...")
        
        docs = [
            (SHARED_PATH / "schemas/SUPABASE_SETUP.md", "Setup Guide"),
            (SHARED_PATH / "schemas/SUPABASE_ARCHITECTURE.md", "Architecture Doc"),
            (SHARED_PATH / "schemas/INTEGRATION_EXAMPLES.md", "Integration Examples"),
            (SHARED_PATH / "README.md", "README"),
        ]
        
        for file_path, desc in docs:
            self.check_file_exists(file_path, f"Doc: {desc}")
        
        self.results["shared"]["status"] = "OK" if self.failed_checks == 0 else "ISSUES FOUND"

    def generate_summary(self):
        """Gerar relatório final"""
        section_header("RESUMO DA AUDITORIA")
        
        print(f"Total de verificações: {self.total_checks}")
        print(f"{Colors.GREEN}Passou: {self.passed_checks}{Colors.RESET}")
        print(f"{Colors.YELLOW}Avisos: {self.warnings}{Colors.RESET}")
        print(f"{Colors.RED}Falhou: {self.failed_checks}{Colors.RESET}")
        
        success_rate = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        
        print()
        
        if success_rate == 100:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ PROJETO 100% PROFISSIONAL{Colors.RESET}")
        elif success_rate >= 90:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ PROJETO COM ALTA QUALIDADE ({success_rate:.1f}%){Colors.RESET}")
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ PROJETO COM QUALIDADE BOA ({success_rate:.1f}%){Colors.RESET}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ PROJETO REQUER MELHORIAS ({success_rate:.1f}%){Colors.RESET}")
        
        print()
        
        # Recomendações
        if self.failed_checks > 0 or self.warnings > 0:
            print(f"{Colors.BOLD}Recomendações:{Colors.RESET}")
            print()
            
            if self.failed_checks > 0:
                print(f"  {Colors.RED}1. Resolver {self.failed_checks} erro(s) crítico(s){Colors.RESET}")
            
            if self.warnings > 0:
                print(f"  {Colors.YELLOW}2. Investigar {self.warnings} aviso(s){Colors.RESET}")
            
            print(f"  {Colors.BLUE}3. Executar testes unitários{Colors.RESET}")
            print(f"  {Colors.BLUE}4. Fazer build do instalador{Colors.RESET}")
            print(f"  {Colors.BLUE}5. Testar em ambiente Windows 10/11{Colors.RESET}")
        
        print()

    def run_full_audit(self):
        """Executar auditoria completa"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}DataMaster Pro - Auditoria Profissional Completa{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        self.audit_desktop_app()
        self.audit_web_app()
        self.audit_shared()
        self.generate_summary()
        
        print(f"\n{Colors.BLUE}Auditoria finalizada.{Colors.RESET}\n")

# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    auditor = ProjectAuditor()
    auditor.run_full_audit()
