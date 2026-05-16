"""
Categorizador v2.0 Pro - Otimizado para máxima velocidade e flexibilidade
Classifica transações por categoria com keyword matching inteligente.
"""
import pandas as pd
import json
import os
from typing import List, Dict, Optional, Any
from pathlib import Path

class Categorizador:
    """Motor profissional de categorização com suporte a regras customizadas"""
    
    DEFAULT_CATEGORIES = {
        "alimentação": {"keywords": ["restaurante", "supermercado", "padaria", "cafe", "pizza", "delivery", "ifood", "uber eats"], "priority": 10},
        "transporte": {"keywords": ["uber", "99app", "taxi", "onibus", "metro", "combustivel", "gasolina", "posto"], "priority": 9},
        "utilidades": {"keywords": ["agua", "energia", "internet", "telefone", "luz", "celular", "cpfl", "sabesp"], "priority": 8},
        "moradia": {"keywords": ["aluguel", "condominio", "iptu", "reforma", "ferragem"], "priority": 7},
        "saúde": {"keywords": ["farmacia", "hospital", "medico", "dentista", "exame", "drogaria"], "priority": 6},
        "educação": {"keywords": ["escola", "curso", "faculdade", "livros", "mensalidade"], "priority": 5},
        "lazer": {"keywords": ["cinema", "viagem", "hotel", "netflix", "spotify", "ingresso"], "priority": 4},
        "receita": {"keywords": ["salario", "venda", "reembolso", "pix recebido", "deposito"], "priority": 100},
        "outros": {"keywords": [], "priority": 0}
    }

    def __init__(self, categories: Dict = None):
        self.categories = categories or self.DEFAULT_CATEGORIES.copy()

    def get_categories(self) -> Dict:
        """Retorna as categorias atuais (exigido pela GUI)"""
        return self.categories

    def add_category(self, name: str, keywords: List[str], priority: int = 1):
        """Adiciona ou atualiza uma categoria"""
        self.categories[name.lower()] = {
            "keywords": [k.lower() for k in keywords],
            "priority": priority
        }

    def load_custom_categories_from_file(self, file_path: str) -> Dict:
        """Carrega categorias de um arquivo JSON ou Excel"""
        try:
            path = Path(file_path)
            if path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories.update(data)
            elif path.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                for _, row in df.iterrows():
                    cat = str(row[0]).lower()
                    keys = str(row[1]).split(',')
                    self.add_category(cat, [k.strip() for k in keys])
            return {"success": True, "categories": self.categories}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def categorize(self, input_path: str, output_path: str, description_column: str = "descricao", category_column: str = "categoria") -> Dict:
        """Categoriza um arquivo completo"""
        try:
            if input_path.endswith('.csv'):
                df = pd.read_csv(input_path)
            else:
                df = pd.read_excel(input_path)

            if description_column not in df.columns:
                return {"success": False, "error": f"Coluna '{description_column}' não encontrada"}

            df[category_column] = df[description_column].apply(lambda x: self._classify(str(x)))
            
            if output_path.endswith('.csv'):
                df.to_csv(output_path, index=False)
            else:
                df.to_excel(output_path, index=False)

            counts = df[category_column].value_counts().to_dict()
            categorized_count = len(df) - counts.get("outros", 0)

            return {
                "success": True,
                "total_rows": len(df),
                "categorized_rows": categorized_count,
                "category_counts": counts,
                "output_path": output_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _classify(self, text: str) -> str:
        """Classifica uma única string baseado nas keywords e prioridade"""
        text = text.lower()
        best_match = "outros"
        highest_priority = -1

        for cat, data in self.categories.items():
            for kw in data["keywords"]:
                if kw in text:
                    if data["priority"] > highest_priority:
                        highest_priority = data["priority"]
                        best_match = cat
                    break # Encontrou match nesta categoria, vai para a próxima
        
        return best_match
