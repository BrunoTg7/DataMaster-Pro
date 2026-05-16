"""
DataMaster Pro - Windows Installer with Folder Selection and Shortcut Creation

Script que gerencia a instalação do DataMaster Pro com:
- Dialog de seleção de pasta
- Opção de criar atalho na área de trabalho
- Validação de permissões
- Launch após instalação (opcional)
"""

import os
import sys
import shutil
import logging
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import subprocess

# Tentar importar pywin32 para criar atalhos (Windows)
try:
    import win32com.client
    import win32api
    SHORTCUT_SUPPORT = True
except ImportError:
    SHORTCUT_SUPPORT = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('installer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataMasterInstaller:
    """Gerenciador de instalação do DataMaster Pro"""
    
    # Paths padrão
    DEFAULT_INSTALL_PATH = r"C:\Program Files\DataMaster Pro"
    APP_DATA_PATH = Path.home() / "AppData" / "Roaming" / "DataMaster Pro"
    
    def __init__(self):
        """Inicializar instalador"""
        self.install_path = None
        self.create_desktop_shortcut = False
        self.launch_after_install = False
        self.window = None
        
    def show_welcome_screen(self):
        """Mostrar tela de boas-vindas do instalador"""
        self.window = tk.Tk()
        self.window.title("DataMaster Pro - Instalador")
        self.window.geometry("600x400")
        self.window.resizable(False, False)
        
        # Centralizar janela
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Logo/Título
        title_label = tk.Label(
            main_frame,
            text="DataMaster Pro",
            font=("Segoe UI", 28, "bold"),
            bg="#f0f0f0",
            fg="#1e40af"
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = tk.Label(
            main_frame,
            text="Ferramenta Profissional de Processamento de Excel",
            font=("Segoe UI", 11),
            bg="#f0f0f0",
            fg="#64748b"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Descrição
        desc_frame = tk.Frame(main_frame, bg="#ffffff", bd=1, relief=tk.SOLID)
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        desc_text = tk.Label(
            desc_frame,
            text=(
                "Bem-vindo ao instalador do DataMaster Pro!\n\n"
                "Este assistente irá guiá-lo através dos seguintes passos:\n"
                "• Seleção do diretório de instalação\n"
                "• Criação de atalho na área de trabalho (opcional)\n"
                "• Configuração inicial da aplicação\n\n"
                "Clique em 'Próximo' para continuar."
            ),
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#334155",
            justify=tk.LEFT,
            wraplength=500
        )
        desc_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Botões
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancelar",
            font=("Segoe UI", 10),
            width=12,
            command=self.cancel_installation
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        next_btn = tk.Button(
            button_frame,
            text="Próximo",
            font=("Segoe UI", 10),
            width=12,
            bg="#1e40af",
            fg="white",
            command=self.show_install_path_screen
        )
        next_btn.pack(side=tk.RIGHT, padx=5)
        
        self.window.mainloop()
        
    def show_install_path_screen(self):
        """Mostrar tela de seleção de caminho de instalação"""
        # Limpar janela anterior
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.window.title("DataMaster Pro - Seleção de Diretório")
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="Selecionar Diretório de Instalação",
            font=("Segoe UI", 16, "bold"),
            bg="#f0f0f0",
            fg="#1e40af"
        )
        title_label.pack(pady=(0, 20), anchor=tk.W)
        
        # Frame de informação
        info_frame = tk.Frame(main_frame, bg="#eff6ff", bd=1, relief=tk.SOLID)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        info_text = tk.Label(
            info_frame,
            text="Escolha o diretório onde o DataMaster Pro será instalado:",
            font=("Segoe UI", 10),
            bg="#eff6ff",
            fg="#1e40af",
            justify=tk.LEFT
        )
        info_text.pack(padx=10, pady=10, anchor=tk.W)
        
        # Display do caminho selecionado
        self.path_var = tk.StringVar(value=self.DEFAULT_INSTALL_PATH)
        
        path_label = tk.Label(
            main_frame,
            text="Caminho de instalação:",
            font=("Segoe UI", 10, "bold"),
            bg="#f0f0f0",
            fg="#334155"
        )
        path_label.pack(pady=(10, 5), anchor=tk.W)
        
        path_frame = tk.Frame(main_frame, bg="#ffffff", bd=1, relief=tk.SOLID)
        path_frame.pack(fill=tk.X, pady=(0, 15))
        
        path_display = tk.Label(
            path_frame,
            textvariable=self.path_var,
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#1e40af",
            wraplength=400,
            justify=tk.LEFT
        )
        path_display.pack(padx=10, pady=10, anchor=tk.W, fill=tk.X)
        
        # Botão para escolher pasta
        browse_btn = tk.Button(
            main_frame,
            text="Procurar...",
            font=("Segoe UI", 10),
            width=15,
            command=self.browse_install_folder
        )
        browse_btn.pack(pady=(0, 20), anchor=tk.W)
        
        # Aviso de espaço em disco
        disk_info_label = tk.Label(
            main_frame,
            text="⚠ Requer aproximadamente 500 MB de espaço livre em disco",
            font=("Segoe UI", 9),
            bg="#fef3c7",
            fg="#92400e",
            wraplength=450,
            justify=tk.LEFT
        )
        disk_info_label.pack(fill=tk.X, pady=10)
        
        # Botões
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancelar",
            font=("Segoe UI", 10),
            width=12,
            command=self.cancel_installation
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        back_btn = tk.Button(
            button_frame,
            text="Voltar",
            font=("Segoe UI", 10),
            width=12,
            command=self.show_welcome_screen
        )
        back_btn.pack(side=tk.LEFT, padx=5)
        
        next_btn = tk.Button(
            button_frame,
            text="Próximo",
            font=("Segoe UI", 10),
            width=12,
            bg="#1e40af",
            fg="white",
            command=self.validate_and_show_options_screen
        )
        next_btn.pack(side=tk.RIGHT, padx=5)
        
    def browse_install_folder(self):
        """Abrir dialog para seleção de pasta"""
        folder = filedialog.askdirectory(
            title="Selecione o diretório de instalação do DataMaster Pro",
            initialdir=self.DEFAULT_INSTALL_PATH
        )
        if folder:
            self.path_var.set(folder)
            
    def validate_and_show_options_screen(self):
        """Validar caminho e mostrar tela de opções"""
        install_path = self.path_var.get().strip()
        
        if not install_path:
            messagebox.showerror("Erro", "Por favor, selecione um diretório válido")
            return
        
        # Validar permissões
        if not self.check_write_permissions(install_path):
            messagebox.showerror(
                "Erro de Permissão",
                f"Você não tem permissão de escrita em:\n{install_path}\n\n"
                "Por favor, escolha outro diretório ou execute como Administrador."
            )
            return
        
        self.install_path = install_path
        self.show_options_screen()
        
    def check_write_permissions(self, path):
        """Verificar se temos permissão de escrita no diretório"""
        try:
            test_file = Path(path) / ".datamaster_test"
            Path(path).mkdir(parents=True, exist_ok=True)
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False
        
    def show_options_screen(self):
        """Mostrar tela de opções (atalho, launch após instalação)"""
        # Limpar janela
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.window.title("DataMaster Pro - Opções de Instalação")
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="Opções de Instalação",
            font=("Segoe UI", 16, "bold"),
            bg="#f0f0f0",
            fg="#1e40af"
        )
        title_label.pack(pady=(0, 20), anchor=tk.W)
        
        # Resumo do caminho
        summary_label = tk.Label(
            main_frame,
            text=f"Local de instalação: {self.install_path}",
            font=("Segoe UI", 10),
            bg="#f0f0f0",
            fg="#64748b"
        )
        summary_label.pack(pady=(0, 20), anchor=tk.W)
        
        # Checkboxes
        options_frame = tk.Frame(main_frame, bg="#f0f0f0")
        options_frame.pack(fill=tk.BOTH, expand=True, anchor=tk.W)
        
        # Checkbox 1: Criar atalho na área de trabalho
        self.shortcut_var = tk.BooleanVar(value=True)
        shortcut_frame = tk.Frame(options_frame, bg="#f0f0f0")
        shortcut_frame.pack(fill=tk.X, pady=15)
        
        shortcut_cb = tk.Checkbutton(
            shortcut_frame,
            text="Criar atalho na área de trabalho",
            variable=self.shortcut_var,
            font=("Segoe UI", 11),
            bg="#f0f0f0",
            fg="#334155",
            selectcolor="#f0f0f0",
            activebackground="#f0f0f0"
        )
        shortcut_cb.pack(anchor=tk.W)
        
        shortcut_desc = tk.Label(
            shortcut_frame,
            text="Um atalho será adicionado à sua área de trabalho para iniciar rapidamente o DataMaster Pro",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#94a3b8",
            wraplength=450,
            justify=tk.LEFT
        )
        shortcut_desc.pack(anchor=tk.W, padx=(25, 0), pady=(5, 0))
        
        # Checkbox 2: Iniciar após instalação
        self.launch_var = tk.BooleanVar(value=True)
        launch_frame = tk.Frame(options_frame, bg="#f0f0f0")
        launch_frame.pack(fill=tk.X, pady=15)
        
        launch_cb = tk.Checkbutton(
            launch_frame,
            text="Iniciar DataMaster Pro após instalação",
            variable=self.launch_var,
            font=("Segoe UI", 11),
            bg="#f0f0f0",
            fg="#334155",
            selectcolor="#f0f0f0",
            activebackground="#f0f0f0"
        )
        launch_cb.pack(anchor=tk.W)
        
        launch_desc = tk.Label(
            launch_frame,
            text="O aplicativo será inicializado automaticamente ao término da instalação",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#94a3b8",
            wraplength=450,
            justify=tk.LEFT
        )
        launch_desc.pack(anchor=tk.W, padx=(25, 0), pady=(5, 0))
        
        # Botões
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancelar",
            font=("Segoe UI", 10),
            width=12,
            command=self.cancel_installation
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        back_btn = tk.Button(
            button_frame,
            text="Voltar",
            font=("Segoe UI", 10),
            width=12,
            command=self.show_install_path_screen
        )
        back_btn.pack(side=tk.LEFT, padx=5)
        
        install_btn = tk.Button(
            button_frame,
            text="Instalar",
            font=("Segoe UI", 10),
            width=12,
            bg="#1e40af",
            fg="white",
            command=self.execute_installation
        )
        install_btn.pack(side=tk.RIGHT, padx=5)
        
    def execute_installation(self):
        """Executar a instalação"""
        try:
            self.create_desktop_shortcut = self.shortcut_var.get()
            self.launch_after_install = self.launch_var.get()
            
            # Limpar janela e mostrar progresso
            for widget in self.window.winfo_children():
                widget.destroy()
            
            self.window.title("DataMaster Pro - Instalando...")
            
            progress_frame = tk.Frame(self.window, bg="#f0f0f0")
            progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            progress_label = tk.Label(
                progress_frame,
                text="Instalando DataMaster Pro...",
                font=("Segoe UI", 12, "bold"),
                bg="#f0f0f0",
                fg="#1e40af"
            )
            progress_label.pack(pady=(20, 10))
            
            status_label = tk.Label(
                progress_frame,
                text="Copiando arquivos...",
                font=("Segoe UI", 10),
                bg="#f0f0f0",
                fg="#64748b"
            )
            status_label.pack(pady=5)
            
            # Atualizar a janela
            self.window.update()
            
            # Executar instalação
            if self.install_files():
                status_label.config(text="Criando atalhos...")
                self.window.update()
                
                if self.create_desktop_shortcut and SHORTCUT_SUPPORT:
                    self.create_desktop_shortcut_file()
                
                # Criar entrada no registro (opcional)
                self.add_to_registry()
                
                # Mostrar tela de sucesso
                self.show_success_screen()
                
                if self.launch_after_install:
                    self.launch_application()
            else:
                messagebox.showerror("Erro", "Falha ao instalar o DataMaster Pro")
                
        except Exception as e:
            logger.error(f"Erro durante instalação: {e}")
            messagebox.showerror("Erro de Instalação", f"Erro: {str(e)}")
            
    def install_files(self):
        """Copiar arquivos da aplicação para o diretório de instalação"""
        try:
            logger.info(f"Instalando para: {self.install_path}")
            
            # Criar diretório de instalação
            install_dir = Path(self.install_path)
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar arquivos do aplicativo
            app_source = Path(__file__).parent
            
            # Arquivos e diretórios a copiar
            items_to_copy = [
                'src', 'assets', 'config.py', 'main.py', 
                'requirements.txt', '.env.example'
            ]
            
            for item in items_to_copy:
                source = app_source / item
                dest = install_dir / item
                
                if source.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(source, dest)
                    logger.info(f"Copiado diretório: {item}")
                elif source.is_file():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                    logger.info(f"Copiado arquivo: {item}")
            
            # Instalar dependências Python
            self.install_dependencies()
            
            # Salvar configuração de instalação
            config_data = {
                'install_path': str(install_dir),
                'install_date': str(Path.home()),
                'version': '1.0.0'
            }
            
            config_file = self.APP_DATA_PATH / 'installation.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info("Instalação de arquivos concluída")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao instalar arquivos: {e}")
            return False
        
    def install_dependencies(self):
        """Instalar dependências Python usando pip"""
        try:
            requirements_file = Path(self.install_path) / 'requirements.txt'
            
            if requirements_file.exists():
                logger.info("Instalando dependências Python...")
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', 
                    '-r', str(requirements_file), '-q'
                ])
                logger.info("Dependências instaladas com sucesso")
                
        except subprocess.CalledProcessError as e:
            logger.warning(f"Aviso ao instalar dependências: {e}")
            # Continuar mesmo se falhar
        except Exception as e:
            logger.warning(f"Erro ao instalar dependências: {e}")
        
    def create_desktop_shortcut_file(self):
        """Criar atalho na área de trabalho"""
        try:
            if not SHORTCUT_SUPPORT:
                logger.warning("pywin32 não disponível, pulando criação de atalho")
                return
            
            desktop_path = Path.home() / "Desktop"
            shortcut_path = desktop_path / "DataMaster Pro.lnk"
            
            # Caminho do executável
            exe_path = Path(self.install_path) / "main.exe"  # Para PyInstaller
            if not exe_path.exists():
                # Se não for um .exe, usar python para executar main.py
                exe_path = Path(self.install_path) / "main.py"
            
            # Criar atalho usando pywin32
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            
            if str(exe_path).endswith('.exe'):
                shortcut.TargetPath = str(exe_path)
                shortcut.WorkingDirectory = str(self.install_path)
            else:
                shortcut.TargetPath = sys.executable
                shortcut.Arguments = str(exe_path)
                shortcut.WorkingDirectory = str(self.install_path)
            
            # Ícone (se disponível)
            icon_path = Path(self.install_path) / "assets" / "icon.ico"
            if icon_path.exists():
                shortcut.IconLocation = str(icon_path)
            
            shortcut.save()
            logger.info(f"Atalho criado em: {shortcut_path}")
            
        except Exception as e:
            logger.error(f"Erro ao criar atalho: {e}")
            
    def add_to_registry(self):
        """Adicionar entrada ao registro do Windows (Programas e Recursos)"""
        try:
            import winreg
            
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path)
            
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "DataMaster Pro")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.install_path)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "DataMaster Pro")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            
            winreg.CloseKey(key)
            logger.info("Entrada adicionada ao registro")
            
        except Exception as e:
            logger.warning(f"Aviso ao adicionar ao registro: {e}")
        
    def show_success_screen(self):
        """Mostrar tela de sucesso da instalação"""
        # Limpar janela
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.window.title("DataMaster Pro - Instalação Concluída")
        
        # Frame principal
        main_frame = tk.Frame(self.window, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Ícone de sucesso
        success_label = tk.Label(
            main_frame,
            text="✓",
            font=("Segoe UI", 60),
            bg="#f0f0f0",
            fg="#10b981"
        )
        success_label.pack(pady=(10, 5))
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="Instalação Concluída com Sucesso!",
            font=("Segoe UI", 16, "bold"),
            bg="#f0f0f0",
            fg="#10b981"
        )
        title_label.pack(pady=(0, 20))
        
        # Detalhes
        details_frame = tk.Frame(main_frame, bg="#ecfdf5", bd=1, relief=tk.SOLID)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        details_text = f"""DataMaster Pro foi instalado com sucesso em:
{self.install_path}

Próximos passos:
✓ Atalho na área de trabalho criado{'  ' if self.create_desktop_shortcut else ' (não criado)'}
✓ Aplicação pronta para usar

Você pode iniciar o DataMaster Pro a qualquer momento através do atalho na área de trabalho ou do menu Iniciar.
"""
        
        details_label = tk.Label(
            details_frame,
            text=details_text,
            font=("Segoe UI", 10),
            bg="#ecfdf5",
            fg="#065f46",
            justify=tk.LEFT,
            wraplength=450
        )
        details_label.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Botão fechar
        close_btn = tk.Button(
            main_frame,
            text="Concluir",
            font=("Segoe UI", 11),
            width=20,
            bg="#10b981",
            fg="white",
            command=self.window.quit
        )
        close_btn.pack(pady=20)
        
    def launch_application(self):
        """Iniciar o DataMaster Pro após instalação"""
        try:
            exe_path = Path(self.install_path) / "main.exe"
            
            if not exe_path.exists():
                exe_path = Path(self.install_path) / "main.py"
            
            if exe_path.exists():
                logger.info(f"Iniciando aplicação: {exe_path}")
                subprocess.Popen([str(exe_path)])
            else:
                logger.warning(f"Executável não encontrado: {exe_path}")
                
        except Exception as e:
            logger.error(f"Erro ao iniciar aplicação: {e}")
        
    def cancel_installation(self):
        """Cancelar instalação"""
        if messagebox.askyesno("Cancelar", "Deseja realmente cancelar a instalação?"):
            logger.info("Instalação cancelada pelo usuário")
            self.window.quit()
            sys.exit(0)


def main():
    """Função principal do instalador"""
    try:
        installer = DataMasterInstaller()
        installer.show_welcome_screen()
    except Exception as e:
        logger.error(f"Erro fatal no instalador: {e}")
        messagebox.showerror("Erro Fatal", f"Erro ao executar o instalador: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
