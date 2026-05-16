"""
Data Sanitizer v2.0 - Limpa e normaliza dados de planilhas
CPF, CNPJ, Telefone, CEP, Nome, E-mail, Endereço
"""
import re
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
import unicodedata


class DataSanitizer:
    """Normaliza e limpa dados de planilhas"""

    def __init__(self, progress_callback=None, log_callback=None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback

    def process_file(self, input_file: str, output_file: str, options: Dict) -> Dict:
        """Processa arquivo aplicando normalizações
        
        Args:
            input_file: Caminho do arquivo de entrada
            output_file: Caminho do arquivo de saída
            options: Dict com campos a normalizar
        
        Returns:
            {success, total_rows, fields_processed, changes}
        """
        try:
            if input_file.endswith('.xlsx'):
                df = pd.read_excel(input_file)
            else:
                df = pd.read_csv(input_file, encoding='utf-8')

            total_rows = len(df)
            changes = {}
            
            fields_to_process = [k for k, v in options.items() if v]
            
            for field in fields_to_process:
                if field not in df.columns:
                    continue
                
                original_count = df[field].notna().sum()
                
                if field == 'nome' or 'nome' in field.lower():
                    df[field] = df[field].apply(self._normalize_name)
                    changes[field] = original_count
                    
                elif field == 'cpf':
                    df[field] = df[field].apply(self._normalize_cpf)
                    changes[field] = original_count
                    
                elif field == 'cnpj':
                    df[field] = df[field].apply(self._normalize_cnpj)
                    changes[field] = original_count
                    
                elif field == 'telefone' or 'fone' in field.lower() or 'celular' in field.lower():
                    df[field] = df[field].apply(self._normalize_phone)
                    changes[field] = original_count
                    
                elif field == 'cep':
                    df[field] = df[field].apply(self._normalize_cep)
                    changes[field] = original_count
                    
                elif field == 'email':
                    df[field] = df[field].apply(self._normalize_email)
                    changes[field] = original_count
                    
                elif field == 'endereco' or 'endereço' in field.lower() or 'rua' in field.lower():
                    df[field] = df[field].apply(self._normalize_address)
                    changes[field] = original_count
                
                if self.progress_callback:
                    self.progress_callback(int((fields_to_process.index(field) + 1) / len(fields_to_process) * 100))

            if output_file.endswith('.xlsx'):
                df.to_excel(output_file, index=False)
            else:
                df.to_csv(output_file, index=False, encoding='utf-8')

            return {
                "success": True,
                "total_rows": total_rows,
                "fields_processed": len(changes),
                "changes": changes,
                "output_path": output_file
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def preview_changes(self, df: pd.DataFrame, field: str, transformation: str) -> List[Dict]:
        """Mostra preview das mudanças"""
        if field not in df.columns:
            return []
        
        sample = df[field].dropna().head(10)
        results = []
        
        for idx, value in sample.items():
            if transformation == 'nome':
                original = str(value)
                transformed = self._normalize_name(original)
            elif transformation == 'cpf':
                original = str(value)
                transformed = self._normalize_cpf(original)
            elif transformation == 'cnpj':
                original = str(value)
                transformed = self._normalize_cnpj(original)
            elif transformation == 'telefone':
                original = str(value)
                transformed = self._normalize_phone(original)
            elif transformation == 'cep':
                original = str(value)
                transformed = self._normalize_cep(original)
            elif transformation == 'email':
                original = str(value)
                transformed = self._normalize_email(original)
            elif transformation == 'endereco':
                original = str(value)
                transformed = self._normalize_address(original)
            else:
                transformed = str(value)
            
            results.append({
                "index": idx,
                "original": original,
                "transformed": transformed,
                "changed": original != transformed
            })
        
        return results

    def _normalize_name(self, value) -> str:
        """Normaliza nomes: maiúsculas, remove acentos extras"""
        if pd.isna(value):
            return ""
        
        name = str(value).strip()
        name = name.upper()
        name = unicodedata.normalize('NFKD', name)
        name = ''.join(c for c in name if not unicodedata.combining(c))
        name = re.sub(r'\s+', ' ', name)
        
        return name

    def _normalize_cpf(self, value) -> str:
        """Normaliza CPF: formata como 000.000.000-00 ou remove máscara"""
        if pd.isna(value):
            return ""
        
        digits = re.sub(r'\D', '', str(value))
        
        if len(digits) == 11:
            return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        elif len(digits) > 0:
            return digits
        
        return str(value)

    def _normalize_cnpj(self, value) -> str:
        """Normaliza CNPJ: formata como 00.000.000/0000-00"""
        if pd.isna(value):
            return ""
        
        digits = re.sub(r'\D', '', str(value))
        
        if len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        elif len(digits) > 0:
            return digits
        
        return str(value)

    def _normalize_phone(self, value) -> str:
        """Normaliza telefone: (00) 00000-0000 ou (00) 0000-0000"""
        if pd.isna(value):
            return ""
        
        digits = re.sub(r'\D', '', str(value))
        
        if len(digits) >= 10:
            if len(digits) == 10:
                return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
            elif len(digits) == 11:
                return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        
        return str(value) if len(digits) < 10 else f"({digits[:2]}) {digits[2:]}"

    def _normalize_cep(self, value) -> str:
        """Normaliza CEP: 00000-000"""
        if pd.isna(value):
            return ""
        
        digits = re.sub(r'\D', '', str(value))
        
        if len(digits) == 8:
            return f"{digits[:5]}-{digits[5:]}"
        
        return str(value)

    def _normalize_email(self, value) -> str:
        """Normaliza e-mail: lowercase e trim"""
        if pd.isna(value):
            return ""
        
        email = str(value).strip().lower()
        return email

    def _normalize_address(self, value) -> str:
        """Normaliza endereço: abreviar+RUA/AV etc"""
        if pd.isna(value):
            return ""
        
        addr = str(value).strip().upper()
        addr = unicodedata.normalize('NFKD', addr)
        addr = ''.join(c for c in addr if not unicodedata.combining(c))
        
        abbrev_map = {
            'RUA ': 'R. ',
            'AVENIDA ': 'AV. ',
            'AVENIDA ': 'AV. ',
            'TRAVESSA ': 'TR. ',
            'PRAÇA ': 'PC. ',
            'ALAMEDA ': 'AL. ',
            'ESTRADA ': 'ESTR. ',
            'RODOVIA ': 'ROD. ',
        }
        
        for full, abbrev in abbrev_map.items():
            if full in addr:
                addr = addr.replace(full, abbrev)
        
        addr = re.sub(r'\s+', ' ', addr)
        
        return addr

    def detect_fields(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detecta automaticamente os campos na planilha"""
        fields = {}
        columns = [c.lower() for c in df.columns]
        
        field_mapping = {
            'cpf': ['cpf', 'cpf/cliente', 'cpf cliente'],
            'cnpj': ['cnpj', 'cnpj/cliente', 'cnpj cliente'],
            'nome': ['nome', 'nome cliente', 'cliente', 'razão social', 'razao social'],
            'telefone': ['telefone', 'fone', 'celular', 'tel', 'whatsapp'],
            'cep': ['cep', 'postal', 'cep/cliente'],
            'email': ['email', 'e-mail', 'mail'],
            'endereco': ['endereço', 'endereco', 'rua', 'logradouro', 'morada'],
        }
        
        for field, keywords in field_mapping.items():
            for i, col in enumerate(columns):
                if col in keywords:
                    fields[field] = df.columns[i]
                    break
        
        return fields