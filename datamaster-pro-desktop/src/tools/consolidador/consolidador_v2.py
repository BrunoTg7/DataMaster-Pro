"""
Consolidador v2.0 - Otimizado para máxima eficiência
Une múltiplas planilhas em estrutura única com performance extrema
"""
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path


class Consolidador:
    """Consolidação de arquivos com pandas puro - sem overhead"""
    
    FORMATS = {".xlsx", ".xls", ".csv"}
    
    def consolidate(
        self, 
        input_files: List[str], 
        output_path: str, 
        merge_strategy: str = "concat", 
        max_rows: Optional[int] = None
    ) -> Dict:
        """Consolida múltiplos arquivos em um único Excel
        
        Args:
            input_files: Lista de caminhos de arquivo
            output_path: Caminho do arquivo de saída
            merge_strategy: 'concat' (vertical) ou 'merge' (horizontal)
            max_rows: Limite de linhas (None = ilimitado)
        
        Returns:
            {success: bool, total_rows: int, total_files: int, output_path: str, error?: str}
        """
        if not input_files:
            return {"success": False, "error": "Nenhum arquivo"}
        
        dataframes = []
        rows_added = 0
        
        for file_path in input_files:
            path = Path(file_path)
            
            # Skip: arquivo não existe
            if not path.exists():
                continue
            
            # Skip: limite de linhas atingido
            if max_rows and rows_added >= max_rows:
                break
            
            # Skip: formato não suportado
            if path.suffix.lower() not in self.FORMATS:
                continue
            
            try:
                # Ler arquivo
                if path.suffix.lower() in {".xlsx", ".xls"}:
                    df = pd.read_excel(path)
                else:
                    df = pd.read_csv(path, encoding="utf-8")
                
                # Respeitar limite de linhas
                if max_rows:
                    remaining = max_rows - rows_added
                    if len(df) > remaining:
                        df = df.head(remaining)
                
                # Adicionar coluna de rastreamento
                df["_source"] = path.name
                dataframes.append(df)
                rows_added += len(df)
                
            except Exception:
                continue  # Skip arquivo com erro
        
        if not dataframes:
            return {"success": False, "error": "Nenhum dado válido"}
        
        try:
            # Consolidar
            result = pd.concat(dataframes, ignore_index=True) if merge_strategy == "concat" else pd.merge(
                dataframes[0], 
                pd.concat(dataframes[1:], axis=1), 
                left_index=True, 
                right_index=True
            )
            
            # Salvar
            result.to_excel(output_path, index=False, engine="openpyxl")
            
            return {
                "success": True,
                "total_rows": len(result),
                "total_files": len(dataframes),
                "output_path": output_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def preview(self, file_path: str, rows: int = 5) -> Optional[pd.DataFrame]:
        """Retorna preview de arquivo"""
        path = Path(file_path)
        
        try:
            if path.suffix.lower() in {".xlsx", ".xls"}:
                return pd.read_excel(path, nrows=rows)
            else:
                return pd.read_csv(path, nrows=rows, encoding="utf-8")
        except:
            return None
