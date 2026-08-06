"""
Comissões Pro v2.1 - Sistema de Cálculo e Geração de Relatórios de Comissões
Suporte: % fixa, faixas de desempenho, volume tiers, exceções por produto, ranking de performance

Novidades v2.1:
- Comissão escalonada por volume (volume_tiers)
- PDF com gráfico de barras de comissões por vendedor
- Métricas de performance aprimoradas
"""
import pandas as pd
import os
import re
import io
import tempfile
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils.excel_styler import save_premium_excel


class Comissoes:
    """Motor profissional de cálculo de comissões e geração de relatórios PDF"""

    def __init__(self, log_callback=None, progress_callback=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    def _progress(self, value: int):
        if self.progress_callback:
            self.progress_callback(value)

    # ==================== CARREGAMENTO E NORMALIZAÇÃO ====================

    def _load_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Carrega arquivo CSV ou Excel com detecção automática de encoding"""
        path = Path(file_path)
        try:
            if path.suffix.lower() == ".csv":
                for enc in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                    try:
                        return pd.read_csv(path, encoding=enc, sep=None, engine='python')
                    except Exception:
                        continue
            elif path.suffix.lower() in {".xlsx", ".xls"}:
                return pd.read_excel(path)
        except Exception as e:
            self._log(f"Erro ao carregar {file_path}: {e}")
        return None

    def _normalize_columns(self, df: pd.DataFrame, mapping: Dict) -> pd.DataFrame:
        """Normaliza nomes de colunas para padrões internos com detecção automática"""
        if not mapping:
            mapping = {}
            for col in df.columns:
                c = str(col).lower().strip()
                if any(x in c for x in ["vendedor", "representante", "vendendor", "seller", "colaborador", "atendente", "consultor", "corretor"]):
                    mapping[col] = "vendedor"
                elif any(x in c for x in ["valor", "amount", "total", "montante", "venda", "preço", "price", "revenue"]):
                    mapping[col] = "valor"
                elif any(x in c for x in ["produto", "item", "sku", "descricao", "produto/servico", "mercadoria"]):
                    mapping[col] = "produto"
                elif any(x in c for x in ["data", "date", "dt", "período", "mes"]):
                    mapping[col] = "data"
                elif any(x in c for x in ["cliente", "customer", "comprador", "razao"]):
                    mapping[col] = "cliente"

        df = df.rename(columns=mapping)

        # Limpar valores numéricos
        if 'valor' in df.columns:
            df['valor'] = (
                df['valor'].astype(str)
                .str.replace(r'[^\d,.\-]', '', regex=True)
                .str.replace(',', '.')
            )
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            df = df[df['valor'] > 0]

        if 'vendedor' in df.columns:
            df['vendedor'] = df['vendedor'].fillna('Não identificado').astype(str).str.strip().str.title()

        if 'produto' in df.columns:
            df['produto'] = df['produto'].fillna('N/A').astype(str).str.strip()

        return df

    # ==================== MOTOR DE CÁLCULO ====================

    def calculate_commissions(
        self,
        sales_file: str,
        rules: Dict,
        column_mapping: Dict = None
    ) -> Dict:
        """
        Calcula comissões com base nas regras definidas.

        Regras suportadas:
        - type: "percentage" → % fixa sobre cada venda
        - type: "tiers" → Faixas progressivas sobre o TOTAL acumulado do vendedor
        - type: "volume_tiers" → Escalonamento por VOLUME TOTAL de vendas do vendedor
        - product_exceptions: {nome_produto: taxa%} → Exceções por produto

        Returns:
            Dict com resultados, DataFrame processado, ranking e métricas
        """
        try:
            self._log("📂 Carregando arquivo de vendas...")
            df = self._load_file(sales_file)
            if df is None:
                return {"success": False, "error": "Erro ao carregar arquivo. Verifique o formato."}

            df = self._normalize_columns(df, column_mapping or {})

            if 'vendedor' not in df.columns:
                return {"success": False, "error": "Coluna 'Vendedor' não encontrada na planilha."}
            if 'valor' not in df.columns:
                return {"success": False, "error": "Coluna 'Valor' não encontrada na planilha."}

            self._log(f"✅ {len(df)} vendas carregadas de {df['vendedor'].nunique()} vendedores")
            self._progress(20)

            # Aplicar comissões
            rule_type = rules.get("type", "percentage")
            
            if rule_type == "tiers":
                df = self._apply_tiered_commissions(df, rules)
            elif rule_type == "volume_tiers":
                df = self._apply_volume_tiered_commissions(df, rules)
            else:
                df = self._apply_flat_commissions(df, rules)

            self._progress(60)

            # Gerar ranking de performance
            ranking = self._generate_ranking(df)
            self._progress(80)

            # Métricas executivas
            total_receita = df['valor'].sum()
            total_comissao = df['comissao'].sum()
            total_vendedores = df['vendedor'].nunique()
            ticket_medio_geral = df['valor'].mean()

            self._log(f"💰 Total em comissões: R$ {total_comissao:,.2f}")
            self._progress(100)

            return {
                "success": True,
                "total_vendas": len(df),
                "total_receita": round(total_receita, 2),
                "total_comissao": round(total_comissao, 2),
                "total_vendedores": total_vendedores,
                "ticket_medio": round(ticket_medio_geral, 2),
                "vendedores": total_vendedores,
                "dataframe": df,
                "ranking": ranking
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _apply_flat_commissions(self, df: pd.DataFrame, rules: Dict) -> pd.DataFrame:
        """Aplica comissão de % fixa sobre cada venda"""
        default_rate = rules.get("default_rate", 0) / 100
        product_exceptions = rules.get("product_exceptions", {})

        def calc(row):
            valor = row.get('valor', 0)
            produto = str(row.get('produto', '')).lower()

            # Verificar exceção por produto
            for prod_key, rate in product_exceptions.items():
                if prod_key.lower() in produto:
                    return valor * (rate / 100)

            return valor * default_rate

        df['comissao'] = df.apply(calc, axis=1).round(2)
        df['taxa_aplicada'] = df.apply(
            lambda row: next(
                (rate for prod_key, rate in product_exceptions.items() 
                 if prod_key.lower() in str(row.get('produto', '')).lower()),
                rules.get("default_rate", 0)
            ), axis=1
        )
        return df

    def _apply_tiered_commissions(self, df: pd.DataFrame, rules: Dict) -> pd.DataFrame:
        """
        Aplica comissão por faixas progressivas.
        A faixa é determinada pelo TOTAL ACUMULADO de vendas do vendedor.
        """
        tiers = rules.get("tiers", [])
        default_rate = rules.get("default_rate", 0) / 100
        product_exceptions = rules.get("product_exceptions", {})

        if not tiers:
            return self._apply_flat_commissions(df, rules)

        # Calcular total por vendedor
        vendor_totals = df.groupby('vendedor')['valor'].sum()

        def get_tier_rate(total_vendas):
            """Retorna a taxa da faixa correspondente ao total de vendas"""
            for tier in sorted(tiers, key=lambda t: t.get("min", 0), reverse=True):
                if total_vendas >= tier.get("min", 0):
                    return tier.get("rate", 0) / 100
            return default_rate

        def calc(row):
            valor = row.get('valor', 0)
            vendedor = row.get('vendedor', '')
            produto = str(row.get('produto', '')).lower()

            # Verificar exceção por produto
            for prod_key, rate in product_exceptions.items():
                if prod_key.lower() in produto:
                    return valor * (rate / 100)

            total = vendor_totals.get(vendedor, 0)
            rate = get_tier_rate(total)
            return valor * rate

        df['comissao'] = df.apply(calc, axis=1).round(2)
        
        # Salvar a taxa aplicada para cada vendedor
        df['taxa_aplicada'] = df['vendedor'].map(
            lambda v: get_tier_rate(vendor_totals.get(v, 0)) * 100
        ).round(1)
        
        return df

    def _apply_volume_tiered_commissions(self, df: pd.DataFrame, rules: Dict) -> pd.DataFrame:
        """
        Aplica comissão escalonada por VOLUME TOTAL de vendas do vendedor.
        Diferente do tiers tradicional, aqui o volume é o NUMERO de vendas, não o valor.
        Cada faixa define: min_volume, max_volume, rate (%)
        """
        volume_tiers = rules.get("volume_tiers", [])
        default_rate = rules.get("default_rate", 0) / 100
        product_exceptions = rules.get("product_exceptions", {})

        if not volume_tiers:
            return self._apply_flat_commissions(df, rules)

        # Calcular volume (nº vendas) e valor total por vendedor
        vendor_stats = df.groupby('vendedor').agg(
            volume=('valor', 'count'),
            total_valor=('valor', 'sum')
        ).to_dict('index')

        def get_volume_tier_rate(vendedor: str):
            """Retorna a taxa da faixa de volume correspondente"""
            stats = vendor_stats.get(vendedor, {"volume": 0})
            vol = stats["volume"]
            
            for tier in sorted(volume_tiers, key=lambda t: t.get("min_volume", 0), reverse=True):
                min_v = tier.get("min_volume", 0)
                max_v = tier.get("max_volume", float("inf"))
                if min_v <= vol <= max_v:
                    return tier.get("rate", 0) / 100
            return default_rate

        def calc(row):
            valor = row.get('valor', 0)
            vendedor = row.get('vendedor', '')
            produto = str(row.get('produto', '')).lower()

            # Verificar exceção por produto
            for prod_key, rate in product_exceptions.items():
                if prod_key.lower() in produto:
                    return valor * (rate / 100)

            rate = get_volume_tier_rate(vendedor)
            return valor * rate

        df['comissao'] = df.apply(calc, axis=1).round(2)
        
        # Salvar a taxa aplicada e o volume para cada vendedor
        df['taxa_aplicada'] = df['vendedor'].map(
            lambda v: get_volume_tier_rate(v) * 100
        ).round(1)
        df['volume_vendedor'] = df['vendedor'].map(
            lambda v: vendor_stats.get(v, {}).get("volume", 0)
        )
        
        return df

    # ==================== RANKING E MÉTRICAS ====================

    def _generate_ranking(self, df: pd.DataFrame) -> List[Dict]:
        """Gera ranking completo de performance dos vendedores"""
        if 'vendedor' not in df.columns:
            return []

        summary = df.groupby('vendedor').agg(
            receita=('valor', 'sum'),
            vendas=('valor', 'count'),
            ticket_medio=('valor', 'mean'),
            comissao=('comissao', 'sum'),
            maior_venda=('valor', 'max'),
        ).reset_index()

        summary = summary.sort_values('receita', ascending=False)

        # Calcular métricas de performance
        max_receita = summary['receita'].max() if len(summary) > 0 else 1
        
        ranking = []
        for i, row in enumerate(summary.itertuples(), 1):
            performance_score = min(100, int((row.receita / max_receita) * 100))
            
            # Classificação por medalha
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"#{i}"
            
            ranking.append({
                "posicao": i,
                "medal": medal,
                "vendedor": row.vendedor,
                "receita": round(row.receita, 2),
                "vendas": int(row.vendas),
                "ticket_medio": round(row.ticket_medio, 2),
                "comissao": round(row.comissao, 2),
                "maior_venda": round(row.maior_venda, 2),
                "performance_score": performance_score
            })

        return ranking

    # ==================== GERAÇÃO DE PDF ====================

    def generate_pdf_reports(
        self,
        df: pd.DataFrame,
        output_dir: str,
        company_name: str = "Empresa",
        logo_path: str = None,
        period: str = None
    ) -> Dict:
        """Gera PDF individual profissional para cada vendedor com paralelismo"""
        try:
            os.makedirs(output_dir, exist_ok=True)

            if 'vendedor' not in df.columns:
                return {"success": False, "error": "Coluna 'vendedor' não encontrada"}

            vendedores = df['vendedor'].unique()
            generated = [None] * len(vendedores)
            total = len(vendedores)

            def gerar(idx, vendedor):
                vendor_df = df[df['vendedor'] == vendedor]
                pdf_path = self._generate_single_pdf(
                    vendor_df, vendedor, output_dir, company_name, logo_path, period
                )
                self._log(f"📄 PDF gerado: {vendedor}")
                return idx, pdf_path

            with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, total)) as executor:
                futures = {executor.submit(gerar, i, v): i for i, v in enumerate(vendedores)}
                for future in as_completed(futures):
                    idx, pdf_path = future.result()
                    generated[idx] = pdf_path
                    self._progress(int(((sum(1 for g in generated if g is not None) / total) * 100)))

            generated = [p for p in generated if p is not None]

            return {
                "success": True,
                "total": len(generated),
                "files": generated
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_single_pdf(
        self,
        df: pd.DataFrame,
        vendedor: str,
        output_dir: str,
        company_name: str,
        logo_path: str,
        period: str = None
    ) -> str:
        """Gera um PDF individual profissional para um vendedor"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rl_colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        except ImportError:
            # Fallback sem reportlab
            csv_path = os.path.join(output_dir, f"comissao_{vendedor}.csv")
            df.to_csv(csv_path, index=False)
            return csv_path

        safe_name = re.sub(r'[^\w\s-]', '', vendedor).strip()[:50]
        pdf_path = os.path.join(output_dir, f"comissao_{safe_name}.pdf")
        period_str = period or datetime.now().strftime('%m/%Y')

        doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
        elements = []

        # Estilos profissionais
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Title'],
            fontSize=18, spaceAfter=6, textColor=rl_colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'Subtitle', parent=styles['Normal'],
            fontSize=11, textColor=rl_colors.HexColor('#6b7280'),
            alignment=TA_CENTER, spaceAfter=20
        )
        section_style = ParagraphStyle(
            'Section', parent=styles['Heading2'],
            fontSize=13, textColor=rl_colors.HexColor('#1a1a2e'),
            spaceBefore=15, spaceAfter=8
        )
        normal = styles['Normal']
        normal.fontSize = 10

        # ===== CABEÇALHO =====
        elements.append(Paragraph(f"{company_name}", title_style))
        elements.append(Paragraph(f"Relatório de Comissão Individual — Período: {period_str}", subtitle_style))
        elements.append(Spacer(1, 10))

        # ===== DADOS DO VENDEDOR =====
        elements.append(Paragraph("Dados do Colaborador", section_style))

        total_vendas = len(df)
        total_receita = df['valor'].sum()
        total_comissao = df['comissao'].sum()
        ticket_medio = df['valor'].mean()
        maior_venda = df['valor'].max()
        taxa_media = (total_comissao / total_receita * 100) if total_receita > 0 else 0

        info_data = [
            ['Vendedor:', vendedor, 'Data de Emissão:', datetime.now().strftime('%d/%m/%Y')],
            ['Total de Vendas:', str(total_vendas), 'Ticket Médio:', f'R$ {ticket_medio:,.2f}'],
            ['Receita Gerada:', f'R$ {total_receita:,.2f}', 'Maior Venda:', f'R$ {maior_venda:,.2f}'],
        ]

        info_table = Table(info_data, colWidths=[3*cm, 5.5*cm, 3.5*cm, 5.5*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), rl_colors.HexColor('#374151')),
            ('TEXTCOLOR', (2, 0), (2, -1), rl_colors.HexColor('#374151')),
            ('TEXTCOLOR', (1, 0), (1, -1), rl_colors.HexColor('#111827')),
            ('TEXTCOLOR', (3, 0), (3, -1), rl_colors.HexColor('#111827')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 15))

        # ===== RESUMO FINANCEIRO =====
        elements.append(Paragraph("Resumo Financeiro", section_style))

        highlight_color = rl_colors.HexColor('#d48214')
        bg_light = rl_colors.HexColor('#fef3e2')

        finance_data = [
            ['Receita Total', f'R$ {total_receita:,.2f}'],
            ['Taxa Média Aplicada', f'{taxa_media:.1f}%'],
            ['COMISSÃO A RECEBER', f'R$ {total_comissao:,.2f}'],
        ]

        finance_table = Table(finance_data, colWidths=[10*cm, 7*cm])
        finance_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), highlight_color),
            ('BACKGROUND', (0, -1), (-1, -1), bg_light),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, rl_colors.HexColor('#e5e7eb')),
            ('LINEBELOW', (0, -1), (-1, -1), 1.5, highlight_color),
        ]))
        elements.append(finance_table)
        elements.append(Spacer(1, 15))

        # ===== DETALHAMENTO DE VENDAS =====
        elements.append(Paragraph("Detalhamento das Vendas", section_style))

        # Montar cabeçalho da tabela
        has_produto = 'produto' in df.columns
        has_data = 'data' in df.columns
        has_cliente = 'cliente' in df.columns

        header = ['#']
        if has_data: header.append('Data')
        if has_produto: header.append('Produto')
        if has_cliente: header.append('Cliente')
        header.extend(['Valor', 'Taxa', 'Comissão'])

        table_data = [header]
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            line = [str(idx)]
            if has_data: line.append(str(row.get('data', ''))[:10])
            if has_produto: line.append(str(row.get('produto', ''))[:30])
            if has_cliente: line.append(str(row.get('cliente', ''))[:25])
            line.append(f"R$ {row['valor']:,.2f}")
            line.append(f"{row.get('taxa_aplicada', 0):.1f}%")
            line.append(f"R$ {row['comissao']:,.2f}")
            table_data.append(line)

            # Limitar para não estourar o PDF
            if idx >= 100:
                table_data.append(['', '', '...', '', '', ''])
                break

        # Calcular larguras dinamicamente
        num_cols = len(header)
        available_width = 17.5 * cm
        col_widths = [available_width / num_cols] * num_cols

        detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        detail_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (-3, 1), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, rl_colors.HexColor('#e5e7eb')),
            # Alternating rows
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor('#f9fafb')]),
        ]))
        elements.append(detail_table)
        elements.append(Spacer(1, 20))

        # ===== RODAPÉ =====
        footer_style = ParagraphStyle(
            'Footer', parent=styles['Normal'],
            fontSize=8, textColor=rl_colors.HexColor('#9ca3af'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Documento gerado automaticamente por DataMaster Pro em {datetime.now().strftime('%d/%m/%Y às %H:%M')}. "
            f"Este relatório não possui valor fiscal.",
            footer_style
        ))

        doc.build(elements)
        return pdf_path

    # ==================== GERAÇÃO DE PDF COM GRÁFICO ====================

    def _generate_chart_image(self, commission_data: List[Dict]) -> Optional[str]:
        """Gera gráfico de barras de comissões por vendedor usando matplotlib"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 5))
            
            sellers = [d['vendedor'][:20] for d in commission_data[:10]]  # Top 10
            commissions = [d['comissao'] for d in commission_data[:10]]
            
            colors_list = ['#1a56db', '#d48214', '#059669', '#dc2626', '#7c3aed',
                          '#ea580c', '#0891b2', '#4f46e5', '#c026d3', '#65a30d']
            
            bars = ax.barh(sellers, commissions, color=colors_list[:len(sellers)])
            ax.set_xlabel("Comissão (R$)", fontsize=10)
            ax.set_title("Top Vendedores por Comissão", fontsize=12, fontweight='bold')
            ax.invert_yaxis()
            
            for bar, val in zip(bars, commissions):
                ax.text(bar.get_width() + max(commissions) * 0.01, 
                       bar.get_y() + bar.get_height()/2,
                       f"R$ {val:,.2f}", va='center', fontsize=8)
            
            plt.tight_layout()
            
            chart_path = os.path.join(tempfile.gettempdir(), "commission_chart.png")
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            return chart_path
        except ImportError:
            self._log("⚠️ matplotlib não instalado. Pulando gráfico no PDF.")
            return None

    def generate_pdf_with_chart(
        self,
        ranking: List[Dict],
        output_path: str,
        company_name: str = "Empresa",
        period: str = None
    ) -> Dict:
        """Gera PDF consolidado com gráfico de barras de comissões"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rl_colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        except ImportError:
            return {"success": False, "error": "reportlab não instalado."}

        if not ranking:
            return {"success": False, "error": "Ranking vazio."}

        period_str = period or datetime.now().strftime('%m/%Y')
        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Title'],
            fontSize=18, spaceAfter=6, textColor=rl_colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'Subtitle', parent=styles['Normal'],
            fontSize=11, textColor=rl_colors.HexColor('#6b7280'),
            alignment=TA_CENTER, spaceAfter=20
        )

        # Cabecalho
        elements.append(Paragraph(f"{company_name}", title_style))
        elements.append(Paragraph(f"Relatório Consolidado de Comissões — {period_str}", subtitle_style))
        elements.append(Spacer(1, 10))

        # Gráfico
        chart_path = self._generate_chart_image(ranking)
        if chart_path and os.path.exists(chart_path):
            elements.append(RLImage(chart_path, width=16*cm, height=8*cm))
            elements.append(Spacer(1, 15))

        # Tabela de ranking
        header = ['Posição', 'Vendedor', 'Receita', 'Vendas', 'Comissão']
        table_data = [header]
        for item in ranking:
            table_data.append([
                item['medal'],
                item['vendedor'],
                f"R$ {item['receita']:,.2f}",
                str(item['vendas']),
                f"R$ {item['comissao']:,.2f}",
            ])

        rank_table = Table(table_data, colWidths=[2*cm, 5*cm, 3.5*cm, 2*cm, 3.5*cm])
        rank_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (-3, 1), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor('#f9fafb')]),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, rl_colors.HexColor('#e5e7eb')),
        ]))
        elements.append(rank_table)

        # Rodapé
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                       textColor=rl_colors.HexColor('#9ca3af'), alignment=TA_CENTER)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            f"Documento gerado automaticamente por DataMaster Pro em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.",
            footer_style
        ))

        doc.build(elements)
        
        # Limpar temporário
        if chart_path and os.path.exists(chart_path):
            os.remove(chart_path)
        
        return {"success": True, "output_path": output_path}

    # ==================== EXPORTAÇÃO ====================

    def export_summary(self, df: pd.DataFrame, output_path: str, visual_theme: str = "classic_blue") -> Dict:
        """Exporta resumo consolidado de comissões para Excel/CSV"""
        try:
            if 'vendedor' not in df.columns:
                return {"success": False, "error": "Coluna vendedor não encontrada"}

            summary = df.groupby('vendedor').agg(
                receita=('valor', 'sum'),
                vendas=('valor', 'count'),
                ticket_medio=('valor', 'mean'),
                comissao=('comissao', 'sum'),
                maior_venda=('valor', 'max'),
            ).reset_index()

            summary.columns = ['Vendedor', 'Receita Total', 'Nº Vendas', 'Ticket Médio', 'Comissão', 'Maior Venda']
            summary['% Comissão'] = (summary['Comissão'] / summary['Receita Total'] * 100).round(2)
            summary = summary.sort_values('Receita Total', ascending=False)

            # Adicionar linha de totais
            totals = pd.DataFrame([{
                'Vendedor': 'TOTAL',
                'Receita Total': summary['Receita Total'].sum(),
                'Nº Vendas': summary['Nº Vendas'].sum(),
                'Ticket Médio': summary['Receita Total'].sum() / max(summary['Nº Vendas'].sum(), 1),
                'Comissão': summary['Comissão'].sum(),
                'Maior Venda': summary['Maior Venda'].max(),
                '% Comissão': (summary['Comissão'].sum() / max(summary['Receita Total'].sum(), 1) * 100)
            }])
            summary = pd.concat([summary, totals], ignore_index=True)

            ext = Path(output_path).suffix.lower()
            if ext == ".csv":
                summary.to_csv(output_path, index=False, encoding='utf-8-sig')
            else:
                total_receita = summary.loc[summary['Vendedor'] == 'TOTAL', 'Receita Total'].values[0]
                total_comissao = summary.loc[summary['Vendedor'] == 'TOTAL', 'Comissão'].values[0]
                save_premium_excel(
                    summary, output_path,
                    theme_name=visual_theme,
                    title="RELATÓRIO DE COMISSÕES",
                    sheet_name="Comissões",
                    stats=[
                        ("Data da Execução", datetime.now().strftime("%d/%m/%Y %H:%M")),
                        ("Total de Vendedores", str(len(summary) - 1)),
                        ("Receita Total", f"R$ {total_receita:,.2f}"),
                        ("Comissão Total", f"R$ {total_comissao:,.2f}"),
                    ]
                )

            return {"success": True, "output_path": output_path, "total_vendedores": len(summary) - 1}
        except Exception as e:
            return {"success": False, "error": str(e)}