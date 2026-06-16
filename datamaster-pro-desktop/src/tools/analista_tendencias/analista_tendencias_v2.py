"""
Analista de Tendências Pro v3.0 - Trend Intelligence Engine
Identifica produtos virais e tendências de mercado em tempo real.
Integra Social Search (TikTok/Instagram via Aggregators) e Marketplaces.
"""
import asyncio
import re
import os
import sys
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import Counter

# Importa configurações globais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import config

class AnalistaTendencias:
    """Motor profissional de análise de tendências com Social Intelligence"""
    
    NICHES = {
        "fitness": {
            "name": "Fitness & Saúde",
            "keywords": ["suplemento", "creatina", "whey", "pre-workout", "treino em casa", "garrafa motivacional", "strap academia"],
            "social_query": "fitness trends 2024 gym hacks"
        },
        "beleza": {
            "name": "Beleza & Skincare",
            "keywords": ["skincare", "serum", "maquiagem viral", "coreana", "protetor solar", "gloss", "retinol"],
            "social_query": "skincare routine viral beauty products"
        },
        "tech": {
            "name": "Tecnologia & Gadgets",
            "keywords": ["smartwatch", "fone bluetooth", "teclado mecanico", "setup gamer", "carregador indução", "hub usb"],
            "social_query": "tech gadgets 2024 amazon finds"
        },
        "casa": {
            "name": "Casa & Organização",
            "keywords": ["organizador", "decoração boho", "luminária led", "aspirador robo", "cozinha inteligente", "mdf"],
            "social_query": "home organization hacks 2024 amazon home"
        },
        "pets": {
            "name": "Pet Shop",
            "keywords": ["brinquedo pet", "cama pet", "bebedouro gato", "coleira personalizada", "petisco natural"],
            "social_query": "funny pet products viral dog toys"
        }
    }

    USER_AGENTS = config.USER_AGENTS

    def __init__(self, progress_callback=None, log_callback=None, max_concurrency: int = 3):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.browser = None
        self.context = None
        self.playwright = None

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    async def _init_browser(self):
        from playwright.async_api import async_playwright
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(user_agent=config.get_random_ua("desktop"))

    async def _close_browser(self):
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        self.context = self.browser = self.playwright = None

    async def _scrape_marketplace(self, url: str, selector: str) -> List[str]:
        """Scraper genérico via Playwright para sites dinâmicos"""
        async with self.semaphore:
            page = None
            try:
                page = await self.context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                # Espera um pouco para carregar conteúdo dinâmico (JS)
                await page.wait_for_timeout(2000)
                
                elements = await page.query_selector_all(selector)
                results = []
                for el in elements[:15]:
                    text = await el.inner_text()
                    if text and len(text.strip()) > 5:
                        results.append(text.strip())
                return results
            except Exception as e:
                self._log(f"Erro ao acessar {url[:30]}...: {str(e)[:40]}")
                return []
            finally:
                if page: await page.close()

    async def _analyze_niche_async(self, niche_key: str, custom_query: str = None) -> Dict:
        """Executa a análise completa do nicho de forma assíncrona"""
        if niche_key not in self.NICHES: return {"success": False, "error": "Nicho inválido"}
        
        niche = self.NICHES[niche_key]
        keywords = [custom_query] if custom_query else niche["keywords"][:4]
        
        await self._init_browser()
        self._log(f"Iniciando inteligência de mercado para: {niche['name']}...")
        
        tasks = []
        # Fontes de Dados
        for kw in keywords:
            kw_clean = kw.replace(" ", "+")
            # Mercado Livre
            tasks.append(self._scrape_marketplace(
                f"https://lista.mercadolivre.com.br/{kw_clean}", 
                "h2.poly-box" # Seletor atualizado ML
            ))
            # Amazon Brasil
            tasks.append(self._scrape_marketplace(
                f"https://www.amazon.com.br/s?k={kw_clean}", 
                "h2 span"
            ))
            # Social Search (Google Dorking para TikTok Trends)
            tasks.append(self._scrape_marketplace(
                f"https://www.google.com/search?q=site:tiktok.com+{kw_clean}+viral+products", 
                "h3"
            ))

        # Executa tudo em paralelo
        raw_results = await asyncio.gather(*tasks)
        
        # Consolidação de Dados
        product_counter = Counter()
        product_platforms = {}  # Track which platforms each product appears on
        for batch_idx, batch in enumerate(raw_results):
            platform_name = ["Mercado Livre", "Amazon", "TikTok"][batch_idx % 3] if len(raw_results) > 3 else ["Mercado Livre", "Amazon", "TikTok"][batch_idx]
            for title in batch:
                # Limpeza simples de títulos
                clean_title = re.sub(r'[^a-zA-Z0-9áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]', '', title)
                # Tenta extrair a marca/nome principal (primeiras 4-5 palavras)
                short_name = " ".join(clean_title.split()[:5])
                if len(short_name) > 10:
                    product_counter[short_name] += 1
                    if short_name not in product_platforms:
                        product_platforms[short_name] = set()
                    product_platforms[short_name].add(platform_name)

        # Calcula total de resultados para normalização
        total_results = sum(product_counter.values()) or 1

        trends = []
        for name, count in product_counter.most_common(15):
            # Score baseado na frequência real (0-100)
            frequency_score = (count / total_results) * 100
            # Bônus por aparecer em múltiplas plataformas
            platform_count = len(product_platforms.get(name, set()))
            platform_bonus = (platform_count - 1) * 15  # +15 por plataforma extra
            score = min(int(frequency_score + platform_bonus), 100)

            # Growth estimado: proporção de aparições vs média esperada
            avg_per_product = total_results / max(len(product_counter), 1)
            growth_ratio = count / avg_per_product if avg_per_product > 0 else 1
            growth_pct = int((growth_ratio - 1) * 100)
            growth_str = f"+{growth_pct}%" if growth_pct > 0 else f"{growth_pct}%"

            trends.append({
                "product": name,
                "growth": growth_str,
                "score": score,
                "opportunity": "Alta" if score > 75 else "Média" if score > 50 else "Baixa",
                "platforms": list(product_platforms.get(name, set())),
                "mentions": count,
            })

        await self._close_browser()
        
        return {
            "success": True,
            "niche": niche["name"],
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "trends": sorted(trends, key=lambda x: x["score"], reverse=True),
            "summary": f"Detectamos {len(trends)} produtos com alto volume de buscas e engajamento social."
        }

    def analyze(self, niche_key: str, query: str = None) -> Dict:
        """Ponto de entrada síncrono para a GUI"""
        try:
            return asyncio.run(self._analyze_niche_async(niche_key, query))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(self._analyze_niche_async(niche_key, query))

    def get_available_niches(self) -> List[Dict]:
        return [{"key": k, "name": v["name"]} for k, v in self.NICHES.items()]

if __name__ == "__main__":
    analista = AnalistaTendencias(log_callback=print)
    res = analista.analyze("tech")
    print(res)