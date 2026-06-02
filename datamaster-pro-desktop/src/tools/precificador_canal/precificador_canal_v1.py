"""
Precificador por Canal de Venda v1.0
Motor de cálculo reverso de preços para múltiplos marketplaces.
Garante a margem líquida desejada considerando: comissão, taxa fixa,
imposto Simples Nacional e frete embutido.
"""
import logging
import pandas as pd
from typing import Dict, Callable, Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

log = logging.getLogger(__name__)


class PrecificadorCanal:
    """
    Calcula o preço de venda ideal por canal (ML, Shopee, Amazon, Magalu)
    para garantir a margem líquida desejada pelo lojista.
    """

    # Tabela de regras dos marketplaces (atualizada 2025)
    CANAIS = {
        "Mercado Livre": {
            "comissao_pct": 0.16,
            "taxa_fixa": 6.00,
            "frete_gratis_min": 79.00,   # acima deste valor, frete grátis obrigatório
            "custo_frete_medio": 15.00,  # estimativa de custo de frete grátis
            "emoji": "🛒",
        },
        "Shopee": {
            "comissao_pct": 0.20,
            "taxa_fixa": 3.00,
            "frete_gratis_min": 0.0,
            "custo_frete_medio": 0.0,    # Shopee subsidia o frete
            "emoji": "🍊",
        },
        "Amazon": {
            "comissao_pct": 0.15,
            "taxa_fixa": 2.00,
            "frete_gratis_min": 0.0,
            "custo_frete_medio": 0.0,
            "emoji": "📦",
        },
        "Magalu": {
            "comissao_pct": 0.18,
            "taxa_fixa": 5.00,
            "frete_gratis_min": 0.0,
            "custo_frete_medio": 0.0,
            "emoji": "🛍️",
        },
    }

    def __init__(self, log_callback: Callable = None, progress_callback: Callable = None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback

    def _log(self, message: str):
        log.info(message)
        if self.log_callback:
            self.log_callback(message)

    def _progress(self, pct: int):
        if self.progress_callback:
            self.progress_callback(pct)

    # ------------------------------------------------------------------
    # Cálculo Reverso: dado o custo + margem desejada, acha o preço de venda
    # ------------------------------------------------------------------
    def _preco_por_canal(
        self,
        custo: float,
        imposto_pct: float,
        margem_desejada_pct: float,
        canal_info: dict,
    ) -> dict:
        """
        Fórmula de cálculo reverso:
            Preço = (CustoBase + TaxaFixa + FreteEmbutido)
                    / (1 - Comissão% - Margem% - Imposto%)

        Onde CustoBase = custo bruto sem imposto (o imposto é sobre o preço de venda).
        """
        comissao = canal_info["comissao_pct"]
        taxa_fixa = canal_info["taxa_fixa"]
        frete_embutido = canal_info.get("custo_frete_medio", 0.0)

        # Percentual total que "sai" do preço de venda
        desconto_total = comissao + (margem_desejada_pct / 100) + (imposto_pct / 100)

        if desconto_total >= 1.0:
            return {"preco": None, "margem_real": None, "erro": "Margem inviável"}

        # Preço de venda sugerido
        preco = (custo + taxa_fixa + frete_embutido) / (1 - desconto_total)

        # Verificar se aciona custo de frete grátis no ML
        frete_min = canal_info.get("frete_gratis_min", 0.0)
        if frete_min > 0 and preco >= frete_min and frete_embutido == 0:
            # Recalcular com frete embutido
            frete_embutido = canal_info.get("custo_frete_medio", 15.0)
            preco = (custo + taxa_fixa + frete_embutido) / (1 - desconto_total)

        # Calcular margem real
        comissao_valor = preco * comissao
        imposto_valor = preco * (imposto_pct / 100)
        lucro_liquido = preco - custo - comissao_valor - taxa_fixa - frete_embutido - imposto_valor
        margem_real = (lucro_liquido / preco) * 100 if preco > 0 else 0

        return {
            "preco": round(preco, 2),
            "margem_real_pct": round(margem_real, 2),
            "lucro_liquido": round(lucro_liquido, 2),
            "comissao_valor": round(comissao_valor, 2),
            "taxa_fixa": round(taxa_fixa, 2),
            "frete_embutido": round(frete_embutido, 2),
            "imposto_valor": round(imposto_valor, 2),
            "erro": None,
        }

    # ------------------------------------------------------------------
    # Processamento em lote via planilha
    # ------------------------------------------------------------------
    def calcular_planilha(
        self,
        df: pd.DataFrame,
        margem_desejada_pct: float = 20.0,
        canais_selecionados: list = None,
        output_path: str = None,
    ) -> dict:
        """
        Processa um DataFrame com colunas:
          - produto (str) — nome do produto
          - custo (float) — custo de aquisição
          - imposto_pct (float) — % Simples Nacional (ex: 6.0 para 6%)

        Retorna dict com sucesso, DataFrame de resultados e caminho do Excel.
        """
        try:
            canais = canais_selecionados or list(self.CANAIS.keys())
            self._log(f"Iniciando cálculo para {len(df)} produto(s) em {len(canais)} canal(is)...")

            # Normalizar colunas
            df_norm = self._normalizar_df(df)
            if df_norm is None:
                return {"success": False, "error": "Colunas obrigatórias não encontradas. Use: produto, custo, imposto_pct"}

            results = []
            total = len(df_norm)
            for i, row in df_norm.iterrows():
                produto = str(row.get("produto", f"Produto {i+1}"))
                custo = float(row.get("custo", 0))
                imposto_pct = float(row.get("imposto_pct", 6.0))

                result_row = {
                    "Produto": produto,
                    "Custo (R$)": custo,
                    "Imposto Simples (%)": imposto_pct,
                    "Margem Desejada (%)": margem_desejada_pct,
                }

                for canal_nome in canais:
                    info = self.CANAIS.get(canal_nome)
                    if not info:
                        continue
                    calc = self._preco_por_canal(custo, imposto_pct, margem_desejada_pct, info)
                    emoji = info["emoji"]
                    if calc["erro"]:
                        result_row[f"{emoji} {canal_nome} - Preço"] = "INVIÁVEL"
                        result_row[f"{emoji} {canal_nome} - Margem Real (%)"] = "-"
                        result_row[f"{emoji} {canal_nome} - Lucro Líquido (R$)"] = "-"
                    else:
                        result_row[f"{emoji} {canal_nome} - Preço"] = calc["preco"]
                        result_row[f"{emoji} {canal_nome} - Margem Real (%)"] = calc["margem_real_pct"]
                        result_row[f"{emoji} {canal_nome} - Lucro Líquido (R$)"] = calc["lucro_liquido"]

                results.append(result_row)
                self._progress(int(((i + 1) / total) * 80))

            result_df = pd.DataFrame(results)
            self._log(f"{len(result_df)} produtos processados.")

            # Gerar Excel estilizado
            if not output_path:
                from datetime import datetime
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                import os, sys
                sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
                import config
                output_path = os.path.join(config.OUTPUT_DIR, f"precificacao_{ts}.xlsx")

            self._save_excel(result_df, output_path, margem_desejada_pct, canais)
            self._progress(100)

            self._log(f"Relatório salvo em: {output_path}")
            return {
                "success": True,
                "rows": len(result_df),
                "output_path": output_path,
                "dataframe": result_df,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _normalizar_df(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Normaliza nomes de colunas para o padrão esperado."""
        col_map = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ["produto", "descricao", "nome", "item", "description"]:
                col_map[col] = "produto"
            elif col_lower in ["custo", "custo_aquisicao", "preco_custo", "cost", "valor_custo"]:
                col_map[col] = "custo"
            elif col_lower in ["imposto", "imposto_pct", "simples", "simples_nacional", "aliquota", "tax_pct"]:
                col_map[col] = "imposto_pct"

        df_norm = df.rename(columns=col_map)

        if "produto" not in df_norm.columns:
            df_norm["produto"] = [f"Produto {i+1}" for i in range(len(df_norm))]
        if "custo" not in df_norm.columns:
            return None
        if "imposto_pct" not in df_norm.columns:
            df_norm["imposto_pct"] = 6.0  # Simples Nacional padrão

        return df_norm[["produto", "custo", "imposto_pct"]]

    # ------------------------------------------------------------------
    # Cálculo manual (produto único)
    # ------------------------------------------------------------------
    def calcular_produto_unico(
        self,
        produto: str,
        custo: float,
        imposto_pct: float,
        margem_desejada_pct: float,
        canais_selecionados: list = None,
    ) -> dict:
        """Para cálculo rápido de um único produto sem planilha."""
        df = pd.DataFrame([{"produto": produto, "custo": custo, "imposto_pct": imposto_pct}])
        return self.calcular_planilha(df, margem_desejada_pct, canais_selecionados)

    # ------------------------------------------------------------------
    # Exportação Excel Premium
    # ------------------------------------------------------------------
    def _save_excel(self, df: pd.DataFrame, output_path: str, margem: float, canais: list):
        wb = Workbook()
        ws = wb.active
        ws.title = "Precificação por Canal"

        # Paleta de cores
        HEADER_BG = "1C1C1E"
        HEADER_FG = "FFFFFF"
        SUB_BG = "2C2C2E"
        SUB_FG = "F5A623"
        ZEBRA = "F9F9F9"
        BORDER_COLOR = "D1D1D6"
        GREEN = "D4EDDA"
        ORANGE = "FFF3CD"
        RED = "F8D7DA"

        thin = Side(style="thin", color=BORDER_COLOR)
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # === CABEÇALHO DA PLANILHA ===
        ws.merge_cells("A1:C1")
        title_cell = ws["A1"]
        title_cell.value = f"📊 DataMaster Pro — Simulador de Precificação por Canal"
        title_cell.font = Font(name="Calibri", size=14, bold=True, color=HEADER_FG)
        title_cell.fill = PatternFill("solid", fgColor=HEADER_BG)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 30

        ws.merge_cells(f"D1:{get_column_letter(len(df.columns))}1")
        meta_cell = ws["D1"]
        meta_cell.value = f"Margem Desejada: {margem}%  |  Canais: {', '.join(canais)}  |  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        meta_cell.font = Font(name="Calibri", size=10, color="A1A1AA")
        meta_cell.fill = PatternFill("solid", fgColor=HEADER_BG)
        meta_cell.alignment = Alignment(horizontal="right", vertical="center")

        # === LINHA DE CABEÇALHO DAS COLUNAS ===
        for col_idx, col_name in enumerate(df.columns, 1):
            cell = ws.cell(row=2, column=col_idx, value=col_name)
            cell.font = Font(name="Calibri", size=10, bold=True, color=SUB_FG)
            cell.fill = PatternFill("solid", fgColor=SUB_BG)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
        ws.row_dimensions[2].height = 40

        # === DADOS ===
        for row_idx, (_, row) in enumerate(df.iterrows(), 3):
            bg = "FFFFFF" if row_idx % 2 == 1 else ZEBRA
            for col_idx, (col_name, value) in enumerate(row.items(), 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = border
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.font = Font(name="Calibri", size=10)

                # Colorir lucro
                if "Lucro" in col_name and isinstance(value, (int, float)):
                    if value > 0:
                        cell.fill = PatternFill("solid", fgColor=GREEN)
                    elif value < 0:
                        cell.fill = PatternFill("solid", fgColor=RED)
                    else:
                        cell.fill = PatternFill("solid", fgColor=ORANGE)
                elif value == "INVIÁVEL":
                    cell.fill = PatternFill("solid", fgColor=RED)
                    cell.font = Font(name="Calibri", size=10, bold=True, color="721C24")
                else:
                    cell.fill = PatternFill("solid", fgColor=bg)

        # Ajuste de largura das colunas
        for col_idx, col_name in enumerate(df.columns, 1):
            max_len = max(len(str(col_name)), 12)
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 30)

        # Congelar cabeçalho
        ws.freeze_panes = "A3"

        wb.save(output_path)
