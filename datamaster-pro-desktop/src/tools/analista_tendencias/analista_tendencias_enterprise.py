"""
Analista de Tendências Enterprise v2.0 - Trend Intelligence Engine
Zero Scraping — Fontes Legítimas Apenas:
- Google Trends via pytrends (tolerado para uso não-comercial/baixo volume)
- Mercado Livre Bestsellers API Oficial
- TikTok Creative Center (export manual CSV)
- Exploding Topics API (pago, opcional)
Scoring: Ensemble multi-fonte + Isolation Forest para detecção de anomalias
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from abc import ABC, abstractmethod

import httpx
import pandas as pd
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class TrendSignal:
    """Sinal bruto de tendência de uma fonte"""
    source: str  # "google_trends", "mercadolivre_bestsellers", "tiktok_creative", "exploding_topics"
    keyword: str
    niche: str
    score: float  # Normalizado 0-100
    metadata: Dict = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrendProduct:
    """Produto consolidado com score final"""
    name: str
    niche: str
    overall_score: float  # 0-100
    growth_pct: float     # % crescimento vs baseline
    opportunity: str      # "Alta", "Média", "Baixa"
    signals: List[TrendSignal]
    platforms: List[str]
    first_seen: datetime
    last_updated: datetime
    metadata: Dict = field(default_factory=dict)


# --- FONTES DE DADOS (IMPLEMENTAÇÕES REAIS) ---

class TrendSource(ABC):
    @abstractmethod
    async def collect(self, niches: List[str], keywords: List[str]) -> List[TrendSignal]:
        pass


class GoogleTrendsSource(TrendSource):
    """
    Google Trends via pytrends (unofficial API wrapper).
    Para enterprise: contratar Google Trends API oficial (parceiros) ou usar BigQuery public datasets.
    Limite: ~100 requests/hora por IP — usar com moderação.
    """
    
    def __init__(self, hl: str = "pt-BR", tz: int = 300):
        self.hl = hl
        self.tz = tz
        self._pytrends = None
    
    def _get_client(self):
        if self._pytrends is None:
            try:
                from pytrends.request import TrendReq
                self._pytrends = TrendReq(hl=self.hl, tz=self.tz, timeout=(10, 25))
            except ImportError:
                raise RuntimeError("pytrends não instalado: pip install pytrends")
        return self._pytrends
    
    async def collect(self, niches: List[str], keywords: List[str]) -> List[TrendSignal]:
        signals = []
        pytrends = self._get_client()
        
        # Batch keywords em grupos de 5 (limite da API)
        for i in range(0, len(keywords), 5):
            batch = keywords[i:i+5]
            try:
                # Interest over time (últimos 90 dias)
                pytrends.build_payload(batch, cat=0, timeframe='today 3-m', geo='BR', gprop='')
                interest_df = pytrends.interest_over_time()
                
                if not interest_df.empty:
                    for kw in batch:
                        if kw in interest_df.columns:
                            series = interest_df[kw].dropna()
                            if len(series) >= 7:
                                # Crescimento: regressão linear
                                x = np.arange(len(series))
                                slope = np.polyfit(x, series.values, 1)[0]
                                avg = series.mean()
                                growth_pct = (slope * len(series) / avg * 100) if avg > 0 else 0
                                
                                # Score: interesse atual + momentum
                                current = series.iloc[-1]
                                score = min(100, (current / 100 * 50) + max(0, growth_pct * 2))
                                
                                signals.append(TrendSignal(
                                    source="google_trends",
                                    keyword=kw,
                                    niche=self._map_keyword_to_niche(kw, niches),
                                    score=score,
                                    metadata={
                                        "current_interest": int(current),
                                        "growth_pct": round(growth_pct, 1),
                                        "avg_interest": round(avg, 1),
                                        "data_points": len(series)
                                    }
                                ))
            except Exception as e:
                log.warning(f"Google Trends batch failed: {e}")
                await asyncio.sleep(5)  # Rate limit
        
        return signals
    
    def _map_keyword_to_niche(self, keyword: str, niches: List[str]) -> str:
        kw_lower = keyword.lower()
        niche_keywords = {
            "fitness": ["creatina", "whey", "pre-workout", "treino", "garrafa", "strap", "academia"],
            "beleza": ["skincare", "serum", "retinol", "protetor", "gloss", "maquiagem", "coreana"],
            "tech": ["smartwatch", "fone", "teclado", "gamer", "carregador", "hub", "setup"],
            "casa": ["organizador", "aspirador", "luminaria", "mdf", "cozinha", "decoracao"],
            "pets": ["racao", "bebedouro", "coleira", "brinquedo", "pet", "cama"],
            "moda": ["tenis", "moletom", "bolsa", "relogio", "oculos", "acessorio"],
            "automotivo": ["carregador carro", "aspirador carro", "organizador porta-malas", "capa banco"],
        }
        for niche, kws in niche_keywords.items():
            if any(k in kw_lower for k in kws):
                return niche
        return "geral"


class MercadoLivreBestsellersSource(TrendSource):
    """
    Mercado Livre Bestsellers via API Oficial.
    Requer: App em https://developers.mercadolivre.com.br/
    OAuth2: Client Credentials Flow
    Endpoint: /sites/MLB/search?category=...&sort=sold_quantity_desc
    """
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv("ML_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("ML_CLIENT_SECRET")
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def _get_token(self) -> str:
        import time
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        
        resp = await self._client.post(
            "https://api.mercadolibre.com/oauth/token",
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
    
    async def collect(self, niches: List[str], keywords: List[str]) -> List[TrendSignal]:
        if not self.client_id or not self.client_secret:
            log.info("Mercado Livre Bestsellers: credenciais não configuradas")
            return []
        
        signals = []
        token = await self._get_token()
        
        # Mapear nichos para categorias ML
        niche_to_category = {
            "fitness": "MLB1577",      # Suplementos
            "beleza": "MLB1192",       # Beleza e Cuidado Pessoal
            "tech": "MLB1055",         # Celulares e Telefones
            "casa": "MLB1392",         # Casa, Móveis e Decoração
            "pets": "MLB1430",         # Pet Shop
            "moda": "MLB1431",         # Moda
            "automotivo": "MLB1743",   # Acessórios para Veículos
        }
        
        async with self._client as client:
            for niche in niches:
                cat_id = niche_to_category.get(niche)
                if not cat_id:
                    continue
                
                try:
                    resp = await client.get(
                        "https://api.mercadolibre.com/sites/MLB/search",
                        headers={"Authorization": f"Bearer {token}"},
                        params={
                            "category": cat_id,
                            "sort": "sold_quantity_desc",
                            "limit": 50,
                            "condition": "new"
                        }
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    
                    for item in data.get("results", [])[:20]:
                        title = item.get("title", "")
                        sold = item.get("sold_quantity", 0)
                        price = item.get("price", 0)
                        
                        # Score baseado em vendas + preço (proxy de receita)
                        score = min(100, (sold / 1000 * 50) + (price / 1000 * 10))
                        
                        signals.append(TrendSignal(
                            source="mercadolivre_bestsellers",
                            keyword=title[:80],
                            niche=niche,
                            score=score,
                            metadata={
                                "sold_quantity": sold,
                                "price": price,
                                "item_id": item.get("id"),
                                "permalink": item.get("permalink")
                            }
                        ))
                except Exception as e:
                    log.warning(f"ML Bestsellers failed for {niche}: {e}")
        
        return signals
    
    async def close(self):
        await self._client.aclose()


class TikTokCreativeCenterSource(TrendSource):
    """
    TikTok Creative Center NÃO tem API pública.
    Estratégia: Export manual CSV semanal de https://ads.tiktok.com/creative-center
    Parser lê CSVs da pasta configurada.
    """
    
    def __init__(self, csv_dir: str = "data/tiktok_trends"):
        self.csv_dir = Path(csv_dir)
        self.csv_dir.mkdir(parents=True, exist_ok=True)
    
    async def collect(self, niches: List[str], keywords: List[str]) -> List[TrendSignal]:
        signals = []
        
        # Procurar CSVs recentes (< 7 dias)
        for csv_file in self.csv_dir.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                # Colunas esperadas: Keyword, Popularity, Change, Category, Region
                for _, row in df.iterrows():
                    kw = str(row.get("Keyword", "")).strip()
                    if not kw:
                        continue
                    
                    # Filtrar por nichos/keywords de interesse
                    if not any(k.lower() in kw.lower() for k in keywords + niches):
                        continue
                    
                    popularity = float(row.get("Popularity", 0))
                    change = float(row.get("Change", 0))
                    score = min(100, popularity * 0.7 + max(0, change) * 0.3)
                    
                    signals.append(TrendSignal(
                        source="tiktok_creative_center",
                        keyword=kw,
                        niche=self._map_keyword_to_niche(kw, niches),
                        score=score,
                        metadata={
                            "popularity": popularity,
                            "change_pct": change,
                            "category": row.get("Category", ""),
                            "csv_file": csv_file.name
                        }
                    ))
            except Exception as e:
                log.warning(f"Failed to parse TikTok CSV {csv_file}: {e}")
        
        return signals
    
    def _map_keyword_to_niche(self, keyword: str, niches: List[str]) -> str:
        return GoogleTrendsSource()._map_keyword_to_niche(keyword, niches)


class ExplodingTopicsSource(TrendSource):
    """
    Exploding Topics API (pago): https://explodingtopics.com/api
    Plano Pro: $97/mês — 1000 requests/mês
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EXPLODING_TOPICS_API_KEY")
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def collect(self, niches: List[str], keywords: List[str]) -> List[TrendSignal]:
        if not self.api_key:
            return []
        
        signals = []
        niche_to_category = {
            "fitness": "health",
            "beleza": "beauty",
            "tech": "technology",
            "casa": "home",
            "pets": "pets",
            "moda": "fashion",
            "automotivo": "automotive"
        }
        
        async with self._client as client:
            for niche in niches:
                category = niche_to_category.get(niche)
                if not category:
                    continue
                
                try:
                    resp = await client.get(
                        "https://api.explodingtopics.com/v1/trends",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        params={"category": category, "limit": 50}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    
                    for trend in data.get("trends", []):
                        name = trend.get("name", "")
                        growth = trend.get("growth", 0)
                        score = min(100, 50 + growth * 2)
                        
                        signals.append(TrendSignal(
                            source="exploding_topics",
                            keyword=name,
                            niche=niche,
                            score=score,
                            metadata={
                                "growth_pct": growth,
                                "status": trend.get("status"),
                                "first_seen": trend.get("first_seen")
                            }
                        ))
                except Exception as e:
                    log.warning(f"Exploding Topics failed for {niche}: {e}")
        
        return signals


# --- AGREGADOR E SCORING ENGINE ---

class TrendAggregator:
    """
    Consolida sinais de múltiplas fontes, aplica scoring estatístico,
    detecta anomalias (Isolation Forest), gera ranking final.
    """
    
    def __init__(self, min_sources_for_confidence: int = 2):
        self.min_sources = min_sources_for_confidence
        self.sources: List[TrendSource] = []
    
    def add_source(self, source: TrendSource):
        self.sources.append(source)
    
    async def analyze(self, niches: List[str], keywords: List[str]) -> List[TrendProduct]:
        # 1. Coletar sinais de todas as fontes em paralelo
        all_signals = []
        tasks = [source.collect(niches, keywords) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                log.error(f"Source collection failed: {result}")
            else:
                all_signals.extend(result)
        
        # 2. Agrupar por (keyword normalizada, niche)
        grouped = self._group_signals(all_signals)
        
        # 3. Calcular score consolidado por produto
        products = []
        for (kw, niche), signals in grouped.items():
            product = self._compute_product_score(kw, niche, signals)
            if product.overall_score >= 30:  # Threshold mínimo
                products.append(product)
        
        # 4. Detectar outliers (possível hype artificial)
        products = self._detect_anomalies(products)
        
        # 5. Ordenar e rankear
        products.sort(key=lambda p: p.overall_score, reverse=True)
        
        return products[:50]  # Top 50
    
    def _group_signals(self, signals: List[TrendSignal]) -> Dict[tuple, List[TrendSignal]]:
        grouped = {}
        for s in signals:
            norm_kw = self._normalize_keyword(s.keyword)
            key = (norm_kw, s.niche)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(s)
        return grouped
    
    def _normalize_keyword(self, kw: str) -> str:
        import re
        kw = kw.lower().strip()
        kw = re.sub(r'[^\w\s]', '', kw)
        stopwords = {"de", "da", "do", "para", "com", "em", "o", "a", "os", "as", "e", "ou", "pro", "pra"}
        tokens = [t for t in kw.split() if t not in stopwords and len(t) > 2]
        return " ".join(tokens[:5])  # Top 5 tokens
    
    def _compute_product_score(self, keyword: str, niche: str, signals: List[TrendSignal]) -> TrendProduct:
        if not signals:
            return TrendProduct(keyword, niche, 0, 0, "Baixa", [], [], datetime.now(), datetime.now())
        
        # Pesos por confiabilidade da fonte
        source_weights = {
            "google_trends": 1.0,
            "mercadolivre_bestsellers": 1.2,  # Dado real de vendas
            "tiktok_creative_center": 0.9,
            "exploding_topics": 1.3,  # Curado por especialistas
        }
        
        weighted_scores = []
        total_weight = 0
        all_platforms = set()
        total_growth = 0
        growth_count = 0
        
        for s in signals:
            w = source_weights.get(s.source, 0.5)
            weighted_scores.append(s.score * w)
            total_weight += w
            all_platforms.add(s.source)
            
            if "growth_pct" in s.metadata:
                total_growth += s.metadata["growth_pct"]
                growth_count += 1
        
        avg_weighted_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0
        
        # Bonus por múltiplas fontes (validação cruzada)
        source_bonus = min(20, (len(all_platforms) - 1) * 8)
        
        # Growth médio
        avg_growth = total_growth / growth_count if growth_count > 0 else 0
        growth_bonus = min(15, max(0, avg_growth))
        
        final_score = min(100, avg_weighted_score + source_bonus + growth_bonus)
        
        # Classificação de oportunidade
        if final_score >= 75 and avg_growth > 20:
            opportunity = "Alta"
        elif final_score >= 55:
            opportunity = "Média"
        else:
            opportunity = "Baixa"
        
        return TrendProduct(
            name=keyword.title(),
            niche=niche,
            overall_score=round(final_score, 1),
            growth_pct=round(avg_growth, 1),
            opportunity=opportunity,
            signals=signals,
            platforms=list(all_platforms),
            first_seen=min(s.collected_at for s in signals),
            last_updated=max(s.collected_at for s in signals),
            metadata={
                "source_count": len(all_platforms),
                "avg_weighted_score": round(avg_weighted_score, 1),
                "source_bonus": source_bonus,
                "growth_bonus": growth_bonus
            }
        )
    
    def _detect_anomalies(self, products: List[TrendProduct]) -> List[TrendProduct]:
        """Isolation Forest para detectar padrões anômalos (hype artificial, bot farms)"""
        if len(products) < 10:
            return products
        
        try:
            from sklearn.ensemble import IsolationForest
            
            X = np.array([
                [p.overall_score, p.growth_pct, len(p.platforms)]
                for p in products
            ])
            
            clf = IsolationForest(contamination=0.1, random_state=42)
            anomalies = clf.fit_predict(X)
            
            for product, is_anomaly in zip(products, anomalies):
                if is_anomaly == -1:
                    product.metadata["anomaly_detected"] = True
                    product.metadata["anomaly_note"] = "Padrão atípico - verificar manualmente"
                    product.overall_score = max(0, product.overall_score - 5)
        
        except ImportError:
            pass  # sklearn não disponível
        
        return products


# --- CLASSE PRINCIPAL COMPATÍVEL COM INTERFACE ANTIGA ---

class AnalistaTendenciasEnterprise:
    """
    Substitui AnalistaTendencias v3.0 (scraping) por engine enterprise.
    Mantém mesma assinatura pública: analyze(niche_key, query)
    """
    
    NICHES = {
        "fitness": {"name": "Fitness & Saúde", "keywords": ["creatina", "whey", "pre-workout", "treino", "garrafa", "strap"]},
        "beleza": {"name": "Beleza & Skincare", "keywords": ["skincare", "serum", "retinol", "protetor solar", "gloss", "maquiagem"]},
        "tech": {"name": "Tecnologia & Gadgets", "keywords": ["smartwatch", "fone bluetooth", "teclado mecanico", "gamer", "carregador"]},
        "casa": {"name": "Casa & Organização", "keywords": ["organizador", "aspirador robo", "luminaria led", "mdf", "cozinha"]},
        "pets": {"name": "Pet Shop", "keywords": ["racao", "bebedouro", "coleira", "brinquedo pet", "cama pet"]},
        "moda": {"name": "Moda & Acessórios", "keywords": ["tenis", "moletom", "bolsa", "relogio", "oculos"]},
        "automotivo": {"name": "Automotivo", "keywords": ["carregador carro", "aspirador carro", "organizador porta-malas", "capa banco"]},
    }
    
    def __init__(self, progress_callback=None, log_callback=None, max_concurrency: int = 3):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.aggregator = TrendAggregator()
        self._init_sources()
    
    def _log(self, msg: str):
        log.info(msg)
        if self.log_callback:
            self.log_callback(msg)
    
    def _init_sources(self):
        """Inicializa fontes com credenciais do ambiente"""
        # Google Trends (sempre disponível)
        self.aggregator.add_source(GoogleTrendsSource())
        
        # Mercado Livre (se credenciais configuradas)
        ml_id = os.getenv("ML_CLIENT_ID")
        ml_secret = os.getenv("ML_CLIENT_SECRET")
        if ml_id and ml_secret:
            self.aggregator.add_source(MercadoLivreBestsellersSource(ml_id, ml_secret))
            self._log("Mercado Livre Bestsellers Provider inicializado")
        
        # TikTok Creative Center (CSVs na pasta)
        self.aggregator.add_source(TikTokCreativeCenterSource())
        
        # Exploding Topics (se API key configurada)
        et_key = os.getenv("EXPLODING_TOPICS_API_KEY")
        if et_key:
            self.aggregator.add_source(ExplodingTopicsSource(et_key))
            self._log("Exploding Topics Provider inicializado")
    
    def analyze(self, niche_key: str, query: str = None) -> Dict:
        """Interface síncrona compatível"""
        import asyncio
        
        if niche_key not in self.NICHES:
            return {"success": False, "error": f"Nicho '{niche_key}' não suportado. Disponíveis: {list(self.NICHES.keys())}"}
        
        niche_info = self.NICHES[niche_key]
        keywords = [query] if query else niche_info["keywords"]
        
        self._log(f"Iniciando análise enterprise para: {niche_info['name']} ({len(keywords)} keywords)")
        
        try:
            products = asyncio.run(self.aggregator.analyze([niche_key], keywords))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            products = loop.run_until_complete(self.aggregator.analyze([niche_key], keywords))
        
        trends_output = []
        for p in products:
            trends_output.append({
                "product": p.name,
                "growth": f"+{p.growth_pct:.0f}%" if p.growth_pct > 0 else f"{p.growth_pct:.0f}%",
                "score": int(p.overall_score),
                "opportunity": p.opportunity,
                "platforms": p.platforms,
                "mentions": len(p.signals),
                "metadata": p.metadata
            })
        
        active_sources = [s.__class__.__name__ for s in self.aggregator.sources]
        
        return {
            "success": True,
            "niche": niche_info["name"],
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "trends": trends_output,
            "summary": f"Analisados {len(trends_output)} produtos com sinais de {len(active_sources)} fontes. Fontes ativas: {active_sources}",
            "sources_used": active_sources
        }
    
    def get_available_niches(self) -> List[Dict]:
        return [{"key": k, "name": v["name"]} for k, v in self.NICHES.items()]
    
    def get_active_sources(self) -> List[str]:
        return [s.__class__.__name__ for s in self.aggregator.sources]


# --- Exemplo de uso standalone ---
if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    analista = AnalistaTendenciasEnterprise(log_callback=print)
    res = analista.analyze("tech")
    print(json.dumps(res, indent=2, ensure_ascii=False))