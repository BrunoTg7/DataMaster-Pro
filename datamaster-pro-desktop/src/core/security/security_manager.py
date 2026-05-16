"""
Security Manager - HWID and Anti-Cloning System
Gera uma identidade única do hardware para evitar pirataria e clonagem.
"""
import subprocess
import hashlib
import os
import sys

class SecurityManager:
    @staticmethod
    def get_hwid() -> str:
        """
        Gera um ID único baseado no Serial da Placa-Mãe e ID do Processador.
        Usa PowerShell (Get-CimInstance) para compatibilidade com Windows 11 moderno.
        """
        try:
            # Captura Serial da Placa Mãe via PowerShell
            cmd_board = 'powershell "Get-CimInstance Win32_BaseBoard | Select-Object -ExpandProperty SerialNumber"'
            serial = subprocess.check_output(cmd_board, shell=True).decode().strip()
            
            # Captura ID do Processador via PowerShell
            cmd_cpu = 'powershell "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty ProcessorId"'
            cpu_id = subprocess.check_output(cmd_cpu, shell=True).decode().strip()
            
            # Combina e gera um Hash SHA-256
            raw_id = f"DATAMASTER-PRO-{serial}-{cpu_id}"
            return hashlib.sha256(raw_id.encode()).hexdigest()
        except Exception as e:
            # Fallback seguro caso o PowerShell falhe
            import uuid
            node = str(uuid.getnode())
            return hashlib.sha256(f"FALLBACK-{node}".encode()).hexdigest()

    @staticmethod
    def check_instance_lock():
        """
        Garante que apenas UMA instância do app esteja rodando.
        Evita que o usuário abra múltiplos processos para burlar limites.
        """
        import socket
        try:
            # Tenta abrir um socket em uma porta específica
            # Se a porta estiver ocupada, significa que o app já está aberto
            lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            lock_socket.bind(('127.0.0.1', 47201)) # Porta arbitrária para o DataMaster
            # Mantemos o socket aberto durante toda a vida do processo
            return lock_socket
        except socket.error:
            print("⚠️ Erro: Uma instância do DataMaster Pro já está em execução.")
            return None
