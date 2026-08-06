"""
DataMaster Pro - Modern Installer
Tema dark com accents dourados, consistente com o app.
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

try:
    import win32com.client
    SHORTCUT_SUPPORT = True
except ImportError:
    SHORTCUT_SUPPORT = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('installer.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# ── Cores do tema ────────────────────────────────────────────────────────────
C = {
    "BG":         "#09090B",
    "CARD":       "#18181B",
    "CARD_HOVER": "#27272A",
    "BORDER":     "#27272A",
    "PRIMARY":    "#d48214",
    "PRIMARY_H":  "#b5690f",
    "SUCCESS":    "#22c55e",
    "DANGER":     "#EF4444",
    "TEXT":       "#FAFAFA",
    "TEXT2":      "#A1A1AA",
    "TEXT3":      "#71717A",
    "INPUT_BG":   "#09090B",
    "INPUT_BD":   "#3f3f46",
}


class ModernButton(tk.Canvas):
    """Botão customizado com cantos arredondados e hover."""
    def __init__(self, parent, text, command=None, bg=None, fg="#FAFAFA",
                 width=140, height=40, font=("Segoe UI", 10, "bold"), **kw):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=parent["bg"], **kw)
        self._bg = bg or C["PRIMARY"]
        self._fg = fg
        self._command = command
        self._w, self._h = width, height
        self._hover = False
        self._draw(text, font)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kw)

    def _draw(self, text, font):
        self.delete("all")
        color = C["PRIMARY_H"] if self._hover else self._bg
        self._rounded_rect(0, 0, self._w, self._h, 10, fill=color, outline="")
        self.create_text(self._w//2, self._h//2, text=text, fill=self._fg, font=font)

    def _on_enter(self, e):
        self._hover = True
        self._draw(self._draw_text, self._draw_font)

    def _on_leave(self, e):
        self._hover = False
        self._draw(self._draw_text, self._draw_font)

    def _on_press(self, e):
        self.configure(cursor="hand2")

    def _on_release(self, e):
        if self._command:
            self._command()

    def _draw_text(self, text, font):
        self.delete("all")
        color = C["PRIMARY_H"] if self._hover else self._bg
        self._rounded_rect(0, 0, self._w, self._h, 10, fill=color, outline="")
        self.create_text(self._w//2, self._h//2, text=text, fill=self._fg, font=font)

    def _draw(self, text, font):
        self._draw_text = text
        self._draw_font = font
        self.delete("all")
        color = C["PRIMARY_H"] if self._hover else self._bg
        self._rounded_rect(0, 0, self._w, self._h, 10, fill=color, outline="")
        self.create_text(self._w//2, self._h//2, text=text, fill=self._fg, font=font)


class ProgressBar(tk.Canvas):
    """Barra de progresso animada."""
    def __init__(self, parent, width=400, height=8, **kw):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=parent["bg"], **kw)
        self._w, self._h = width, height
        self._progress = 0
        self._draw()

    def set(self, value):
        self._progress = min(100, max(0, value))
        self._draw()

    def _draw(self):
        self.delete("all")
        self._rounded_rect(0, 0, self._w, self._h, 4, fill=C["BORDER"], outline="")
        if self._progress > 0:
            w = max(8, int(self._w * self._progress / 100))
            self._rounded_rect(0, 0, w, self._h, 4, fill=C["PRIMARY"], outline="")

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1,
        ]
        self.create_polygon(points, smooth=True, **kw)


class DataMasterInstaller:
    DEFAULT_INSTALL_PATH = r"C:\Program Files\DataMaster Pro"
    APP_DATA_PATH = Path.home() / "AppData" / "Roaming" / "DataMaster Pro"

    def __init__(self):
        self.install_path = None
        self.create_desktop_shortcut = False
        self.launch_after_install = False
        self.window = None

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _center(self, w, h):
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"{w}x{h}+{x}+{y}")

    def _make_label(self, parent, text, size=10, bold=False, color=C["TEXT"], **kw):
        weight = "bold" if bold else "normal"
        return tk.Label(parent, text=text, font=("Segoe UI", size, weight),
                        bg=parent["bg"], fg=color, **kw)

    def _separator(self, parent):
        tk.Frame(parent, bg=C["BORDER"], height=1).pack(fill=tk.X, pady=15)

    # ── Tela 1: Welcome ──────────────────────────────────────────────────────
    def show_welcome_screen(self):
        self.window = tk.Tk()
        self.window.title("DataMaster Pro — Instalador")
        self.window.configure(bg=C["BG"])
        self.window.resizable(False, False)
        self._center(580, 480)

        main = tk.Frame(self.window, bg=C["BG"])
        main.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Logo
        logo_frame = tk.Frame(main, bg=C["CARD"], width=80, height=80)
        logo_frame.pack(pady=(10, 15))
        logo_frame.pack_propagate(False)
        self._make_label(logo_frame, "DM", size=28, bold=True, color=C["PRIMARY"]).pack(expand=True)

        self._make_label(main, "DataMaster Pro", size=24, bold=True).pack()
        self._make_label(main, "Ferramenta Profissional de Processamento de Excel",
                         size=10, color=C["TEXT2"]).pack(pady=(5, 25))

        self._separator(main)

        # Card de info
        card = tk.Frame(main, bg=C["CARD"], highlightbackground=C["BORDER"], highlightthickness=1)
        card.pack(fill=tk.X, pady=(0, 20))
        self._make_label(card,
            "Bem-vindo ao instalador!\n\n"
            "  1.  Selecionar diretório de instalação\n"
            "  2.  Escolher opções (atalho, inicializar)\n"
            "  3.  Instalar e configurar\n\n"
            "Clique em Prosseguir para continuar.",
            size=10, color=C["TEXT2"], justify=tk.LEFT, wraplength=480
        ).pack(padx=20, pady=18, anchor=tk.W)

        # Botões
        btn_frame = tk.Frame(main, bg=C["BG"])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ModernButton(btn_frame, "Cancelar", command=self._cancel,
                     bg=C["CARD"], fg=C["TEXT2"], width=120).pack(side=tk.LEFT)
        ModernButton(btn_frame, "Prosseguir  →", command=self.show_path_screen,
                     bg=C["PRIMARY"], width=140).pack(side=tk.RIGHT)

        self.window.mainloop()

    # ── Tela 2: Path ─────────────────────────────────────────────────────────
    def show_path_screen(self):
        for w in self.window.winfo_children():
            w.destroy()
        self.window.title("DataMaster Pro — Diretório")

        main = tk.Frame(self.window, bg=C["BG"])
        main.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        self._make_label(main, "Diretório de Instalação", size=16, bold=True).pack(anchor=tk.W)
        self._make_label(main, "Escolha onde o DataMaster Pro será instalado:",
                         size=10, color=C["TEXT2"]).pack(anchor=tk.W, pady=(5, 15))

        # Path card
        path_card = tk.Frame(main, bg=C["CARD"], highlightbackground=C["BORDER"], highlightthickness=1)
        path_card.pack(fill=tk.X, pady=(0, 10))

        self.path_var = tk.StringVar(value=self.DEFAULT_INSTALL_PATH)
        path_entry = tk.Entry(path_card, textvariable=self.path_var,
                              font=("Consolas", 10), bg=C["INPUT_BG"], fg=C["PRIMARY"],
                              insertbackground=C["TEXT"], relief=tk.FLAT,
                              highlightbackground=C["INPUT_BD"], highlightthickness=1)
        path_entry.pack(fill=tk.X, padx=12, pady=12, ipady=6)

        ModernButton(main, "Procurar...", command=self._browse,
                     bg=C["CARD_HOVER"], fg=C["TEXT"], width=120).pack(anchor=tk.W, pady=(0, 15))

        # Aviso
        warn = tk.Frame(main, bg="#1c1917", highlightbackground="#78350f", highlightthickness=1)
        warn.pack(fill=tk.X, pady=(0, 15))
        self._make_label(warn, "⚠  Requer ~500 MB de espaço livre em disco",
                         size=9, color="#fbbf24").pack(padx=12, pady=10, anchor=tk.W)

        # Botões
        btn_frame = tk.Frame(main, bg=C["BG"])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ModernButton(btn_frame, "← Voltar", command=self.show_welcome_screen,
                     bg=C["CARD"], fg=C["TEXT2"], width=120).pack(side=tk.LEFT)
        ModernButton(btn_frame, "Prosseguir  →", command=self._validate_path,
                     bg=C["PRIMARY"], width=140).pack(side=tk.RIGHT)

    def _browse(self):
        folder = filedialog.askdirectory(
            title="Selecionar diretório de instalação",
            initialdir=self.DEFAULT_INSTALL_PATH)
        if folder:
            self.path_var.set(folder)

    def _validate_path(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Erro", "Selecione um diretório válido.")
            return
        try:
            test = Path(path) / ".dm_test"
            Path(path).mkdir(parents=True, exist_ok=True)
            test.touch()
            test.unlink()
        except (PermissionError, OSError):
            messagebox.showerror("Sem permissão",
                f"Sem permissão de escrita em:\n{path}\n\nEscolha outro diretório ou execute como Administrador.")
            return
        self.install_path = path
        self.show_options_screen()

    # ── Tela 3: Options ──────────────────────────────────────────────────────
    def show_options_screen(self):
        for w in self.window.winfo_children():
            w.destroy()
        self.window.title("DataMaster Pro — Opções")

        main = tk.Frame(self.window, bg=C["BG"])
        main.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        self._make_label(main, "Opções de Instalação", size=16, bold=True).pack(anchor=tk.W)
        self._make_label(main, f"Instalar em:  {self.install_path}",
                         size=9, color=C["TEXT3"]).pack(anchor=tk.W, pady=(5, 15))

        self._separator(main)

        # Checkbox 1
        self.shortcut_var = tk.BooleanVar(value=True)
        c1_frame = tk.Frame(main, bg=C["CARD"], highlightbackground=C["BORDER"], highlightthickness=1)
        c1_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Checkbutton(c1_frame, text="  Criar atalho na área de trabalho",
            variable=self.shortcut_var, font=("Segoe UI", 11),
            bg=C["CARD"], fg=C["TEXT"], selectcolor=C["CARD_HOVER"],
            activebackground=C["CARD"], activeforeground=C["TEXT"]
        ).pack(anchor=tk.W, padx=10, pady=(10, 0))
        self._make_label(c1_frame, "   Acesso rápido ao DataMaster Pro pela área de trabalho",
                         size=9, color=C["TEXT3"]).pack(anchor=tk.W, padx=10, pady=(0, 10))

        # Checkbox 2
        self.launch_var = tk.BooleanVar(value=True)
        c2_frame = tk.Frame(main, bg=C["CARD"], highlightbackground=C["BORDER"], highlightthickness=1)
        c2_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Checkbutton(c2_frame, text="  Iniciar após a instalação",
            variable=self.launch_var, font=("Segoe UI", 11),
            bg=C["CARD"], fg=C["TEXT"], selectcolor=C["CARD_HOVER"],
            activebackground=C["CARD"], activeforeground=C["TEXT"]
        ).pack(anchor=tk.W, padx=10, pady=(10, 0))
        self._make_label(c2_frame, "   O aplicativo será aberto automaticamente ao final",
                         size=9, color=C["TEXT3"]).pack(anchor=tk.W, padx=10, pady=(0, 10))

        # Botões
        btn_frame = tk.Frame(main, bg=C["BG"])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ModernButton(btn_frame, "← Voltar", command=self.show_path_screen,
                     bg=C["CARD"], fg=C["TEXT2"], width=120).pack(side=tk.LEFT)
        ModernButton(btn_frame, "Instalar  ✓", command=self._install,
                     bg=C["SUCCESS"], fg="#fff", width=140).pack(side=tk.RIGHT)

    # ── Tela 4: Progress ─────────────────────────────────────────────────────
    def _install(self):
        self.create_desktop_shortcut = self.shortcut_var.get()
        self.launch_after_install = self.launch_var.get()

        for w in self.window.winfo_children():
            w.destroy()
        self.window.title("DataMaster Pro — Instalando...")

        main = tk.Frame(self.window, bg=C["BG"])
        main.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        self._make_label(main, "Instalando DataMaster Pro", size=16, bold=True).pack(anchor=tk.W, pady=(10, 5))

        self.status_var = tk.StringVar(value="Preparando arquivos...")
        self._make_label(main, textvariable=self.status_var, size=10, color=C["TEXT2"]).pack(anchor=tk.W, pady=(0, 15))

        self.progress = ProgressBar(main, width=520, height=10)
        self.progress.pack(fill=tk.X)

        self.pct_var = tk.StringVar(value="0%")
        self._make_label(main, textvariable=self.pct_var, size=9, color=C["TEXT3"]).pack(anchor=tk.E, pady=(8, 0))

        self.window.update()

        steps = [
            ("Copiando arquivos...", 20),
            ("Configurando dependências...", 50),
            ("Criando atalhos...", 75),
            ("Registrando no Windows...", 90),
            ("Concluído!", 100),
        ]
        for msg, pct in steps:
            self.status_var.set(msg)
            self.progress.set(pct)
            self.pct_var.set(f"{pct}%")
            self.window.update()
            import time; time.sleep(0.3)

        if self._do_install():
            self._show_success()
            if self.launch_after_install:
                self._launch()
        else:
            messagebox.showerror("Erro", "Falha ao instalar o DataMaster Pro.")

    def _do_install(self):
        try:
            install_dir = Path(self.install_path)
            install_dir.mkdir(parents=True, exist_ok=True)

            src = Path(__file__).parent
            for item in ['src', 'assets', 'config.py', 'main.py', 'requirements.txt', '.env.example']:
                s, d = src / item, install_dir / item
                if s.is_dir():
                    if d.exists():
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                elif s.is_file():
                    d.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(s, d)

            if self.create_desktop_shortcut and SHORTCUT_SUPPORT:
                self._create_shortcut()
            self._add_registry()

            cfg = self.APP_DATA_PATH / 'installation.json'
            cfg.parent.mkdir(parents=True, exist_ok=True)
            with open(cfg, 'w') as f:
                json.dump({'install_path': str(install_dir), 'version': '1.2.8'}, f, indent=2)

            logger.info("Instalação concluída: %s", install_dir)
            return True
        except Exception as e:
            logger.error("Erro na instalação: %s", e)
            return False

    def _create_shortcut(self):
        try:
            desktop = Path.home() / "Desktop"
            lnk = desktop / "DataMaster Pro.lnk"
            exe = Path(self.install_path) / "main.exe"
            if not exe.exists():
                exe = Path(self.install_path) / "main.py"

            shell = win32com.client.Dispatch("WScript.Shell")
            sc = shell.CreateShortCut(str(lnk))
            if str(exe).endswith('.exe'):
                sc.TargetPath = str(exe)
            else:
                sc.TargetPath = sys.executable
                sc.Arguments = str(exe)
            sc.WorkingDirectory = str(self.install_path)
            icon = Path(self.install_path) / "assets" / "icon.ico"
            if icon.exists():
                sc.IconLocation = str(icon)
            sc.save()
        except Exception as e:
            logger.warning("Atalho: %s", e)

    def _add_registry(self):
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro")
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "DataMaster Pro")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.install_path)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "DataMaster Pro")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.2.8")
            winreg.CloseKey(key)
        except Exception as e:
            logger.warning("Registro: %s", e)

    # ── Tela 5: Success ──────────────────────────────────────────────────────
    def _show_success(self):
        for w in self.window.winfo_children():
            w.destroy()
        self.window.title("DataMaster Pro — Concluído")

        main = tk.Frame(self.window, bg=C["BG"])
        main.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Check animado
        check_frame = tk.Frame(main, bg=C["SUCCESS"], width=70, height=70)
        check_frame.pack(pady=(20, 15))
        check_frame.pack_propagate(False)
        self._make_label(check_frame, "✓", size=32, bold=True, color="#fff").pack(expand=True)

        self._make_label(main, "Instalação Concluída!", size=20, bold=True, color=C["SUCCESS"]).pack()
        self._make_label(main, "DataMaster Pro está pronto para uso",
                         size=10, color=C["TEXT2"]).pack(pady=(5, 20))

        self._separator(main)

        # Detalhes
        card = tk.Frame(main, bg=C["CARD"], highlightbackground=C["BORDER"], highlightthickness=1)
        card.pack(fill=tk.X, pady=(0, 20))
        self._make_label(card,
            f"Local:    {self.install_path}\n"
            f"Atalho:   {'Criado na área de trabalho' if self.create_desktop_shortcut else 'Não criado'}\n"
            f"Iniciar:  {'Sim' if self.launch_after_install else 'Não'}",
            size=10, color=C["TEXT2"], justify=tk.LEFT, font=("Consolas", 10)
        ).pack(padx=18, pady=15, anchor=tk.W)

        ModernButton(main, "Concluir", command=self.window.quit,
                     bg=C["SUCCESS"], fg="#fff", width=180).pack(pady=(10, 0))

    def _launch(self):
        try:
            exe = Path(self.install_path) / "main.exe"
            if not exe.exists():
                exe = Path(self.install_path) / "main.py"
            if exe.exists():
                subprocess.Popen([str(exe)])
        except Exception as e:
            logger.error("Launch: %s", e)

    def _cancel(self):
        if messagebox.askyesno("Cancelar", "Deseja cancelar a instalação?"):
            self.window.quit()
            sys.exit(0)


def main():
    try:
        DataMasterInstaller().show_welcome_screen()
    except Exception as e:
        logger.error("Fatal: %s", e)
        messagebox.showerror("Erro", f"Erro ao executar instalador: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
