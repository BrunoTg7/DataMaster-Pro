"""
Consolidador - Une múltiplas planilhas em uma estrutura única
"""
import pandas as pd
import os
from typing import List, Dict, Optional
import openpyxl


class Consolidador:
    def __init__(self):
        self.supported_formats = [".xlsx", ".xls", ".csv"]

    def consolidate(self, input_files: List[str], output_path: str, merge_strategy: str = "concat", max_rows: Optional[int] = None) -> Dict:
        if not input_files:
            return {"success": False, "error": "Nenhum arquivo selecionado"}

        dataframes = []
        total_rows_added = 0

        for file_path in input_files:
            if not os.path.exists(file_path): continue
            if max_rows and total_rows_added >= max_rows: break

            ext = os.path.splitext(file_path)[1].lower()
            try:
                if ext in [".xlsx", ".xls"]: df = pd.read_excel(file_path)
                else: df = pd.read_csv(file_path, encoding="utf-8")

                if max_rows:
                    quota = max_rows - total_rows_added
                    if len(df) > quota: df = df.head(quota)
                
                total_rows_added += len(df)
                df["_source_file"] = os.path.basename(file_path)
                dataframes.append(df)
            except Exception as e: print(f"Erro ao ler {file_path}: {e}")

        if not dataframes:
            return {"success": False, "error": "Nenhum dado válido encontrado"}

        try:
            if merge_strategy == "concat": result = pd.concat(dataframes, ignore_index=True)
            else: result = self._merge_horizontal(dataframes)

            result.to_excel(output_path, index=False, engine="openpyxl")
            return {
                "success": True,
                "total_rows": len(result),
                "total_files": len(dataframes),
                "output_path": output_path
            }
        except Exception as e: return {"success": False, "error": str(e)}

    def _merge_horizontal(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """Mescla dataframes horizontalmente (por linha)"""
        result = dataframes[0]
        for df in dataframes[1:]:
            result = pd.merge(result, df, how="outer", left_index=True, right_index=True)
        return result

    def get_preview(self, file_path: str, max_rows: int = 5) -> Optional[pd.DataFrame]:
        """Retorna preview do arquivo"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in [".xlsx", ".xls"]:
                return pd.read_excel(file_path, nrows=max_rows)
            else:
                return pd.read_csv(file_path, nrows=max_rows, encoding="utf-8")
        except:
            return None