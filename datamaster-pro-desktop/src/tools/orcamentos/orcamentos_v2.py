"""
Orçamentos v2.0 - Otimizado para máxima velocidade
Geração de PDFs profissionais em massa com reportlab puro
"""
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Orcamentos:
    """Geração ultra-rápida de PDFs profissionais"""
    
    def __init__(self, company: str = "DataMaster Pro"):
        self.company = company
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup de estilos uma única vez"""
        self.title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#d48214"),
            spaceAfter=12
        )
        
        self.header_style = ParagraphStyle(
            "CustomHeader",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=6
        )
    
    def generate_bulk(self, data_file: str, output_dir: str, template: Optional[Dict] = None) -> Dict:
        """Gera múltiplos PDFs a partir de CSV/Excel
        
        Args:
            data_file: Arquivo com dados (.csv ou .xlsx)
            output_dir: Diretório de saída
            template: Dict com layout personalizado
        
        Returns:
            {success: bool, generated: int, errors: [...]}
        """
        try:
            # Carregar dados
            if data_file.endswith(".xlsx"):
                df = pd.read_excel(data_file)
            else:
                df = pd.read_csv(data_file)
            
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            generated = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    pdf_name = f"orcamento_{row.get('numero', idx)}.pdf"
                    pdf_path = output_path / pdf_name
                    
                    self._create_single(row, pdf_path)
                    generated += 1
                except Exception as e:
                    errors.append({"row": idx, "error": str(e)})
            
            return {
                "success": True,
                "total": len(df),
                "generated": generated,
                "output_dir": str(output_path),
                "errors": errors if errors else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_single(self, data: pd.Series, output_path: Path):
        """Cria um PDF individual"""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        elements = []
        
        # Título
        elements.append(Paragraph(f"ORÇAMENTO #{data.get('numero', '001')}", self.title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Cabeçalho
        elements.append(Paragraph(f"<b>Empresa:</b> {self.company}", self.header_style))
        elements.append(Paragraph(f"<b>Data:</b> {data.get('data', 'N/A')}", self.header_style))
        elements.append(Paragraph(f"<b>Cliente:</b> {data.get('cliente', 'N/A')}", self.header_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabela de itens
        items_data = [["Descrição", "Qtd", "Valor Unit.", "Total"]]
        
        # Parse itens (esperado: coluna JSON ou texto separado)
        items = self._parse_items(data.get("itens", ""))
        for item in items:
            items_data.append([
                item.get("desc", ""),
                str(item.get("qtd", 1)),
                f"R$ {item.get('valor', 0):.2f}",
                f"R$ {float(item.get('qtd', 1)) * float(item.get('valor', 0)):.2f}"
            ])
        
        # Rodapé com total
        total = sum(float(item.get('qtd', 1)) * float(item.get('valor', 0)) for item in items)
        items_data.append(["", "", "<b>TOTAL:</b>", f"<b>R$ {total:.2f}</b>"])
        
        # Tabela
        table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1.2*inch, 1*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d48214")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Observações
        obs = data.get("observacoes", "")
        if obs:
            elements.append(Paragraph(f"<b>Observações:</b> {obs}", self.styles["Normal"]))
        
        # Gerar PDF
        doc.build(elements)
        logger.info(f"PDF criado: {output_path}")
    
    def _parse_items(self, items_str: str) -> List[Dict]:
        """Parse de itens (suporta JSON ou CSV simples)"""
        if not items_str:
            return []
        
        try:
            import json
            return json.loads(items_str)
        except:
            # Fallback: CSV simples (desc|qtd|valor)
            items = []
            for line in str(items_str).split(";"):
                parts = line.split("|")
                if len(parts) >= 3:
                    items.append({
                        "desc": parts[0].strip(),
                        "qtd": float(parts[1].strip()),
                        "valor": float(parts[2].strip())
                    })
            return items
    
    def generate_single(self, output_path: str, **kwargs) -> bool:
        """Gera um PDF individual com dados customizados"""
        try:
            self._create_single(pd.Series(kwargs), Path(output_path))
            return True
        except:
            return False
