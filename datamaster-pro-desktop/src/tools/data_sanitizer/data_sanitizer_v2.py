"""
Data Sanitizer v3.0 - Limpa e normaliza dados de planilhas
CPF, CNPJ, Telefone, CEP, Nome, E-mail, Endereço

Novidades v3.0:
- Validação de CPF/CNPJ via dígito verificador (módulo 11)
- Normalização de endereço via ViaCEP API (gratuita)
- Relatório de inválidos (CPF/CNPJ com dígito incorreto)
"""
import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import unicodedata
import httpx
from src.utils.excel_styler import save_premium_excel


class DataSanitizer:
    """Normaliza e limpa dados de planilhas"""

    VIACEP_API = "https://viacep.com.br/ws/{cep}/json/"

    # Strategy dict: maps field name patterns to normalization methods
    _TRANSFORMATION_MAP = {
        'nome': '_normalize_name',
        'cpf': '_normalize_cpf',
        'cnpj': '_normalize_cnpj',
        'telefone': '_normalize_phone',
        'fone': '_normalize_phone',
        'celular': '_normalize_phone',
        'cep': '_normalize_cep',
        'email': '_normalize_email',
        'endereco': '_normalize_address',
        'endereço': '_normalize_address',
        'rua': '_normalize_address',
    }

    def __init__(self, progress_callback=None, log_callback=None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback

    def _resolve_transform(self, field: str):
        """Resolve the normalization method for a given field name."""
        field_lower = field.lower()
        for pattern, method_name in self._TRANSFORMATION_MAP.items():
            if pattern in field_lower:
                return getattr(self, method_name)
        return None

    def process_file(self, input_file: str, output_file: str, options: Dict, visual_theme: str = "classic_blue", validate_docs: bool = True) -> Dict:
        """Processa arquivo aplicando normalizações
        
        Args:
            input_file: Caminho do arquivo de entrada
            output_file: Caminho do arquivo de saída
            options: Dict com campos a normalizar
            validate_docs: Se True, valida CPF/CNPJ e gera relatório de inválidos
        
        Returns:
            {success, total_rows, fields_processed, changes, validation_report?}
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
                transform_fn = self._resolve_transform(field)
                
                if transform_fn:
                    df[field] = df[field].apply(transform_fn)
                    changes[field] = original_count
                
                if self.progress_callback:
                    self.progress_callback(int((fields_to_process.index(field) + 1) / len(fields_to_process) * 100))

            # Validação de CPF/CNPJ
            validation_report = None
            if validate_docs:
                cpf_col = next((c for c in df.columns if 'cpf' in c.lower()), None)
                cnpj_col = next((c for c in df.columns if 'cnpj' in c.lower()), None)
                if cpf_col or cnpj_col:
                    validation_report = self.validate_and_report(df, cpf_col, cnpj_col)

            if output_file.endswith('.xlsx'):
                stats = [
                    ("Data da Execução", datetime.now().strftime("%d/%m/%Y %H:%M")),
                    ("Total de Registros", str(total_rows)),
                    ("Campos Processados", str(len(changes))),
                    *[(f"Registros Normalizados - {k}", str(v)) for k, v in changes.items()],
                ]
                if validation_report:
                    stats.append(("CPF Válidos", str(validation_report["valid_cpf"])))
                    stats.append(("CPF Inválidos", str(len(validation_report["invalid_cpf"]))))
                    stats.append(("CNPJ Válidos", str(validation_report["valid_cnpj"])))
                    stats.append(("CNPJ Inválidos", str(len(validation_report["invalid_cnpj"]))))

                save_premium_excel(
                    df, output_file,
                    theme_name=visual_theme,
                    title="DATA SANITIZER - NORMALIZAÇÃO DE DADOS",
                    stats=stats
                )
            else:
                df.to_csv(output_file, index=False, encoding='utf-8')

            result = {
                "success": True,
                "total_rows": total_rows,
                "fields_processed": len(changes),
                "changes": changes,
                "output_path": output_file
            }
            if validation_report:
                result["validation_report"] = validation_report
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def preview_changes(self, df: pd.DataFrame, field: str, transformation: str) -> List[Dict]:
        try:
            if field not in df.columns:
                return []

            sample = df[field].dropna().head(10)
            results = []

            for idx, value in sample.items():
                original = str(value)
                transform_fn = self._resolve_transform(transformation)
                if transform_fn:
                    transformed = transform_fn(original)
                else:
                    transformed = str(value)

                results.append({
                    "index": idx,
                    "original": original,
                    "transformed": transformed,
                    "changed": original != transformed
                })

            return results
        except Exception:
            return []

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

    _EMAIL_RE = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
    )

    def _normalize_email(self, value) -> str:
        """Normaliza e-mail: lowercase, trim e valida formato RFC 5322"""
        if pd.isna(value):
            return ""
        
        email = str(value).strip().lower()
        if not self._EMAIL_RE.match(email):
            return ""
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
        try:
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
        except Exception:
            return {}

    # =====================================================================
    # VALIDAÇÃO DE CPF/CNPJ (Dígito Verificador - Módulo 11)
    # =====================================================================

    def validate_cpf(self, value) -> bool:
        """Valida CPF usando algoritmo de dígito verificador (módulo 11)"""
        if pd.isna(value):
            return False
        cpf = re.sub(r'\D', '', str(value))
        if len(cpf) != 11:
            return False
        # Rejeitar CPFs com todos dígitos iguais (ex: 111.111.111-11)
        if len(set(cpf)) == 1:
            return False
        # Primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        if int(cpf[9]) != dv1:
            return False
        # Segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        return int(cpf[10]) == dv2

    def validate_cnpj(self, value) -> bool:
        """Valida CNPJ usando algoritmo de dígito verificador (módulo 11)"""
        if pd.isna(value):
            return False
        cnpj = re.sub(r'\D', '', str(value))
        if len(cnpj) != 14:
            return False
        if len(set(cnpj)) == 1:
            return False
        peso1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        peso2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * peso1[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        soma = sum(int(cnpj[i]) * peso2[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        return cnpj[-2:] == f"{dv1}{dv2}"

    def validate_and_report(self, df: pd.DataFrame, cpf_col: str = None, cnpj_col: str = None) -> Dict:
        """Valida CPF/CNPJ e retorna relatório de inválidos"""
        report = {"invalid_cpf": [], "invalid_cnpj": [], "valid_cpf": 0, "valid_cnpj": 0}

        if cpf_col and cpf_col in df.columns:
            for idx, val in df[cpf_col].items():
                if pd.isna(val) or str(val).strip() == "":
                    continue
                if self.validate_cpf(val):
                    report["valid_cpf"] += 1
                else:
                    report["invalid_cpf"].append({"row": idx + 2, "value": str(val)})

        if cnpj_col and cnpj_col in df.columns:
            for idx, val in df[cnpj_col].items():
                if pd.isna(val) or str(val).strip() == "":
                    continue
                if self.validate_cnpj(val):
                    report["valid_cnpj"] += 1
                else:
                    report["invalid_cnpj"].append({"row": idx + 2, "value": str(val)})

        return report

    # =====================================================================
    # NORMALIZAÇÃO DE ENDEREÇO VIA VIACEP
    # =====================================================================

    def normalize_address_by_cep(self, cep: str) -> Dict:
        """Busca endereço completo via ViaCEP API (gratuita)"""
        cep_clean = re.sub(r'\D', '', str(cep))
        if len(cep_clean) != 8:
            return {"error": "CEP inválido"}
        try:
            resp = httpx.get(self.VIACEP_API.format(cep=cep_clean), timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if "erro" not in data:
                    return {
                        "logradouro": data.get("logradouro", ""),
                        "bairro": data.get("bairro", ""),
                        "cidade": data.get("localidade", ""),
                        "uf": data.get("uf", ""),
                        "complemento": data.get("complemento", ""),
                        "ibge": data.get("ibge", ""),
                    }
        except Exception:
            pass
        return {"error": "CEP não encontrado"}

    def enrich_addresses_from_cep(self, df: pd.DataFrame, cep_col: str, output_col: str = "endereco_completo") -> pd.DataFrame:
        """ Enriquece DataFrame com endereços completos a partir de CEPs"""
        if cep_col not in df.columns:
            return df

        df = df.copy()
        df[output_col] = ""

        for idx, val in df[cep_col].items():
            if pd.isna(val) or str(val).strip() == "":
                continue
            addr = self.normalize_address_by_cep(val)
            if "error" not in addr:
                parts = [
                    addr.get("logradouro", ""),
                    addr.get("bairro", ""),
                    addr.get("cidade", ""),
                    addr.get("uf", ""),
                ]
                df.at[idx, output_col] = ", ".join(p for p in parts if p)

        return df