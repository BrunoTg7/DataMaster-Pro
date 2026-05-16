"""
Conciliador Pro v2.1 - Suporta dois modos:
1. Modo Clássico: Extrato bancário ↔ Planilha de vendas
2. Modo NF-e: XML de Notas Fiscais ↔ Extrato bancário
Focado em MEIs e pequenas empresas brasileiras
"""
import pandas as pd
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime


class Conciliador:
    def __init__(self, log_callback: Callable = None):
        self.log_callback = log_callback

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    # ========================================================================
    # MODO CLÁSSICO: Extrato ↔ Vendas
    # ========================================================================
    def reconcile_classic(
        self,
        extract_file: str,
        sales_file: str,
        output_path: str,
        tolerance: float = 0.01
    ) -> Dict:
        """Concilia extrato bancário com planilha de vendas (modo antigo)"""
        try:
            self._log("Iniciando conciliação clássica...")

            extract_df = self._load_file(extract_file)
            sales_df = self._load_file(sales_file)

            if extract_df is None or sales_df is None:
                return {"success": False, "error": "Erro ao carregar arquivos"}

            extract_df = self._normalize_columns(extract_df)
            sales_df = self._normalize_columns_sales(sales_df)

            matched = []
            unmatched_extract = []
            matched_values = set()

            for idx_e, row_e in extract_df.iterrows():
                found = False
                for idx_s, row_s in sales_df.iterrows():
                    key = f"{row_s.get('data')}_{row_s.get('valor')}"
                    if key in matched_values:
                        continue

                    if (row_e.get("data") == row_s.get("data") and
                        abs(float(row_e.get("valor", 0)) - float(row_s.get("valor", 0))) <= tolerance):
                        matched.append({
                            "status": "CONCILIADO",
                            "data": row_e.get("data"),
                            "valor": row_e.get("valor"),
                            "descricao": row_e.get("descricao"),
                            "venda_id": row_s.get("id", "")
                        })
                        matched_values.add(key)
                        found = True
                        break

                if not found:
                    unmatched_extract.append({
                        "status": "PENDENTE (sem venda)",
                        "data": row_e.get("data"),
                        "valor": row_e.get("valor"),
                        "descricao": row_e.get("descricao")
                    })

            unmatched_sales = []
            for idx_s, row_s in sales_df.iterrows():
                key = f"{row_s.get('data')}_{row_s.get('valor')}"
                if key not in matched_values:
                    unmatched_sales.append({
                        "status": "PENDENTE (sem recebimento)",
                        "data": row_s.get("data"),
                        "valor": row_s.get("valor"),
                        "descricao": row_s.get("descricao")
                    })

            result_df = pd.DataFrame(matched + unmatched_extract + unmatched_sales)
            result_df.to_excel(output_path, index=False)

            return {
                "success": True,
                "mode": "classic",
                "total_extract": len(extract_df),
                "total_sales": len(sales_df),
                "matched": len(matched),
                "unmatched_extract": len(unmatched_extract),
                "unmatched_sales": len(unmatched_sales),
                "output_path": output_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================================================
    # MODO NF-e: XML ↔ Extrato
    # ========================================================================
    def reconcile_nfe(
        self,
        xml_folder: str,
        bank_file: str,
        output_path: str,
        tolerance: float = 0.05
    ) -> Dict:
        """Concilia XMLs de NF-e com extrato bancário"""
        try:
            self._log("Iniciando conciliação de NF-e...")

            nfe_data = self._load_nfe_files(xml_folder)
            if not nfe_data:
                return {"success": False, "error": "Nenhum XML de NF-e encontrado"}

            nfe_df = pd.DataFrame(nfe_data)
            self._log(f"{len(nfe_df)} notas fiscais carregadas")

            bank_df = self._load_file(bank_file)
            if bank_df is None:
                return {"success": False, "error": "Erro ao carregar extrato bancário"}

            bank_df = self._normalize_columns(bank_df)
            bank_df['valor'] = bank_df['valor'].abs()
            self._log(f"Extrato carregado: {len(bank_df)} transações")

            matched = []
            unmatched_nfe = []
            matched_banks = set()

            for idx_n, nfe in nfe_df.iterrows():
                best_match = None
                best_diff = float('inf')

                for idx_b, bank in bank_df.iterrows():
                    if idx_b in matched_banks:
                        continue

                    diff = abs(float(nfe['valor']) - float(bank['valor']))
                    if diff <= tolerance:
                        if diff < best_diff:
                            best_match = (idx_b, bank)
                            best_diff = diff

                if best_match:
                    idx_b, bank = best_match
                    matched_banks.add(idx_b)
                    matched.append({
                        "status": "CONCILIADO",
                        "nfe_numero": nfe['numero'],
                        "nfe_serie": nfe.get('serie', ''),
                        "cliente": nfe['cliente'],
                        "data_nfe": nfe['data'],
                        "valor_nfe": nfe['valor'],
                        "data_pagamento": bank['data'],
                        "valor_pago": bank['valor'],
                        "descricao_banco": bank.get('descricao', '')
                    })
                else:
                    unmatched_nfe.append({
                        "status": "PENDENTE (não pago)",
                        "nfe_numero": nfe['numero'],
                        "nfe_serie": nfe.get('serie', ''),
                        "cliente": nfe['cliente'],
                        "data_nfe": nfe['data'],
                        "valor_nfe": nfe['valor'],
                        "data_pagamento": "-",
                        "valor_pago": 0,
                        "descricao_banco": "Sem correspondente no extrato"
                    })

            unmatched_bank = []
            for idx_b, bank in bank_df.iterrows():
                if idx_b not in matched_banks:
                    unmatched_bank.append({
                        "status": "SEM NF CORRESPONDENTE",
                        "nfe_numero": "-",
                        "nfe_serie": "-",
                        "cliente": "-",
                        "data_nfe": "-",
                        "valor_nfe": 0,
                        "data_pagamento": bank['data'],
                        "valor_pago": bank['valor'],
                        "descricao_banco": bank.get('descricao', '')
                    })

            result_df = pd.DataFrame(matched + unmatched_nfe + unmatched_bank)
            result_df.to_excel(output_path, index=False)

            return {
                "success": True,
                "mode": "nfe",
                "total_nfe": len(nfe_df),
                "total_bank": len(bank_df),
                "matched": len(matched),
                "unmatched_nfe": len(unmatched_nfe),
                "unmatched_bank": len(unmatched_bank),
                "output_path": output_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================================================
    # COMPATIBILIDADE - Método antigo
    # ========================================================================
    def reconcile(self, extract_file: str, sales_file: str, output_path: str, tolerance: float = 0.01) -> Dict:
        return self.reconcile_classic(extract_file, sales_file, output_path, tolerance)

    # ========================================================================
    # HELPERS
    # ========================================================================
    def _load_nfe_files(self, path: str) -> List[Dict]:
        """Carrega XMLs de NF-e de arquivo único ou pasta"""
        data = []
        files = []

        if os.path.isdir(path):
            files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.xml')]
        elif os.path.isfile(path) and path.lower().endswith('.xml'):
            files = [path]

        import os
        for xml_file in files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

                infNFe = root.find('.//nfe:infNFe', ns)
                if infNFe is None:
                    infNFe = root.find('.//infNFe')

                if infNFe is not None:
                    ide = infNFe.find('nfe:ide', ns) if ide is None else infNFe.find('ide')
                    n_nf = ide.find('nfe:nNF', ns).text if ide is not None and ide.find('nfe:nNF', ns) is not None else "0"
                    if n_nf == "0":
                        n_nf = ide.find('nNF', ns).text if ide is not None else "0"

                    d_emi = ""
                    dhEmi = ide.find('nfe:dhEmi', ns).text if ide is not None else ""
                    if dhEmi:
                        d_emi = dhEmi[:10]
                    else:
                        dEmi = ide.find('dEmi', ns).text if ide is not None else ""
                        if dEmi:
                            d_emi = dEmi

                    total = infNFe.find('nfe:total/nfe:ICMSTot', ns)
                    v_nf = "0"
                    if total is not None:
                        v_nf = total.find('nfe:vNF', ns).text if total.find('nfe:vNF', ns) is not None else "0"

                    dest = infNFe.find('nfe:dest', ns)
                    x_nome = "Consumidor"
                    if dest is not None:
                        x_nome = dest.find('nfe:xNome', ns).text if dest.find('nfe:xNome', ns) is not None else "Consumidor"

                    serie = ""
                    if ide is not None:
                        serie = ide.find('nfe:serie', ns).text if ide.find('nfe:serie', ns) is not None else ""

                    data.append({
                        "numero": n_nf,
                        "serie": serie,
                        "data": d_emi,
                        "valor": float(v_nf) if v_nf else 0,
                        "cliente": x_nome
                    })
            except Exception as e:
                self._log(f"Erro ao ler {xml_file}: {e}")

        return data

    def _load_file(self, file_path: str) -> Optional[pd.DataFrame]:
        path = Path(file_path)
        try:
            if path.suffix.lower() == ".csv":
                for enc in ['utf-8', 'latin1', 'iso-8859-1']:
                    try:
                        return pd.read_csv(path, encoding=enc, sep=None, engine='python')
                    except:
                        continue
            elif path.suffix.lower() in {".xlsx", ".xls"}:
                return pd.read_excel(path)
            elif path.suffix.lower() == ".ofx":
                return self._parse_ofx(path)
        except Exception as e:
            self._log(f"Erro ao carregar {file_path}: {e}")
        return None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = {}
        for col in df.columns:
            c = str(col).lower()
            if any(x in c for x in ["data", "date", "dt"]):
                mapping[col] = "data"
            elif any(x in c for x in ["valor", "amount", "val", "lançamento"]):
                mapping[col] = "valor"
            elif any(x in c for x in ["desc", "hist", "memo", "origem"]):
                mapping[col] = "descricao"

        df = df.rename(columns=mapping)

        if 'valor' in df.columns:
            df['valor'] = df['valor'].astype(str).str.replace(r'[^\d,.-]', '', regex=True).str.replace(',', '.').str.replace('R$', '').str.strip()
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)

        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')

        return df.dropna(subset=['valor']) if 'valor' in df.columns else df

    def _normalize_columns_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = {}
        for col in df.columns:
            c = str(col).lower()
            if any(x in c for x in ["data", "date", "dt", "emissão"]):
                mapping[col] = "data"
            elif any(x in c for x in ["valor", "amount", "val", "montante", "total", "preço"]):
                mapping[col] = "valor"
            elif any(x in c for x in ["desc", "description", "descricao", "produto"]):
                mapping[col] = "descricao"
            elif any(x in c for x in ["id", "codigo", "número", "nota"]):
                mapping[col] = "id"

        df = df.rename(columns=mapping)

        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)

        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce').dt.strftime('%Y-%m-%d')

        return df

    def _parse_ofx(self, file_path: Path) -> Optional[pd.DataFrame]:
        try:
            with open(file_path, "r", encoding="utf-8", errors='ignore') as f:
                content = f.read()

            transactions = []
            pattern = r'<STMTTRN>.*?</STMTTRN>'

            for match in re.finditer(pattern, content, re.DOTALL):
                trn = match.group(0)
                date = re.search(r'<DTPOSTED>(\d{8})', trn)
                amt = re.search(r'<TRNAMT>([-\d.]+)', trn)
                memo = re.search(r'<MEMO>([^<]+)', trn)

                if date and amt:
                    dt_obj = datetime.strptime(date.group(1), '%Y%m%d')
                    transactions.append({
                        "data": dt_obj,
                        "valor": abs(float(amt.group(1))),
                        "descricao": memo.group(1) if memo else "Transação"
                    })

            return pd.DataFrame(transactions) if transactions else None
        except:
            return None