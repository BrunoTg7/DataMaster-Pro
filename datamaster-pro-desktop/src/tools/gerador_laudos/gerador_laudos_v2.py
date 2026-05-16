"""
Gerador de Laudos de Conformidade v2.0
Gera PDFs profissionais com cruzamento de dados do Conciliador e Consolidador
Template dinâmico com personalização de cabeçalho, cores e rodapé
"""
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime


class GeradorLaudos:
    """Gera laudos de conformidade em PDF usando ReportLab"""

    def __init__(self):
        pass

    def generate(
        self,
        extrato_file: str,
        notas_file: str,
        output_path: str,
        config: Dict
    ) -> Dict:
        """Gera laudo de conformidade
        
        Args:
            extrato_file: Arquivo do extrato bancário
            notas_file: Arquivo das notas fiscais
            output_path: Caminho do PDF de saída
            config: Configurações do template {company_name, logo_path, header_color, footer_text}
        
        Returns:
            {success, output_path, summary}
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor

            extrato_df = self._load_file(extrato_file)
            notas_df = self._load_file(notas_file)

            conformity_data = self._match_data(extrato_df, notas_df)

            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            styles = getSampleStyleSheet()
            elements = []

            header_color = config.get("header_color", "#d48214")
            text_color = config.get("text_color", "#333333")

            title_style = ParagraphStyle(
                "LaudoTitle",
                parent=styles["Heading1"],
                fontSize=20,
                textColor=HexColor(header_color),
                spaceAfter=10,
                alignment=1
            )

            header_style = ParagraphStyle(
                "Header",
                parent=styles["Normal"],
                fontSize=10,
                textColor=colors.grey,
                alignment=1
            )

            company_name = config.get("company_name", "DataMaster Pro")
            elements.append(Paragraph(company_name.upper(), title_style))
            elements.append(Spacer(1, 0.1 * inch))

            elements.append(Paragraph("LAUDO DE CONFORMIDADE FINANCEIRA", title_style))
            elements.append(Spacer(1, 0.2 * inch))

            date_str = datetime.now().strftime("%d/%m/%Y")
            elements.append(Paragraph(f"Data: {date_str}", header_style))

            if config.get("cnpj"):
                elements.append(Paragraph(f"CNPJ: {config['cnpj']}", header_style))

            if config.get("address"):
                elements.append(Paragraph(config["address"], header_style))

            elements.append(Spacer(1, 0.3 * inch))

            data = [
                ["DATA", "DESCRIÇÃO", "VALOR (R$)", "NF", "STATUS"]
            ]

            total_conforme = 0
            total_nao_conforme = 0

            for item in conformity_data[:50]:
                status = item.get("status", "Pendente")
                status_symbol = "✓" if status == "Conforme" else "✗"

                data.append([
                    item.get("date", "N/A"),
                    item.get("description", "N/A")[:30],
                    f"{item.get('value', 0):.2f}",
                    item.get("nf", "N/A"),
                    status_symbol
                ])

                if status == "Conforme":
                    total_conforme += 1
                else:
                    total_nao_conforme += 1

            table = Table(data, colWidths=[70, 180, 80, 50, 50])

            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor(header_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor(text_color)),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor("#f5f5f5")]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])

            table.setStyle(table_style)
            elements.append(table)

            elements.append(Spacer(1, 0.4 * inch))

            summary_style = ParagraphStyle(
                "Summary",
                parent=styles["Normal"],
                fontSize=11,
                textColor=HexColor(text_color),
                spaceAfter=10
            )

            total_items = total_conforme + total_nao_conforme
            compliance_rate = (total_conforme / total_items * 100) if total_items > 0 else 0

            overall_status = "APROVADO" if compliance_rate >= 80 else "APROVADO PARCIALMENTE" if compliance_rate >= 50 else "REPROVADO"
            status_color = "#22c55e" if overall_status == "APROVADO" else "#eab308" if "PARCIAL" in overall_status else "#ef4444"

            elements.append(Paragraph("<b>RESUMO DA CONFORMIDADE</b>", summary_style))
            elements.append(Spacer(1, 0.1 * inch))

            summary_data = [
                ["Total de Itens", str(total_items)],
                ["Itens em Conformidade", str(total_conforme)],
                ["Itens Pendentes/Inválidos", str(total_nao_conforme)],
                ["Taxa de Conformidade", f"{compliance_rate:.1f}%"],
                ["STATUS FINAL", overall_status]
            ]

            summary_table = Table(summary_data, colWidths=[200, 150])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor(text_color)),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BACKGROUND', (0, -1), (-1, -1), HexColor(status_color)),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))

            elements.append(summary_table)

            elements.append(Spacer(1, 0.5 * inch))

            if config.get("footer_text"):
                footer_style = ParagraphStyle(
                    "Footer",
                    parent=styles["Normal"],
                    fontSize=8,
                    textColor=colors.grey,
                    alignment=1
                )
                elements.append(Paragraph(config["footer_text"], footer_style))

            doc.build(elements)

            return {
                "success": True,
                "output_path": output_path,
                "summary": {
                    "total_items": total_items,
                    "conforme": total_conforme,
                    "nao_conforme": total_nao_conforme,
                    "compliance_rate": round(compliance_rate, 1),
                    "status": overall_status
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _load_file(self, file_path: str) -> pd.DataFrame:
        """Carrega arquivo Excel ou CSV"""
        if file_path.endswith('.xlsx'):
            return pd.read_excel(file_path)
        else:
            return pd.read_csv(file_path, encoding='utf-8')

    def _match_data(self, extrato_df: pd.DataFrame, notas_df: pd.DataFrame) -> List[Dict]:
        """Cruza dados do extrato com notas fiscais"""
        results = []

        for _, extrato_row in extrato_df.iterrows():
            value = extrato_row.get('valor', extrato_row.get('Value', 0))
            date = extrato_row.get('data', extrato_row.get('date', 'N/A'))
            desc = extrato_row.get('descricao', extrato_row.get('description', extrato_row.get('histórico', 'N/A')))

            matched = False

            for _, nota_row in notas_df.iterrows():
                nota_value = nota_row.get('valor', nota_row.get('Value', 0))

                if abs(float(value) - float(nota_value)) < 1:
                    results.append({
                        "date": str(date),
                        "description": str(desc)[:40],
                        "value": float(value),
                        "nf": str(nota_row.get('numero', nota_row.get('nfe', 'N/A'))),
                        "status": "Conforme"
                    })
                    matched = True
                    break

            if not matched:
                results.append({
                    "date": str(date),
                    "description": str(desc)[:40],
                    "value": float(value),
                    "nf": "N/A",
                    "status": "Pendente"
                })

        return results

    def get_default_config(self) -> Dict:
        """Retorna configuração padrão do template"""
        return {
            "company_name": "Nome da Empresa",
            "cnpj": "00.000.000/0001-00",
            "address": "Rua Example, 123 - Cidade - UF",
            "header_color": "#d48214",
            "text_color": "#333333",
            "footer_text": "Documento gerado automaticamente por DataMaster Pro"
        }