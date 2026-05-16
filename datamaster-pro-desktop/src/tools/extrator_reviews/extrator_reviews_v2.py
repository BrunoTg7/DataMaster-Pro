"""
Extrator de Reviews Pro v3.2
Motor com Análise de Sentimento Individual e Telemetria de Scroll.
"""
import asyncio
import re
import random
import os
import sys
from typing import List, Dict, Optional, Any
from datetime import datetime

# Importa configurações globais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import config

class ExtratorReviews:
    """Extrai e analisa reviews de produtos usando navegação dinâmica"""

    def __init__(self, api_key: str = "", progress_callback=None, log_callback=None, max_concurrency: int = 2):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def _log(self, message: str):
        print(f"[Extrator] {message}", flush=True)
        if self.log_callback:
            self.log_callback(message)

    SENTIMENT_DICT = {
        "positive": [
            "bom", "ótimo", "excelente", "perfeito", "maravilhoso", "recomendo", "gostei", 
            "rápido", "qualidade", "top", "lindo", "original", "atendeu", "surpreso",
            "fácil", "baixo custo", "vale a pena", "satisfeito", "impecável", "entrega rápida"
        ],
        "negative": [
            "ruim", "péssimo", "horrível", "defeito", "quebrou", "lixo", "não recomendo",
            "decepção", "devolver", "problema", "atraso", "falha", "fraco", "pior",
            "falso", "pirata", "parou de funcionar", "estragou", "caro", "insatisfeito", "paraguaio"
        ]
    }

    async def _extract_reviews_playwright(self, page, max_reviews: int) -> List[Dict]:
        self._log("Scrolling para carregar reviews dinâmicos...")
        for i in range(3):
            await page.evaluate(f"window.scrollBy(0, {800 + (i*200)})")
            await page.wait_for_timeout(1500)

        reviews = []
        selectors = [
            ".ui-review-capability-comments__comment__content",
            ".ui-review-capability-comments__comment",
            ".review-text-content",
            ".shopee-product-rating__comment",
            ".review-content",
            "[data-testid='review-text']"
        ]

        found_elements = []
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    found_elements.extend(elements)
                    self._log(f"Encontrados {len(elements)} elementos em '{selector}'")
            except: continue

        for el in found_elements:
            try:
                text = await el.inner_text()
                text = text.strip()
                if len(text) > 15 and text not in [r['text'] for r in reviews]:
                    sentiment_res = self._analyze_text_sentiment(text)
                    reviews.append({
                        "text": text[:500],
                        "sentiment": sentiment_res["label"],
                        "date": datetime.now().strftime("%d/%m/%Y")
                    })
            except: continue
            if len(reviews) >= max_reviews: break
        
        return reviews

    def _analyze_text_sentiment(self, text: str) -> Dict:
        t = text.lower()
        pos_score = sum(1 for word in self.SENTIMENT_DICT["positive"] if word in t)
        neg_score = sum(1 for word in self.SENTIMENT_DICT["negative"] if word in t)
        label = "neutral"
        if pos_score > neg_score: label = "positive"
        elif neg_score > pos_score: label = "negative"
        return {"label": label, "pos": pos_score, "neg": neg_score}

    async def _process_url(self, context, url: str, max_reviews: int) -> Dict:
        async with self.semaphore:
            page = None
            try:
                page = await context.new_page()
                ua = config.get_random_ua("desktop")
                await page.set_extra_http_headers({"User-Agent": ua})
                
                self._log(f"🔍 Analisando: {url[:40]}...")
                await page.goto(url, wait_until="load", timeout=60000)
                await page.wait_for_timeout(2000)

                site_name = "Mercado Livre" if "mercadolivre" in url else "Amazon" if "amazon" in url else "Shopee" if "shopee" in url else "Loja"
                reviews = await self._extract_reviews_playwright(page, max_reviews)
                
                pos = sum(1 for r in reviews if r['sentiment'] == 'positive')
                neg = sum(1 for r in reviews if r['sentiment'] == 'negative')
                neu = sum(1 for r in reviews if r['sentiment'] == 'neutral')
                total = len(reviews)
                score = ((pos - neg) / total * 100) if total > 0 else 0
                
                return {
                    "success": True,
                    "site": site_name,
                    "url": url,
                    "reviews": reviews,
                    "total_reviews": total,
                    "sentiment": "positive" if score > 15 else "negative" if score < -15 else "neutral",
                    "positive": pos,
                    "negative": neg,
                    "neutral": neu,
                    "score": round(score, 1)
                }
            except Exception as e:
                self._log(f"🛑 Erro em {url[:30]}: {str(e)}")
                return {"success": False, "error": str(e), "url": url}
            finally:
                if page: await page.close()

    async def analyze_multiple_async(self, urls: List[str], max_reviews: int = 15) -> Dict:
        from playwright.async_api import async_playwright
        self._log(f"🚀 Iniciando extração de {len(urls)} produtos...")
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            tasks = [self._process_url(context, url, max_reviews) for url in urls]
            completed = 0
            for task in asyncio.as_completed(tasks):
                res = await task
                results.append(res)
                completed += 1
                if self.progress_callback:
                    self.progress_callback(int((completed / len(urls)) * 100))
            await browser.close()

        successful = [r for r in results if r.get("success")]
        return {
            "success": True,
            "results": results,
            "total": len(urls),
            "analyzed": len(successful),
            "summary": "Processamento concluído."
        }

    def analyze_multiple(self, urls: List[str], max_reviews: int = 15) -> Dict:
        try:
            return asyncio.run(self.analyze_multiple_async(urls, max_reviews))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(self.analyze_multiple_async(urls, max_reviews))