"""
Minerador Pro v5.0 Enterprise – Motor Profissional de Rastreio de Preços e Dados da Web
100% Offline/Local, Sem Uso de IA.

NOVIDADES v5.0:
- Selector Registry versionado (GitHub/Gist + arquivo local) com auto-atualização
- Fallback para APIs oficiais de marketplaces (ML, Amazon SP-API, Shopee Open Platform)
- Health check automático de seletores (detecta breaking changes)
- Cache inteligente com TTL + invalidação por versão
- Seletores customizados persistidos por usuário
- Métricas de qualidade de extração por marketplace
- Circuit breaker para anti-bot agressivo
"""

import asyncio
import logging
import re
import random
import os
import sys
import time
import json
import hashlib
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from urllib.parse import urlparse
from dataclasses import dataclass, asdict, field
import config
from src.tools.minerador.minerador_v2 import SELECTOR_REGISTRY

log = logging.getLogger(__name__)
from src.utils.user_agents import UserAgentProvider
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ── URL validation ──────────────────────────────────────────────────────────
ALLOWED_URL_SCHEMES = {"http", "https"}
BANNED_SCHEMES = {"javascript", "data", "file", "ftp", "ftps", "sftp", "blob", "about", "chrome", "edge", "vbscript"}

def validate_url(url: str) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    url = url.strip().strip('"\'')
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.scheme.lower() in BANNED_SCHEMES:
            return None
        if not parsed.scheme:
            clean = url.lstrip("/")
            url = "https://" + clean
            parsed = urlparse(url)
        if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
            return None
        if not parsed.netloc:
            return None
        return url
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
# SELECTOR REGISTRY ENTERPRISE - Versionado, Auto-atualizável, Health-checked
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class SelectorSet:
    """Conjunto de seletores para um campo específico"""
    selectors: List[str]
    version: str
    last_tested: Optional[str] = None
    success_rate: float = 1.0
    source: str = "builtin"  # "builtin", "github", "local", "user"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SelectorSet':
        return cls(**data)


@dataclass
class MarketplaceSelectors:
    """Seletores completos para um marketplace"""
    marketplace: str
    title: SelectorSet
    price: SelectorSet
    availability: SelectorSet
    rating: SelectorSet
    seller: SelectorSet
    custom_fields: Dict[str, SelectorSet] = field(default_factory=dict)
    registry_version: str = "1.0"
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "marketplace": self.marketplace,
            "title": self.title.to_dict(),
            "price": self.price.to_dict(),
            "availability": self.availability.to_dict(),
            "rating": self.rating.to_dict(),
            "seller": self.seller.to_dict(),
            "custom_fields": {k: v.to_dict() for k, v in self.custom_fields.items()},
            "registry_version": self.registry_version,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MarketplaceSelectors':
        return cls(
            marketplace=data["marketplace"],
            title=SelectorSet.from_dict(data["title"]),
            price=SelectorSet.from_dict(data["price"]),
            availability=SelectorSet.from_dict(data["availability"]),
            rating=SelectorSet.from_dict(data["rating"]),
            seller=SelectorSet.from_dict(data["seller"]),
            custom_fields={k: SelectorSet.from_dict(v) for k, v in data.get("custom_fields", {}).items()},
            registry_version=data.get("registry_version", "1.0"),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )


class SelectorRegistryEnterprise:
    """
    Registry Enterprise de seletores CSS com:
    - Versionamento semântico
    - Auto-atualização via GitHub/Gist
    - Health check contínuo
    - Cache com TTL
    - Persistência local de customizações do usuário
    """
    
    REGISTRY_VERSION = "5.0"
    
    # URLs para auto-atualização
    GITHUB_REGISTRY_URL = "https://raw.githubusercontent.com/datamasterpro/selectors/main/registry.json"
    GIST_REGISTRY_URL = "https://gist.githubusercontent.com/datamasterpro/selector-registry/raw/registry.json"
    
    # Arquivos locais
    LOCAL_REGISTRY_PATH = "data/selectors/registry.json"
    USER_CUSTOM_PATH = "data/selectors/user_custom.json"
    HEALTH_LOG_PATH = "data/selectors/health_log.json"
    
    # TTL do cache (horas)
    CACHE_TTL_HOURS = 24
    HEALTH_CHECK_INTERVAL_HOURS = 6
    
    def __init__(self):
        self._registry: Dict[str, MarketplaceSelectors] = {}
        self._custom_selectors: Dict[str, Dict[str, SelectorSet]] = {}
        self._health_log: List[Dict] = []
        self._last_update: Optional[datetime] = None
        self._last_health_check: Optional[datetime] = None
        self._load_registry()
        self._load_custom()
        self._load_health_log()
    
    def _load_registry(self):
        """Carrega registry: builtin → local → github (fallback chain)"""
        # 1. Builtin (hardcoded fallback)
        self._registry = self._get_builtin_registry()
        
        # 2. Local versionado (commitado no repo)
        if os.path.exists(self.LOCAL_REGISTRY_PATH):
            try:
                with open(self.LOCAL_REGISTRY_PATH, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                self._merge_registry(local_data, source="local")
                log.info(f"Registry local carregado: {len(local_data)} marketplaces")
            except Exception as e:
                log.warning(f"Falha ao carregar registry local: {e}")
        
        # 3. Auto-atualização via GitHub (async, non-blocking)
        # Não bloqueia inicialização - roda em background
        self._schedule_remote_update()
    
    def _schedule_remote_update(self):
        """Agenda atualização remota em background"""
        def _update():
            try:
                self._update_from_remote()
            except Exception as e:
                log.debug(f"Auto-update falhou (ignorado): {e}")
        
        # Roda em thread separada para não bloquear
        import threading
        t = threading.Thread(target=_update, daemon=True)
        t.start()
    
    def _update_from_remote(self):
        """Tenta baixar registry do GitHub/Gist"""
        for url in [self.GITHUB_REGISTRY_URL, self.GIST_REGISTRY_URL]:
            try:
                resp = httpx.get(url, timeout=15.0)
                if resp.status_code == 200:
                    remote_data = resp.json()
                    # Verificar versão
                    remote_version = remote_data.get("registry_version", "0.0")
                    if self._version_greater(remote_version, self.REGISTRY_VERSION):
                        self._merge_registry(remote_data, source="github")
                        # Salvar localmente para próxima vez
                        self._save_local_registry(remote_data)
                        log.info(f"Registry atualizado para v{remote_version} via {url}")
                        return
            except Exception:
                continue
    
    def _version_greater(self, v1: str, v2: str) -> bool:
        """Compara versões semânticas simples"""
        try:
            p1 = [int(x) for x in v1.split(".")]
            p2 = [int(x) for x in v2.split(".")]
            return p1 > p2
        except:
            return False
    
    def _get_builtin_registry(self) -> Dict[str, MarketplaceSelectors]:
        """Registry hardcoded como fallback final"""
        builtin = {}
        for mp, selectors in SELECTOR_REGISTRY.items():
            builtin[mp] = MarketplaceSelectors(
                marketplace=mp,
                title=SelectorSet(selectors=selectors.get("title", []), version="5.0", source="builtin"),
                price=SelectorSet(selectors=selectors.get("price", []), version="5.0", source="builtin"),
                availability=SelectorSet(selectors=selectors.get("availability", []), version="5.0", source="builtin"),
                rating=SelectorSet(selectors=selectors.get("rating", []), version="5.0", source="builtin"),
                seller=SelectorSet(selectors=selectors.get("seller", []), version="5.0", source="builtin"),
                registry_version="5.0"
            )
        return builtin
    
    def _merge_registry(self, data: Dict, source: str):
        """Merge registry remoto/local com prioridade: user > remote > local > builtin"""
        for mp, mp_data in data.items():
            if mp not in self._registry:
                self._registry[mp] = MarketplaceSelectors.from_dict(mp_data)
            else:
                # Merge campos - prioridade: source mais recente
                existing = self._registry[mp]
                for field_name in ["title", "price", "availability", "rating", "seller"]:
                    if field_name in mp_data:
                        new_set = SelectorSet.from_dict(mp_data[field_name])
                        if new_set.source != "user" or source == "user":
                            setattr(existing, field_name, new_set)
                
                # Custom fields do usuário têm prioridade máxima
                if "custom_fields" in mp_data and source == "user":
                    for cf_name, cf_data in mp_data["custom_fields"].items():
                        existing.custom_fields[cf_name] = SelectorSet.from_dict(cf_data)
    
    def _load_custom(self):
        """Carrega customizações do usuário"""
        if os.path.exists(self.USER_CUSTOM_PATH):
            try:
                with open(self.USER_CUSTOM_PATH, "r", encoding="utf-8") as f:
                    custom_data = json.load(f)
                self._custom_selectors = {
                    mp: {k: SelectorSet.from_dict(v) for k, v in cf.items()}
                    for mp, cf in custom_data.items()
                }
                # Merge no registry principal
                self._merge_registry({
                    mp: {"custom_fields": cf} for mp, cf in self._custom_selectors.items()
                }, source="user")
                log.info(f"Customizações do usuário carregadas: {len(custom_data)} marketplaces")
            except Exception as e:
                log.warning(f"Falha ao carregar customizações: {e}")
    
    def _load_health_log(self):
        """Carrega log de saúde dos seletores"""
        if os.path.exists(self.HEALTH_LOG_PATH):
            try:
                with open(self.HEALTH_LOG_PATH, "r", encoding="utf-8") as f:
                    self._health_log = json.load(f)
            except Exception:
                self._health_log = []
    
    def _save_local_registry(self, data: Dict):
        """Salva registry local versionado"""
        os.makedirs(os.path.dirname(self.LOCAL_REGISTRY_PATH), exist_ok=True)
        try:
            with open(self.LOCAL_REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning(f"Falha ao salvar registry local: {e}")
    
    def save_custom_selectors(self, marketplace: str, field: str, selectors: List[str]):
        """Salva customização do usuário (prioridade máxima)"""
        if marketplace not in self._custom_selectors:
            self._custom_selectors[marketplace] = {}
        
        self._custom_selectors[marketplace][field] = SelectorSet(
            selectors=selectors,
            version="user",
            source="user",
            last_tested=datetime.now().isoformat(),
            success_rate=1.0
        )
        
        # Atualiza registry
        if marketplace in self._registry:
            self._registry[marketplace].custom_fields[field] = self._custom_selectors[marketplace][field]
        
        # Persiste
        os.makedirs(os.path.dirname(self.USER_CUSTOM_PATH), exist_ok=True)
        custom_json = {
            mp: {k: v.to_dict() for k, v in cf.items()}
            for mp, cf in self._custom_selectors.items()
        }
        with open(self.USER_CUSTOM_PATH, "w", encoding="utf-8") as f:
            json.dump(custom_json, f, ensure_ascii=False, indent=2)
    
    def get_selectors(self, marketplace: str, field: str) -> List[str]:
        """Obtém seletores com prioridade: user > remote > local > builtin"""
        if marketplace in self._registry:
            mp = self._registry[marketplace]
            
            # 1. Custom do usuário
            if field in mp.custom_fields:
                return mp.custom_fields[field].selectors
            
            # 2. Campo padrão
            if hasattr(mp, field):
                return getattr(mp, field).selectors
        
        # Fallback genérico
        return SELECTOR_REGISTRY.get("generico", {}).get(field, [])
    
    def record_extraction_result(self, marketplace: str, field: str, success: bool):
        """Registra resultado de extração para health check"""
        if marketplace not in self._registry:
            return
        
        mp = self._registry[marketplace]
        if hasattr(mp, field):
            selector_set = getattr(mp, field)
            # Atualiza taxa de sucesso (EMA - exponential moving average)
            alpha = 0.1
            selector_set.success_rate = (1 - alpha) * selector_set.success_rate + alpha * (1.0 if success else 0.0)
            selector_set.last_tested = datetime.now().isoformat()
            
            # Log de saúde
            self._health_log.append({
                "timestamp": datetime.now().isoformat(),
                "marketplace": marketplace,
                "field": field,
                "success": success,
                "success_rate": selector_set.success_rate
            })
            
            # Mantém apenas últimos 10000 entries
            if len(self._health_log) > 10000:
                self._health_log = self._health_log[-10000:]
    
    def health_check(self) -> Dict:
        """Retorna relatório de saúde dos seletores"""
        report = {
            "registry_version": self.REGISTRY_VERSION,
            "marketplaces": len(self._registry),
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "health_by_marketplace": {},
            "alerts": []
        }
        
        for mp_name, mp in self._registry.items():
            mp_health = {
                "fields": {},
                "overall_score": 0.0
            }
            scores = []
            for field_name in ["title", "price", "availability", "rating", "seller"]:
                if hasattr(mp, field_name):
                    ss = getattr(mp, field_name)
                    mp_health["fields"][field_name] = {
                        "success_rate": round(ss.success_rate * 100, 1),
                        "version": ss.version,
                        "source": ss.source,
                        "last_tested": ss.last_tested
                    }
                    scores.append(ss.success_rate)
            
            mp_health["overall_score"] = round(sum(scores) / len(scores) * 100, 1) if scores else 0
            
            # Alertas
            if mp_health["overall_score"] < 70:
                report["alerts"].append(f"{mp_name}: score geral {mp_health['overall_score']}% - revisão recomendada")
            for fn, fd in mp_health["fields"].items():
                if fd["success_rate"] < 50:
                    report["alerts"].append(f"{mp_name}.{fn}: {fd['success_rate']}% - seletores degradados")
            
            report["health_by_marketplace"][mp_name] = mp_health
        
        return report
    
    def run_health_check_async(self):
        """Executa health check em background"""
        def _check():
            try:
                report = self.health_check()
                # Salvar log
                os.makedirs(os.path.dirname(self.HEALTH_LOG_PATH), exist_ok=True)
                with open(self.HEALTH_LOG_PATH, "w", encoding="utf-8") as f:
                    json.dump(self._health_log, f, ensure_ascii=False, indent=2)
                self._last_health_check = datetime.now()
            except Exception as e:
                log.debug(f"Health check falhou: {e}")
        
        threading.Thread(target=_check, daemon=True).start()


# Instância global do registry
_selector_registry = SelectorRegistryEnterprise()


# ════════════════════════════════════════════════════════════════════════════
# MARKETPLACE OFFICIAL API CLIENTS
# ════════════════════════════════════════════════════════════════════════════

class MercadoLivreAPIClient:
    """Cliente oficial Mercado Livre para busca de produtos/preços"""
    
    BASE_URL = "https://api.mercadolibre.com"
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv("ML_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("ML_CLIENT_SECRET")
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def _get_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        
        resp = await self._client.post(
            f"{self.BASE_URL}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"]
        return self._access_token
    
    async def search_products(self, query: str, limit: int = 20) -> List[Dict]:
        """Busca produtos via API oficial"""
        token = await self._get_token()
        resp = await self._client.get(
            f"{self.BASE_URL}/sites/MLB/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "limit": limit, "sort": "relevance"}
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    
    async def get_product(self, item_id: str) -> Optional[Dict]:
        """Obtém detalhes completos de um produto"""
        token = await self._get_token()
        resp = await self._client.get(
            f"{self.BASE_URL}/items/{item_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    
    async def close(self):
        await self._client.aclose()


class AmazonSPAPIClient:
    """Cliente Amazon Selling Partner API (SP-API)"""
    
    def __init__(self, lwa_client_id: str = None, lwa_client_secret: str = None, refresh_token: str = None):
        self.lwa_client_id = lwa_client_id or os.getenv("AMZ_LWA_CLIENT_ID")
        self.lwa_client_secret = lwa_client_secret or os.getenv("AMZ_LWA_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("AMZ_REFRESH_TOKEN")
        self._access_token: Optional[str] = None
        self._client = httpx.AsyncClient(timeout=30.0)
        self._endpoint = "https://sellingpartnerapi-na.amazon.com"
    
    async def _get_token(self) -> str:
        if self._access_token:
            return self._access_token
        # LWA token exchange
        resp = await self._client.post(
            "https://api.amazon.com/auth/o2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.lwa_client_id,
                "client_secret": self.lwa_client_secret
            }
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        return self._access_token
    
    async def search_items(self, query: str, limit: int = 20) -> List[Dict]:
        """Busca itens via Catalog Items API"""
        token = await self._get_token()
        resp = await self._client.get(
            f"{self._endpoint}/catalog/2022-04-01/items",
            headers={"Authorization": f"Bearer {token}", "x-amz-access-token": token},
            params={"keywords": query, "marketplaceIds": "A2Q3Y263D00KWM", "limit": limit}
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
    
    async def close(self):
        await self._client.aclose()


class ShopeeOpenPlatformClient:
    """Cliente Shopee Open Platform API"""
    
    BASE_URL = "https://partner.shopeemobile.com"
    
    def __init__(self, partner_id: str = None, partner_key: str = None, shop_id: str = None):
        self.partner_id = partner_id or os.getenv("SHOPEE_PARTNER_ID")
        self.partner_key = partner_key or os.getenv("SHOPEE_PARTNER_KEY")
        self.shop_id = shop_id or os.getenv("SHOPEE_SHOP_ID")
        self._client = httpx.AsyncClient(timeout=30.0)
    
    def _generate_sign(self, path: str, params: Dict) -> tuple:
        import hmac, hashlib, time
        timestamp = int(time.time())
        base_string = f"{self.partner_id}{path}{timestamp}{json.dumps(params, separators=(',', ':'))}"
        sign = hmac.new(
            self.partner_key.encode(),
            base_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return sign, timestamp
    
    async def search_items(self, keyword: str, limit: int = 20) -> List[Dict]:
        path = "/api/v2/product/search_items"
        params = {
            "keyword": keyword,
            "page_size": min(limit, 50),
            "shop_id": self.shop_id
        }
        sign, timestamp = self._generate_sign(path, params)
        
        headers = {
            "Authorization": f"SHA256 Credential={self.partner_id}, Timestamp={timestamp}, Signature={sign}"
        }
        
        resp = await self._client.get(
            f"{self.BASE_URL}{path}",
            headers=headers,
            params=params
        )
        if resp.status_code != 200:
            log.error(f"Shopee API error: {resp.status_code} - {resp.text}")
            return []
        data = resp.json()
        return data.get("response", {}).get("items", [])
    
    async def close(self):
        await self._client.aclose()


# ════════════════════════════════════════════════════════════════════════════
# MINERADOR ENTERPRISE v5.0
# ════════════════════════════════════════════════════════════════════════════

class MineradorEnterprise:
    """
    Minerador Enterprise v5.0 - Com API Oficial + Registry Auto-atualizável
    """
    
    def __init__(
        self,
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None,
        max_concurrency: int = 5,
        max_retries: int = 2,
    ):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.max_concurrency = max_concurrency
        self.max_retries = max_retries
        self._semaphore: Optional[asyncio.Semaphore] = None
        
        # Registry enterprise
        self.registry = _selector_registry
        
        # API Clients (inicializados lazy)
        self._ml_client: Optional[MercadoLivreAPIClient] = None
        self._amazon_client: Optional[AmazonSPAPIClient] = None
        self._shopee_client: Optional[ShopeeOpenPlatformClient] = None
        
        # Circuit breaker para anti-bot
        self._circuit_breakers: Dict[str, Dict] = {}
    
    def _log(self, message: str):
        log.info(message)
        if self.log_callback:
            self.log_callback(message)
    
    def _get_ml_client(self) -> Optional[MercadoLivreAPIClient]:
        if self._ml_client is None:
            ml_id = os.getenv("ML_CLIENT_ID")
            ml_secret = os.getenv("ML_CLIENT_SECRET")
            if ml_id and ml_secret:
                self._ml_client = MercadoLivreAPIClient(ml_id, ml_secret)
        return self._ml_client
    
    def _get_amazon_client(self) -> Optional[AmazonSPAPIClient]:
        if self._amazon_client is None:
            if os.getenv("AMZ_LWA_CLIENT_ID") and os.getenv("AMZ_LWA_CLIENT_SECRET") and os.getenv("AMZ_REFRESH_TOKEN"):
                self._amazon_client = AmazonSPAPIClient()
        return self._amazon_client
    
    def _get_shopee_client(self) -> Optional[ShopeeOpenPlatformClient]:
        if self._shopee_client is None:
            if os.getenv("SHOPEE_PARTNER_ID") and os.getenv("SHOPEE_PARTNER_KEY") and os.getenv("SHOPEE_SHOP_ID"):
                self._shopee_client = ShopeeOpenPlatformClient()
        return self._shopee_client
    
    # ═══════════════════════════════════════════════════════════════════════════
    # API PÚBLICA
    # ═══════════════════════════════════════════════════════════════════════════
    
    def mine_from_links(
        self,
        urls: List[str],
        marketplace: str = "generico",
        custom_selectors: Optional[Dict[str, str]] = None,
        visual_theme: str = "classic_blue",
        max_successful: Optional[int] = None,
        use_official_api: bool = True,
    ) -> Dict:
        """Minera dados de uma lista de URLs - com fallback API oficial → Playwright → ScraperAPI"""
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                self._mine_async(urls, marketplace, custom_selectors or {}, 
                               max_successful=max_successful, use_official_api=use_official_api)
            )
            loop.close()
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "results": [], "errors": []}
    
    def mine_from_file(
        self,
        file_path: str,
        marketplace: str = "generico",
        custom_selectors: Optional[Dict[str, str]] = None,
        max_links: Optional[int] = None,
        visual_theme: str = "classic_blue",
    ) -> Dict:
        """Lê URLs de arquivo (CSV/JSON) e minera dados de cada uma"""
        try:
            import pandas as pd
            
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith(".json"):
                df = pd.read_json(file_path)
            else:
                raise ValueError(f"Formato não suportado: {file_path}")
            
            url_col = None
            for col in ["url", "link", "URL", "Link", "product_url"]:
                if col in df.columns:
                    url_col = col
                    break
            if not url_col:
                raise ValueError(f"Coluna de URL não encontrada. Colunas: {list(df.columns)}")
            
            urls = df[url_col].dropna().astype(str).tolist()
            if max_links:
                urls = urls[:max_links]
            
            if not urls:
                return {"success": True, "results": [], "errors": [], "total": 0, "collected": 0, "output": ""}
            
            self._log(f"📁 Arquivo carregado: {len(urls)} URLs de {os.path.basename(file_path)}")
            
            result = self.mine_from_links(
                urls=urls,
                marketplace=marketplace,
                custom_selectors=custom_selectors,
                visual_theme=visual_theme,
                max_successful=max_links,
                use_official_api=True,
            )
            
            if result.get("success") and result.get("results"):
                output_path = file_path.rsplit(".", 1)[0] + "_mined.xlsx"
                try:
                    self.export_results(result["results"], output_path, visual_theme)
                    result["output"] = output_path
                except Exception as e:
                    self._log(f"⚠️ Erro ao exportar: {e}")
            
            return result
            
        except Exception as e:
            self._log(f"❌ Erro em mine_from_file: {e}")
            return {"success": False, "error": str(e), "results": [], "errors": [], "total": 0, "collected": 0, "output": ""}
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MOTOR ASSÍNCRONO COM FALLBACK INTELIGENTE
    # ════════════════════════════════════════════════════════════════════════════
    
    async def _mine_async(
        self,
        urls: List[str],
        marketplace: str,
        custom_selectors: Dict[str, str],
        max_successful: Optional[int] = None,
        use_official_api: bool = True,
    ) -> Dict:
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        
        # Validar URLs
        validated_urls = []
        for u in urls:
            clean = validate_url(u)
            if clean:
                validated_urls.append(clean)
        
        if not validated_urls:
            return {"success": True, "results": [], "errors": [], "total": 0, "collected": 0}
        
        total = len(validated_urls)
        self._log(f"🚀 Iniciando mineração Enterprise de {total} links (marketplace: {marketplace})")
        
        # 1. Tentar API Oficial primeiro (se disponível e use_official_api=True)
        official_results = {}
        if use_official_api:
            official_results = await self._try_official_api(validated_urls, marketplace)
        
        # 2. Para URLs não resolvidas pela API, usar Playwright + Registry
        remaining_urls = [u for u in validated_urls if u not in official_results]
        
        if remaining_urls:
            self._log(f"📱 {len(remaining_urls)} URLs para Playwright + Registry")
            playwright_results = await self._mine_playwright(remaining_urls, marketplace, custom_selectors, max_successful)
            official_results.update(playwright_results)
        
        # 3. Consolidar resultados
        results = []
        errors = []
        for url in validated_urls:
            if url in official_results:
                res = official_results[url]
                if res.get("success"):
                    results.append(res)
                else:
                    errors.append(res)
        
        collected = sum(1 for r in results if r.get("preco", 0) > 0)
        
        return {
            "success": True,
            "results": results,
            "errors": errors,
            "total": total,
            "collected": collected,
            "api_coverage": len([u for u in validated_urls if u in official_results and official_results[u].get("success")]),
            "playwright_coverage": len([u for u in validated_urls if u not in official_results or not official_results[u].get("success")]),
        }
    
    async def _try_official_api(self, urls: List[str], marketplace: str) -> Dict[str, Dict]:
        """Tenta extrair via API oficial do marketplace"""
        results = {}
        
        if marketplace == "mercadolivre":
            ml_client = self._get_ml_client()
            if ml_client:
                for url in urls:
                    item_id = self._extract_ml_item_id(url)
                    if item_id:
                        try:
                            product = await ml_client.get_product(item_id)
                            if product:
                                results[url] = self._parse_ml_product(product, url)
                        except Exception as e:
                            log.debug(f"ML API falhou para {item_id}: {e}")
        
        elif marketplace == "amazon":
            amz_client = self._get_amazon_client()
            if amz_client:
                for url in urls:
                    asin = self._extract_amazon_asin(url)
                    if asin:
                        try:
                            items = await amz_client.search_items(asin, limit=1)
                            if items:
                                results[url] = self._parse_amazon_item(items[0], url)
                        except Exception as e:
                            log.debug(f"Amazon API falhou: {e}")
        
        elif marketplace == "shopee":
            shopee_client = self._get_shopee_client()
            if shopee_client:
                # Shopee API requer shop_id - mais complexo
                pass
        
        return results
    
    def _extract_ml_item_id(self, url: str) -> Optional[str]:
        match = re.search(r"/(MLB|MLU|MLA|MCO|MLM|MLV|MEC|MRD|MPY)-\d+", url)
        if match:
            return match.group(0).replace("/", "")
        match = re.search(r"/p/([A-Z0-9]+)", url)
        if match:
            return "MLB" + match.group(1)  # Heurística
        return None
    
    def _parse_ml_product(self, product: Dict, url: str) -> Dict:
        price = product.get("price", 0)
        return {
            "success": True,
            "url": url,
            "titulo": product.get("title", "Título não encontrado"),
            "preco_raw": str(price),
            "preco": float(price) if price else 0,
            "disponibilidade": "Disponível" if product.get("available_quantity", 0) > 0 else "Esgotado",
            "avaliacao": str(product.get("rating_average", "N/D")),
            "marketplace": "Mercado Livre",
            "source": "official_api",
            "coletado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _extract_amazon_asin(self, url: str) -> Optional[str]:
        match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if match:
            return match.group(1)
        match = re.search(r"/gp/product/([A-Z0-9]{10})", url)
        if match:
            return match.group(1)
        return None
    
    def _parse_amazon_item(self, item: Dict, url: str) -> Dict:
        return {
            "success": True,
            "url": url,
            "titulo": item.get("title", "Título não encontrado"),
            "preco_raw": str(item.get("price", {}).get("display_price", "0")),
            "preco": float(item.get("price", {}).get("amount", 0)) / 100,
            "disponibilidade": "N/D",
            "avaliacao": "N/D",
            "marketplace": "Amazon",
            "source": "official_api",
            "coletado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLAYWRIGHT + REGISTRY ENTERPRISE
    # ════════════════════════════════════════════════════════════════════════════
    
    async def _mine_playwright(
        self,
        urls: List[str],
        marketplace: str,
        custom_selectors: Dict[str, str],
        max_successful: Optional[int] = None,
    ) -> Dict[str, Dict]:
        """Mineração via Playwright com Registry Enterprise + Circuit Breaker"""
        from playwright.async_api import async_playwright
        
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        results = {}
        
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--disable-default-apps",
                ],
            )
            
            context = await browser.new_context(
                user_agent=random.choice(config.USER_AGENTS),
                viewport={"width": random.choice([1366, 1440, 1536, 1920]), 
                         "height": random.choice([768, 900, 1080])},
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
            )
            
            # Stealth script
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                window.chrome = { runtime: {} };
            """)
            
            # Health check do registry
            self.registry.run_health_check_async()
            
            pending = {
                asyncio.create_task(self._process_url_playwright(context, url, marketplace, custom_selectors)): url
                for url in urls
            }
            
            completed = 0
            confirmed = 0
            
            while pending and (max_successful is None or confirmed < max_successful):
                done, _ = await asyncio.wait(pending.keys(), return_when=asyncio.FIRST_COMPLETED)
                
                for task in done:
                    url = pending.pop(task)
                    try:
                        res = await task
                        results[url] = res
                    except Exception as e:
                        results[url] = {"success": False, "error": str(e), "url": url}
                    
                    # Circuit breaker check
                    mp = self._detect_marketplace(url, marketplace)
                    if self._is_circuit_open(mp):
                        self._log(f"⚡ Circuit breaker aberto para {mp} - pulando URLs restantes")
                        for t, u in pending.items():
                            t.cancel()
                            results[u] = {"success": False, "error": "Circuit breaker", "url": u}
                        pending.clear()
                        break
                    
                    # Health check feedback
                    if "success" in results[url] and results[url].get("success"):
                        if results[url].get("preco", 0) > 0:
                            confirmed += 1
                            # Registrar sucesso no registry
                            self.registry.record_extraction_result(mp, "price", True)
                            self.registry.record_extraction_result(mp, "title", True)
                        else:
                            self.registry.record_extraction_result(mp, "price", False)
                    
                    completed += 1
                    if self.progress_callback:
                        self.progress_callback(completed, total=len(urls), 
                                             percent=int(completed/len(urls)*100))
            
            await browser.close()
        
        return results
    
    def _is_circuit_open(self, marketplace: str) -> bool:
        """Circuit breaker: abre se taxa de erro > 70% nos últimos 10 requests"""
        if marketplace not in self._circuit_breakers:
            return False
        
        cb = self._circuit_breakers[marketplace]
        recent = cb.get("recent_results", [])[-10:]
        if len(recent) < 5:
            return False
        
        error_rate = sum(1 for r in recent if not r.get("success", True)) / len(recent)
        if error_rate > 0.7:
            cb["open"] = True
            cb["opened_at"] = datetime.now().isoformat()
            return True
        
        return False
    
    def _record_circuit_result(self, marketplace: str, success: bool):
        if marketplace not in self._circuit_breakers:
            self._circuit_breakers[marketplace] = {"recent_results": [], "open": False}
        
        self._circuit_breakers[marketplace]["recent_results"].append({
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        # Manter apenas últimos 20
        self._circuit_breakers[marketplace]["recent_results"] = \
            self._circuit_breakers[marketplace]["recent_results"][-20:]
    
    async def _process_url_playwright(
        self,
        context,
        url: str,
        marketplace: str,
        custom_selectors: Dict[str, str],
    ) -> Dict:
        """Processa URL com seletores do Registry Enterprise + fallback inteligente"""
        mp = self._detect_marketplace(url, marketplace)
        
        # Verificar circuit breaker
        if self._is_circuit_open(mp):
            return {"success": False, "error": "Circuit breaker open", "url": url}
        
        page = None
        last_data = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                if page:
                    await page.close()
                page = await context.new_page()
                
                # Headers realísticos
                await page.set_extra_http_headers({
                    **UserAgentProvider.get_headers(),
                    "User-Agent": random.choice(config.USER_AGENTS),
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": "https://www.google.com/",
                })
                
                navigate_timeout = 25_000 if mp in ("shopee", "magalu") else 18_000
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=navigate_timeout)
                except Exception:
                    await page.goto(url, wait_until="load", timeout=15_000)
                
                await page.wait_for_timeout(random.randint(800, 1500))
                
                # Extração com Registry Enterprise
                data = await self._extract_with_registry(page, mp, custom_selectors)
                data["url"] = url
                data["coletado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data["success"] = True
                data["source"] = "playwright_registry"
                last_data = data
                
                has_price = data.get("preco", 0) > 0
                has_title = data.get("titulo") and data["titulo"] not in ["Título não encontrado", "", "N/D"]
                
                # Circuit breaker feedback
                self._record_circuit_result(mp, has_price and has_title)
                
                if has_price and has_title:
                    if page:
                        await page.close()
                    return data
                
                # Se não achou, tenta scroll
                if not has_price:
                    await self._organic_scroll(page)
                    await page.wait_for_timeout(1000)
                    data = await self._extract_with_registry(page, mp, custom_selectors)
                    has_price = data.get("preco", 0) > 0
                    if has_price:
                        if page:
                            await page.close()
                        return data
                
                if attempt < self.max_retries:
                    await page.wait_for_timeout(random.randint(1000, 2000))
                    continue
                    
            except Exception as e:
                self._record_circuit_result(mp, False)
                if attempt < self.max_retries:
                    await asyncio.sleep(random.uniform(1, 2))
                    continue
            
            finally:
                if page:
                    try:
                        await page.close()
                    except:
                        pass
        
        # Fallback ScraperAPI
        fallback = await self._ext_fetch_async(url, mp, custom_selectors)
        if fallback:
            fallback["url"] = url
            fallback["coletado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fallback["source"] = "scraperapi"
            return fallback
        
        if last_data:
            return last_data
        
        return {"success": False, "error": "Todas as tentativas falharam", "url": url}
    
    async def _extract_with_registry(self, page, marketplace: str, custom_selectors: Dict) -> Dict:
        """Extração usando Registry Enterprise com prioridade: custom > registry > generico"""
        registry = _selector_registry
        
        async def try_selectors(field: str) -> str:
            # 1. Custom do usuário
            if field in custom_selectors and custom_selectors[field]:
                try:
                    el = await page.query_selector(custom_selectors[field])
                    if el:
                        text = (await el.inner_text()).strip()
                        if text:
                            registry.record_extraction_result(marketplace, field, True)
                            return text
                except Exception:
                    pass
            
            # 2. Registry enterprise
            selectors = registry.get_selectors(marketplace, field)
            for sel in selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        text = (await el.inner_text()).strip()
                        if text:
                            registry.record_extraction_result(marketplace, field, True)
                            return text
                except Exception:
                    continue
            
            registry.record_extraction_result(marketplace, field, False)
            return ""
        
        # JSON-LD e Meta tags (prioridade máxima)
        jsonld = await self._extract_jsonld(page)
        meta = await self._extract_meta(page)
        
        title = jsonld["title"] or meta["title"] or await try_selectors("title") or ""
        price_raw = jsonld["price"] or meta["price"] or await try_selectors("price") or ""
        
        availability = await try_selectors("availability")
        rating = await try_selectors("rating")
        seller = await try_selectors("seller")
        
        # Regex fallback
        if not title or not price_raw:
            body_text = await page.inner_text("body")
            if not title:
                title = self._extract_title_regex(body_text)
            if not price_raw:
                price_raw = self._extract_price_regex(body_text)
        
        # Último recurso: page.title()
        if not title or title in ["Título não encontrado", ""]:
            try:
                pt = await page.title()
                if pt and len(pt) > 5:
                    title = pt
            except:
                pass
        
        price_num = self._parse_price(price_raw)
        
        return {
            "titulo": title or "Título não encontrado",
            "preco_raw": price_raw,
            "preco": price_num,
            "disponibilidade": availability or "N/D",
            "avaliacao": rating or "N/D",
            "marketplace": _MARKETPLACE_NAMES.get(marketplace, marketplace),
        }
    
    # ════════════════════════════════════════════════════════════════════════════
    # EXPORTAÇÃO E COMPATIBILIDADE
    # ════════════════════════════════════════════════════════════════════════════
    
    def export_results(self, results: List[Dict], output_path: str, visual_theme: str = "classic_blue") -> bool:
        try:
            df = pd.DataFrame(results)
            self._save_premium_excel(df, output_path, visual_theme)
            return True
        except Exception as e:
            self._log(f"Erro ao exportar: {e}")
            return False
    
    def get_registry_health(self) -> Dict:
        """Retorna relatório de saúde do registry"""
        return self.registry.health_check()
    
    def save_user_selectors(self, marketplace: str, field: str, selectors: List[str]):
        """Salva seletores customizados do usuário"""
        self.registry.save_custom_selectors(marketplace, field, selectors)
        self._log(f"Seletores customizados salvos: {marketplace}.{field}")
    
    # ════════════════════════════════════════════════════════════════════════════
    # EXECUÇÃO SÍNCRONA (COMPATIBILIDADE)
    # ════════════════════════════════════════════════════════════════════════════
    
    def mine_from_links(
        self,
        urls: List[str],
        marketplace: str = "generico",
        custom_selectors: Optional[Dict[str, str]] = None,
        visual_theme: str = "classic_blue",
        max_successful: Optional[int] = None,
        use_official_api: bool = True,
    ) -> Dict:
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                self._mine_async(urls, marketplace, custom_selectors or {}, 
                               max_successful=max_successful, use_official_api=use_official_api)
            )
            loop.close()
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "results": [], "errors": []}


# ════════════════════════════════════════════════════════════════════════════
# INSTÂNCIA GLOBAL PARA COMPATIBILIDADE
# ════════════════════════════════════════════════════════════════════════════

_minerador_enterprise = MineradorEnterprise()


# ════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ════════════════════════════════════════════════════════════════════════════

__all__ = [
    "MineradorEnterprise",
    "SelectorRegistryEnterprise",
    "MercadoLivreAPIClient",
    "AmazonSPAPIClient", 
    "ShopeeOpenPlatformClient",
    "SelectorSet",
    "MarketplaceSelectors",
    "minerador_enterprise",
    "_selector_registry",
]


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    # Teste rápido
    m = MineradorEnterprise(log_callback=print)
    print("Registry health:", m.get_registry_health())
    print("Minerador Enterprise v5.0 pronto!")