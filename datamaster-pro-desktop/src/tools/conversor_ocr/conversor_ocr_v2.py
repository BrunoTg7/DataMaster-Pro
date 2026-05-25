"""
Conversor v3.0 - Extrai dados de PDFs e Imagens
- PDFs: Usa PyMuPDF (sem necessidade de OCR)
- Imagens: Necessita Tesseract (avisa o usuário)
"""
import os
import sys
import requests
import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from src.utils.excel_styler import save_premium_excel


class ConversorOCR:
    """Conversor de PDFs e Imagens para Excel - Versão simplificada com suporte a OCR em PDF"""

    def __init__(self, progress_callback=None, log_callback=None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.libs_installed = True
        try:
            self._setup_tesseract_path()
        except ImportError:
            self.libs_installed = False
            self._log("Erro: Bibliotecas Python (pytesseract, etc) não instaladas.")
        
        self.pymupdf_available = self._check_pymupdf()
        self.tesseract_available = self._check_tesseract()
    
    def _setup_tesseract_path(self):
        """Configura o caminho do Tesseract, procurando em locais comuns e no diretório local"""
        try:
            import pytesseract
        except ImportError:
            self._log("Módulo 'pytesseract' não encontrado. Use: pip install pytesseract")
            raise
        
        # 1. Tenta encontrar no diretório de dependências do app (bundle) - Prioridade Máxima
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_tesseract = os.path.join(base_dir, "bin", "tesseract", "tesseract.exe")
        
        # 2. Caminhos para busca (lista exaustiva)
        import shutil
        common_paths = [
            local_tesseract,
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tesseract-OCR", "tesseract.exe"),
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Tesseract-OCR", "tesseract.exe"),
            shutil.which("tesseract")
        ]
        
        self._log(f"DEBUG: Iniciando busca do Tesseract em {len(common_paths)} locais...")
        
        for path in common_paths:
            if not path: continue
            self._log(f"DEBUG: Verificando: {path}")
            if os.path.exists(path):
                # Verifica se o diretório tessdata existe e tem o idioma português
                tessdata = os.path.join(os.path.dirname(path), "tessdata")
                por_data = os.path.join(tessdata, "por.traineddata")
                
                if os.path.exists(por_data):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self._set_tessdata(tessdata)
                    self._log(f"Tesseract (com idioma PT) encontrado em: {path}")
                    self.tesseract_available = True
                    return
                else:
                    self._log(f"Tesseract encontrado em {path}, mas SEM idioma Português.")
                    
                    # Tenta baixar o idioma. Se der erro de permissão, migramos para local.
                    try:
                        os.makedirs(tessdata, exist_ok=True)
                        url_por = "https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata"
                        import requests
                        resp = requests.get(url_por, timeout=60)
                        if resp.status_code == 200:
                            with open(por_data, "wb") as f:
                                f.write(resp.content)
                            self._log("✅ Idioma Português instalado com sucesso!")
                            pytesseract.pytesseract.tesseract_cmd = path
                            self._set_tessdata(tessdata)
                            self.tesseract_available = True
                            return
                    except Exception as e:
                        if "Permission denied" in str(e) and "Program Files" in path:
                            self._log("⚠️ Sem permissão no Program Files. Migrando Tesseract para pasta local...")
                            try:
                                import shutil
                                src_dir = os.path.dirname(path)
                                dest_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "tesseract")
                                
                                # Copia tudo para o local onde temos permissão
                                if os.path.exists(dest_dir): shutil.rmtree(dest_dir, ignore_errors=True)
                                shutil.copytree(src_dir, dest_dir)
                                
                                # Agora tenta baixar na cópia local
                                local_tessdata = os.path.join(dest_dir, "tessdata")
                                local_por = os.path.join(local_tessdata, "por.traineddata")
                                os.makedirs(local_tessdata, exist_ok=True)
                                
                                self._log("🌐 Baixando idioma na pasta local...")
                                resp = requests.get(url_por, timeout=60)
                                with open(local_por, "wb") as f:
                                    f.write(resp.content)
                                
                                new_exe = os.path.join(dest_dir, "tesseract.exe")
                                pytesseract.pytesseract.tesseract_cmd = new_exe
                                self._set_tessdata(local_tessdata)
                                self.tesseract_available = True
                                self._log("✅ Migração e idioma concluídos com sucesso!")
                                return
                            except Exception as e2:
                                self._log(f"❌ Falha na migração: {e2}")
                        else:
                            self._log(f"⚠️ Erro ao baixar idioma: {e}")
                    
                    self.tesseract_available = False
        
        # Se chegou aqui, nenhum Tesseract válido foi encontrado.
        # Não setamos tesseract_cmd nem tesseract_available, forçando o auto-setup.
        self.tesseract_available = False
        self._log("Nenhum Tesseract completo encontrado. Preparando instalação local...")
        
        self._log("Tesseract não encontrado nos locais padrões ou no PATH.")

    def _set_tessdata(self, tessdata_dir: str):
        """Define o diretório de dados do Tesseract via variável de ambiente"""
        if os.path.exists(tessdata_dir):
            os.environ["TESSDATA_PREFIX"] = tessdata_dir
            self._tessdata_dir = tessdata_dir

    def _log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)
    
    def _check_pymupdf(self) -> bool:
        try:
            import fitz
            return True
        except Exception:
            return False
    
    def _check_tesseract(self) -> bool:
        try:
            import pytesseract
            cmd = pytesseract.pytesseract.tesseract_cmd
            if cmd and os.path.exists(cmd):
                return True
            # Tenta rodar 'tesseract --version' pra ver se tá no PATH
            import subprocess
            subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False
    
    def get_status(self) -> Dict:
        return {
            "libs_installed": self.libs_installed,
            "pymupdf_installed": self.pymupdf_available,
            "tesseract_installed": self.tesseract_available,
            "pdf_support": self.pymupdf_available,
            "image_support": self.tesseract_available,
            "tesseract_path": getattr(__import__('pytesseract').pytesseract, 'tesseract_cmd', 'Não configurado') if self.libs_installed else "Módulo ausente",
            "version": "3.1"
        }
    
    def process_multiple(self, files: List[str], output_dir: str, extract_tables: bool = True, visual_theme: str = "classic_blue") -> Dict:
        """Processa múltiplos arquivos"""
        results = []
        processed = 0
        
        for file_path in files:
            try:
                result = self.process_file(file_path, output_dir, extract_tables, visual_theme=visual_theme)
                results.append({"file": file_path, "result": result})
                if result.get("success"):
                    processed += 1
            except Exception as e:
                results.append({"file": file_path, "result": {"success": False, "error": str(e)}})
        
        return {
            "total": len(files),
            "processed": processed,
            "results": results
        }
    
    def process_file(self, file_path: str, output_dir: str, extract_tables: bool = True, visual_theme: str = "classic_blue") -> Dict:
        try:
            ext = Path(file_path).suffix.lower()

            if ext == ".pdf":
                return self._process_pdf(file_path, output_dir, extract_tables, visual_theme)
            elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]:
                return self._process_image(file_path, output_dir, visual_theme)
            else:
                return {"success": False, "error": "Tipo de arquivo não suportado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_financeiro(self, texto: str) -> Dict:
        """Extrai dados financeiros básicos do texto usando Regex"""
        dados = {
            "valor_total": "",
            "data": "",
            "cnpj_cpf": ""
        }
        
        # 1. Busca todos os valores monetários no formato 1.234,56
        valores_encontrados = re.findall(r'([\d\.]+\,\d{2})', texto)
        
        # 2. Busca específica por Valor Total (Prioridade)
        valor_total_patterns = [
            r'VALOR TOTAL DO SERVIÇO\s*[\=\:]*\s*R\$\s*([\d\.]+\,\d{2})',
            r'VALOR TOTAL\s*[\=\:]*\s*R\$\s*([\d\.]+\,\d{2})',
            r'TOTAL\s*[\=\:]*\s*R\$\s*([\d\.]+\,\d{2})',
            r'VALOR TOTAL DO SERVIÇO\s*[\=\:]*\s*([\d\.]+\,\d{2})'
        ]
        
        for pattern in valor_total_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                dados["valor_total"] = match.group(1)
                break
        
        # 3. Se não achou pelo nome, pega o maior valor da nota (geralmente é o total)
        if not dados["valor_total"] and valores_encontrados:
            try:
                # Converte strings "1.234,56" para float para comparar
                nums = [float(v.replace('.', '').replace(',', '.')) for v in valores_encontrados]
                max_idx = nums.index(max(nums))
                dados["valor_total"] = valores_encontrados[max_idx]
            except Exception: pass
            
        # Data (DD/MM/AAAA)
        data_match = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_match:
            dados["data"] = data_match.group(1)
            
        # CNPJ (00.000.000/0001-00)
        cnpj_match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
        if cnpj_match:
            dados["cnpj_cpf"] = cnpj_match.group(1)
            
        return dados

    def _process_pdf(self, pdf_path: str, output_dir: str, extract_tables: bool = True, visual_theme: str = "classic_blue") -> Dict:
        """Extrai texto de PDF, com fallback para OCR se necessário"""
        if not self.pymupdf_available:
            return {"success": False, "error": "PyMuPDF não instalado"}
        
        try:
            import fitz
            all_data = []
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            has_text = False
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text().strip()
                
                if text:
                    has_text = True
                    financeiro = self._parse_financeiro(text)
                    clean_text = " ".join(text.split())
                    
                    all_data.append({
                        "pagina": page_num + 1,
                        "tipo": "texto_nativo",
                        "valor": financeiro["valor_total"],
                        "data": financeiro["data"],
                        "cnpj": financeiro["cnpj_cpf"],
                        "conteudo": clean_text[:500] + "..." if len(clean_text) > 500 else clean_text
                    })
                    
                    if financeiro["valor_total"]:
                        self._log(f"   [Dados Encontrados] Valor: {financeiro['valor_total']} | Data: {financeiro['data']}")
                
                if self.progress_callback:
                    self.progress_callback(int(((page_num + 0.5) / total_pages) * 100))

            # Se não encontrou texto nativo, tenta OCR
            if not has_text:
                if not self.tesseract_available:
                    doc.close()
                    return {
                        "success": False, 
                        "error": "PDF sem texto nativo e Tesseract não encontrado para OCR",
                        "hint": "Instale o Tesseract para processar PDFs escaneados."
                    }
                
                self._log(f"PDF {os.path.basename(pdf_path)} parece escaneado. Iniciando OCR...")
                import pytesseract
                from PIL import Image
                import io

                # DEBUG PROFUNDO
                import subprocess
                try:
                    tess_v = subprocess.run([pytesseract.pytesseract.tesseract_cmd, "--version"], capture_output=True, text=True)
                    self._log(f"DEBUG Tesseract EXE: {pytesseract.pytesseract.tesseract_cmd}")
                    self._log(f"DEBUG Tesseract Version: {tess_v.stdout.splitlines()[0]}")
                    self._log(f"DEBUG ENV TESSDATA_PREFIX: {os.environ.get('TESSDATA_PREFIX')}")
                except Exception as e:
                    self._log(f"DEBUG Erro ao checar versão: {e}")

                for page_num in range(total_pages):
                    page = doc[page_num]
                    # Converte página para imagem
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom 2x para melhor OCR
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR — TESSDATA_PREFIX já está definido via os.environ
                    if hasattr(self, "_tessdata_dir"):
                        os.environ["TESSDATA_PREFIX"] = self._tessdata_dir
                    
                    try:
                        text = pytesseract.image_to_string(img, lang='por')
                        if text.strip():
                            # Extrai dados financeiros da página
                            financeiro = self._parse_financeiro(text)
                            
                            # Limpa o texto para o Excel
                            clean_text = " ".join(text.split())
                            
                            all_data.append({
                                "pagina": page_num + 1,
                                "tipo": "ocr",
                                "valor": financeiro["valor_total"],
                                "data": financeiro["data"],
                                "cnpj": financeiro["cnpj_cpf"],
                                "conteudo": clean_text[:500] + "..." if len(clean_text) > 500 else clean_text
                            })
                            
                            if financeiro["valor_total"]:
                                self._log(f"   [Dados Encontrados] Valor: {financeiro['valor_total']} | Data: {financeiro['data']}")
                    except Exception as e:
                        self._log(f"DEBUG Erro OCR na página {page_num+1}: {e}")
                        raise e
                    
                    if self.progress_callback:
                        self.progress_callback(int(((page_num + 1) / total_pages) * 100))

            doc.close()
            
            if all_data:
                output_file = os.path.join(output_dir, f"{Path(pdf_path).stem}_resultado.xlsx")
                df = pd.DataFrame(all_data)
                method = "OCR" if not has_text else "Nativo"
                save_premium_excel(
                    df, output_file,
                    theme_name=visual_theme,
                    title="CONVERSOR OCR - EXTRAÇÃO DE TEXTO",
                    sheet_name="Texto Extraído",
                    stats=[
                        ("Data da Execução", datetime.now().strftime("%d/%m/%Y %H:%M")),
                        ("Páginas Processadas", str(total_pages)),
                        ("Método", method),
                        ("Total de Caracteres", str(sum(len(d["conteudo"]) for d in all_data))),
                    ]
                )
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "pages": total_pages,
                    "method": method,
                    "text_length": sum(len(d["conteudo"]) for d in all_data)
                }
            else:
                return {"success": False, "error": "Nenhum texto encontrado (nem via OCR)"}
                
        except Exception as e:
            return {"success": False, "error": f"Erro no processamento de PDF: {str(e)}"}
    
    def _process_image(self, image_path: str, output_dir: str, visual_theme: str = "classic_blue") -> Dict:
        """Processa imagem - requer Tesseract"""
        if not self.tesseract_available:
            return {
                "success": False,
                "error": "Tesseract não instalado",
                "hint": "Instale o Tesseract OCR para processar imagens."
            }
        
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            if hasattr(self, "_tessdata_dir"):
                os.environ["TESSDATA_PREFIX"] = self._tessdata_dir
            text = pytesseract.image_to_string(img, lang='por')
            
            financeiro = self._parse_financeiro(text)
            clean_text = " ".join(text.split())
            
            output_file = os.path.join(output_dir, f"{Path(image_path).stem}_resultado.xlsx")
            df = pd.DataFrame([{
                "pagina": 1,
                "tipo": "ocr",
                "valor": financeiro["valor_total"],
                "data": financeiro["data"],
                "cnpj": financeiro["cnpj_cpf"],
                "conteudo": clean_text[:500] + "..." if len(clean_text) > 500 else clean_text
            }])
            save_premium_excel(
                df, output_file,
                theme_name=visual_theme,
                title="CONVERSOR OCR - IMAGEM",
                sheet_name="Texto Extraído",
            )
            
            if financeiro["valor_total"]:
                self._log(f"   [Dados Encontrados] Valor: {financeiro['valor_total']} | Data: {financeiro['data']}")
            
            return {
                "success": True,
                "output_file": output_file,
                "text_length": len(text),
                "valor": financeiro["valor_total"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_tesseract(self, output_dir: str = None) -> Dict:
        """Baixa o Tesseract e prepara para instalação"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if output_dir is None:
            output_dir = os.path.join(base_dir, "bin", "tesseract")
        
        # O instalador precisa ser baixado em uma pasta temporária ou na raiz do bin
        temp_dir = os.path.join(base_dir, "bin")
        os.makedirs(temp_dir, exist_ok=True)
        
        url = "https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe"
        installer_path = os.path.join(temp_dir, "tesseract-setup.exe")
        
        try:
            # Verifica se o arquivo existe e tem tamanho razoável (> 1MB)
            if not os.path.exists(installer_path) or os.path.getsize(installer_path) < 1000000:
                if os.path.exists(installer_path): os.remove(installer_path)
                
                self._log("Baixando Tesseract (aprox. 30MB)...")
                response = requests.get(url, stream=True, timeout=300)
                total = int(response.headers.get('content-length', 0))
                
                downloaded = 0
                with open(installer_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if self.progress_callback and total:
                                self.progress_callback(int((downloaded/total)*100))
            
            return {
                "success": True,
                "installer_path": installer_path,
                "target_dir": output_dir,
                "message": "Download concluído! Iniciando instalação silenciosa..."
            }
        except Exception as e:
            return {"success": False, "error": f"Erro no download: {str(e)}"}

    def install_tesseract_silently(self, installer_path: str, target_dir: str) -> Dict:
        """Executa o instalador do Tesseract em modo silencioso no diretório alvo"""
        import subprocess
        try:
            os.makedirs(target_dir, exist_ok=True)
            
            # RESOLUÇÃO DEFINITIVA PARA ESPAÇOS: Converter para Short Path (8.3)
            # O instalador NSIS do Tesseract não aceita aspas no /D=, mas engasga com espaços.
            # A única forma 100% segura é usar o caminho curto do Windows.
            get_short_path_cmd = f'(New-Object -ComObject Scripting.FileSystemObject).GetFolder("{os.path.dirname(target_dir)}").ShortPath'
            res = subprocess.run(["powershell", "-Command", get_short_path_cmd], capture_output=True, text=True)
            short_base = res.stdout.strip()
            
            if not short_base:
                # Fallback se o PowerShell falhar em pegar o short path
                short_target = target_dir
            else:
                short_target = os.path.join(short_base, os.path.basename(target_dir))

            self._log(f"Instalando motor de OCR (pode levar 1 min)...")
            
            # RESOLUÇÃO PARA O INSTALADOR NÃO ABRIR JANELA:
            # Usar o formato de lista @() no PowerShell para garantir que os argumentos sejam passados separadamente
            ps_cmd = f'$args = @("/S", "/D={short_target}"); Start-Process -FilePath "{installer_path}" -ArgumentList $args -Wait -WindowStyle Hidden'
            
            try:
                subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
            except Exception as e:
                self._log(f"DEBUG: Falha no PowerShell: {e}. Tentando fallback...")
                subprocess.run([installer_path, "/S", f"/D={target_dir}"], capture_output=True, text=True)
            
            # Pequena espera para o disco e verificação
            import time
            time.sleep(3)

            # Após a instalação, vamos procurar o executável em todos os locais possíveis,
            # pois o instalador NSIS do Tesseract costuma ignorar o /D e ir para o Program Files.
            self._setup_tesseract_path() # Re-executa a busca para atualizar tesseract_cmd
            
            import pytesseract
            tesseract_exe = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
            
            if tesseract_exe and os.path.exists(tesseract_exe):
                # Garante o idioma português (Auto-Download)
                tessdata_dir = os.path.join(os.path.dirname(tesseract_exe), "tessdata")
                self._set_tessdata(tessdata_dir)
                
                por_data = os.path.join(tessdata_dir, "por.traineddata")
                if not os.path.exists(por_data):
                    self._log("🌐 Idioma Português não encontrado. Iniciando download...")
                    os.makedirs(tessdata_dir, exist_ok=True)
                    url_por = "https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata"
                    try:
                        resp = requests.get(url_por, timeout=60)
                        if resp.status_code == 200:
                            with open(por_data, "wb") as f:
                                f.write(resp.content)
                            self._log("✅ Idioma Português ('por') instalado com sucesso!")
                        else:
                            self._log(f"⚠️ Erro no download do idioma (Status {resp.status_code})")
                    except Exception as e:
                        self._log(f"⚠️ Erro ao baixar idioma: {e}")

                self.tesseract_available = True
                return {
                    "success": True, 
                    "message": "Tesseract configurado com sucesso!",
                    "exe_path": tesseract_exe
                }
            else:
                return {"success": False, "error": "Falha ao localizar o Tesseract após a instalação."}
        except Exception as e:
            return {"success": False, "error": f"Erro na instalação: {str(e)}"}