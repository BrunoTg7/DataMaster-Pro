"""
Conversor OCR Enterprise v3.0 - PaddleOCR based
- Layout Analysis (detecção de tabelas, colunas, parágrafos)
- Extração estruturada: texto + bounding boxes + estrutura de tabela
- Zero binários externos (modelos ONNX internos)
- Suporte nativo a PT-BR
- Batch processing com ThreadPoolExecutor
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging
import json
import tempfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger(__name__)


@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: List[List[int]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    block_type: str  # "text", "table", "title", "header", "footer"


@dataclass
class TableResult:
    headers: List[str]
    rows: List[List[str]]
    bbox: List[List[int]]
    confidence: float


class PaddleOCREngine:
    """
    Wrapper enterprise para PaddleOCR (PP-OCRv4).
    Inicialização lazy (modelos pesados ~50MB).
    """
    
    def __init__(self, use_gpu: bool = False, lang: str = "pt", 
                 det_model_dir: str = None, rec_model_dir: str = None,
                 table_model_dir: str = None):
        self.use_gpu = use_gpu
        self.lang = lang
        self._model_dirs = {
            "det": det_model_dir,
            "rec": rec_model_dir,
            "table": table_model_dir
        }
        self._ocr = None
        self._table_engine = None
    
    def _init_ocr(self):
        if self._ocr is not None:
            return
        try:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False,
                det_model_dir=self._model_dirs["det"],
                rec_model_dir=self._model_dirs["rec"],
                enable_mkldnn=not self.use_gpu,  # Otimização Intel CPU
                cpu_threads=os.cpu_count() or 4
            )
            log.info("PaddleOCR inicializado (det+rec+cls)")
        except ImportError:
            raise RuntimeError("paddleocr não instalado: pip install paddleocr")
    
    def _init_table_engine(self):
        if self._table_engine is not None:
            return
        try:
            from paddleocr import PPStructure
            self._table_engine = PPStructure(
                use_gpu=self.use_gpu,
                show_log=False,
                table=True,
                ocr=True,
                lang=self.lang
            )
            log.info("PaddleOCR Table Engine inicializado")
        except ImportError:
            raise RuntimeError("paddleocr[table] não instalado: pip install 'paddleocr[table]'")
    
    def process_image(self, image_path: str, extract_tables: bool = True) -> Dict:
        """Processa uma imagem - retorna texto + tabelas estruturadas"""
        self._init_ocr()
        
        # Carregar imagem
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Não foi possível ler imagem: {image_path}")
        
        # OCR geral (texto + layout)
        ocr_result = self._ocr.ocr(img, cls=True)
        
        # Extrair blocos de texto
        text_blocks = []
        full_text_parts = []
        
        if ocr_result and ocr_result[0]:
            for line in ocr_result[0]:
                bbox, (text, conf) = line
                text_blocks.append(OCRResult(
                    text=text,
                    confidence=conf,
                    bbox=bbox,
                    block_type="text"
                ))
                full_text_parts.append(text)
        
        result = {
            "full_text": "\n".join(full_text_parts),
            "blocks": [asdict(b) for b in text_blocks],
            "tables": [],
            "page_dims": {"width": img.shape[1], "height": img.shape[0]}
        }
        
        # Extração de tabelas (se solicitado)
        if extract_tables:
            self._init_table_engine()
            table_result = self._table_engine(img)
            tables = []
            for region in table_result:
                if region.get("type") == "table":
                    res = region.get("res", {})
                    html = res.get("html", "")
                    if html:
                        table = self._parse_table_html(html, region.get("bbox", []))
                        if table:
                            tables.append(asdict(table))
            result["tables"] = tables
        
        return result
    
    def _parse_table_html(self, html: str, bbox: List) -> Optional[TableResult]:
        """Converte HTML da tabela PaddleOCR para estrutura Python"""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table")
            if not table:
                return None
            
            headers = []
            rows = []
            
            # Cabeçalho
            thead = table.find("thead")
            if thead:
                for th in thead.find_all("th"):
                    headers.append(th.get_text(strip=True))
            
            # Linhas
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                row = []
                for td in tr.find_all(["td", "th"]):
                    row.append(td.get_text(strip=True))
                if row and row != headers:
                    rows.append(row)
            
            # Confiança média das células (aproximada)
            confidences = []
            for td in table.find_all(["td", "th"]):
                # PaddleOCR não expõe confiança por célula no HTML
                # Usar heurística: células não vazias = alta confiança
                confidences.append(0.9 if td.get_text(strip=True) else 0.3)
            
            avg_conf = np.mean(confidences) if confidences else 0.8
            
            return TableResult(
                headers=headers,
                rows=rows,
                bbox=bbox,
                confidence=avg_conf
            )
        except Exception as e:
            log.warning(f"Falha ao parsear tabela HTML: {e}")
            return None
    
    def process_pdf(self, pdf_path: str, extract_tables: bool = True, 
                    max_workers: int = 4) -> Dict:
        """Processa PDF multi-página com paralelismo"""
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        all_text = []
        all_blocks = []
        all_tables = []
        
        # Converter páginas para imagens (paralelo)
        def page_to_image(page_num: int) -> tuple:
            page = doc[page_num]
            # 2x zoom para melhor OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            temp_dir = Path(tempfile.gettempdir()) / "paddleocr_cache"
            temp_dir.mkdir(exist_ok=True)
            img_path = temp_dir / f"{Path(pdf_path).stem}_p{page_num}.png"
            pix.save(str(img_path))
            return page_num, str(img_path)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(page_to_image, i): i for i in range(len(doc))}
            
            for future in as_completed(futures):
                page_num, img_path = future.result()
                try:
                    result = self.process_image(img_path, extract_tables=True)
                    all_text.append(f"--- PÁGINA {page_num + 1} ---\n{result['full_text']}")
                    all_blocks.extend(result['blocks'])
                    for t in result['tables']:
                        t['page'] = page_num + 1
                        all_tables.append(t)
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)
        
        doc.close()
        
        return {
            "full_text": "\n\n".join(all_text),
            "blocks": all_blocks,
            "tables": all_tables,
            "total_pages": len(doc)
        }


# ============================================================
# INTEGRAÇÃO NO CONVERSOR OCR EXISTENTE
# ============================================================

class ConversorOCRV3:
    """
    Conversor OCR v3.0 Enterprise - PaddleOCR based.
    Mantém interface compatível: process_file, process_multiple, get_status
    """
    
    def __init__(self, progress_callback=None, log_callback=None, use_gpu=False):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.engine = PaddleOCREngine(use_gpu=use_gpu, lang="pt")
        self._log("Conversor OCR v3.0 (PaddleOCR) inicializado")
    
    def _log(self, msg: str):
        log.info(msg)
        if self.log_callback:
            self.log_callback(msg)
    
    def get_status(self) -> Dict:
        return {
            "engine": "PaddleOCR v2.7+ (PP-OCRv4)",
            "languages": ["pt", "en", "multi"],
            "features": ["text_detection", "text_recognition", "layout_analysis", "table_extraction"],
            "gpu_enabled": self.engine.use_gpu,
            "version": "3.0"
        }
    
    def process_file(self, file_path: str, output_dir: str, 
                     extract_tables: bool = True, visual_theme: str = "classic_blue") -> Dict:
        try:
            ext = Path(file_path).suffix.lower()
            
            if ext == ".pdf":
                result = self.engine.process_pdf(file_path, extract_tables)
                method = "PaddleOCR_PDF"
            elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]:
                result = self.engine.process_image(file_path, extract_tables)
                method = "PaddleOCR_Image"
            else:
                return {"success": False, "error": "Tipo não suportado"}
            
            # Salvar resultado estruturado
            output_file = os.path.join(output_dir, f"{Path(file_path).stem}_ocr.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # Também gerar Excel premium (compatibilidade)
            self._export_excel(result, file_path, output_dir, visual_theme)
            
            return {
                "success": True,
                "output_file": output_file,
                "method": method,
                "pages": result.get("total_pages", 1),
                "tables_found": len(result.get("tables", [])),
                "text_length": len(result.get("full_text", ""))
            }
        except Exception as e:
            self._log(f"Erro OCR: {e}")
            return {"success": False, "error": str(e)}
    
    def _export_excel(self, result: Dict, original_path: str, output_dir: str, theme: str):
        """Exporta texto + tabelas para Excel premium (usa save_premium_excel existente)"""
        from src.utils.excel_styler import save_premium_excel
        import pandas as pd
        from datetime import datetime
        
        # Aba 1: Texto completo
        df_text = pd.DataFrame([{"pagina": 1, "conteudo": result["full_text"][:50000]}])
        
        # Abas de tabelas (uma por tabela)
        tables_data = {}
        for i, table in enumerate(result.get("tables", [])):
            if table.get("rows"):
                headers = table.get("headers", [f"Col_{j}" for j in range(len(table["rows"][0]))])
                df_table = pd.DataFrame(table["rows"], columns=headers)
                tables_data[f"Tabela_{i+1}_p{table.get('page',1)}"] = df_table
        
        output_file = os.path.join(output_dir, f"{Path(original_path).stem}_resultado.xlsx")
        
        if tables_data:
            from openpyxl import Workbook
            wb = Workbook()
            ws_text = wb.active
            ws_text.title = "Texto_Extraido"
            for r in df_text.itertuples(index=False):
                ws_text.append(list(r))
            
            for name, df in tables_data.items():
                ws = wb.create_sheet(title=name[:31])
                for r in df.itertuples(index=False):
                    ws.append(list(r))
            wb.save(output_file)
        else:
            save_premium_excel(df_text, output_file, theme_name=theme,
                             title="CONVERSOR OCR v3 - PADDLEOCR",
                             stats=[
                                 ("Data da Execução", datetime.now().strftime("%d/%m/%Y %H:%M")),
                                 ("Páginas Processadas", str(result.get("total_pages", 1))),
                                 ("Tabelas Encontradas", str(len(result.get("tables", [])))),
                                 ("Total de Caracteres", str(len(result.get("full_text", "")))),
                             ])

    def process_multiple(self, files: List[str], output_dir: str, 
                         extract_tables: bool = True, visual_theme: str = "classic_blue") -> Dict:
        results = []
        processed = 0
        
        for file_path in files:
            try:
                result = self.process_file(file_path, output_dir, extract_tables, visual_theme)
                results.append({"file": file_path, "result": result})
                if result.get("success"):
                    processed += 1
            except Exception as e:
                results.append({"file": file_path, "result": {"success": False, "error": str(e)}})
            
            if self.progress_callback:
                self.progress_callback(int((processed / len(files)) * 100))
        
        return {
            "total": len(files),
            "processed": processed,
            "results": results
        }
    
    def preview_changes(self, df: pd.DataFrame, field: str, transformation: str) -> List[Dict]:
        # Não aplicável para OCR - mantido para compatibilidade
        return []


# ============================================================
# EXEMPLO DE USO STANDALONE
# ============================================================

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    conversor = ConversorOCRV3(log_callback=print)
    print(conversor.get_status())