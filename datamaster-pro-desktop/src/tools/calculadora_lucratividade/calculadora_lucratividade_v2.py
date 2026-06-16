"""
Calculadora de Lucratividade e Arbitragem v3.2 Pro
Motor com Telemetria Avançada e Logs de Terminal em Tempo Real.
"""
import asyncio
import logging
import re
import os
import sys
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

log = logging.getLogger(__name__)

# Importa configurações globais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import config

class CalculadoraLucratividade:
    """Calculadora profissional com telemetria de extração e logs de terminal"""
    
    MARKETPLACE_FEES = {
        "mercadolivre": {"percent": 0.16, "fixed": 6.00},
        "amazon": {"percent": 0.15, "fixed": 2.00},
        "shopee": {"percent": 0.14, "fixed": 3.00},
        "magalu": {"percent": 0.18, "fixed": 5.00},
        "aliexpress": {"percent": 0.10, "fixed": 0.00},
        "other": {"percent": 0.15, "fixed": 0.00}
    }

    # Seletores de preço atualizados 2024/2025
    PRICE_SELECTORS = [
        ".ui-pdp-price__second-line .andes-money-amount__fraction",
        ".ui-pdp-price__fraction",
        ".price-tag-amount",
        ".a-price .a-offscreen",
        ".a-price-whole",
        ".shopee-product-rating",
        "[data-testid='price-value']",
        ".andes-money-amount__fraction",
        ".vtex-product-price-0-x-currencyInteger"
    ]

    def __init__(self, progress_callback=None, log_callback=None, max_concurrency: int = 3):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def _log(self, message: str):
        """Log que sai no Terminal e na GUI simultaneamente"""
        log.info(message)
        if self.log_callback:
            self.log_callback(message)

    async def _extract_price_from_page(self, page) -> Optional[float]:
        """Tenta extrair o preço usando telemetria multi-nível"""
        
        # Nível 1: Metadados JSON-LD
        self._log("🔍 Verificando metadados JSON-LD...")
        try:
            scripts = await page.query_selector_all('script[type="application/ld+json"]')
            for script in scripts:
                content = await script.inner_text()
                if not content: continue
                data = json.loads(content)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    offers = item.get("offers")
                    if isinstance(offers, dict):
                        price = offers.get("price")
                        if price:
                            self._log(f"✅ Preço encontrado via JSON-LD: {price}")
                            return self._clean_price(str(price))
        except Exception: pass

        # Nível 2: Seletores CSS
        self._log(f"🔍 Testando {len(self.PRICE_SELECTORS)} seletores CSS...")
        for selector in self.PRICE_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text:
                        self._log(f"📍 Seletor '{selector}' encontrou: '{text.strip()}'")
                        if "mercadolivre" in page.url:
                            cents_el = await page.query_selector(".andes-money-amount__cents")
                            if cents_el:
                                cents = await cents_el.inner_text()
                                text = f"{text.strip()},{cents.strip()}"
                        
                        price = self._clean_price(text)
                        if price and price > 1: return price
            except Exception: continue

        # Nível 3: Meta tags
        self._log("🔍 Verificando Meta Tags SEO...")
        try:
            meta_price = await page.query_selector('meta[property="product:price:amount"]')
            if meta_price:
                val = await meta_price.get_attribute("content")
                if val: 
                    self._log(f"✅ Preço via Meta Tag: {val}")
                    return self._clean_price(val)
        except Exception: pass

        # Nível 4: Regex Deep Scan
        self._log("🔍 Iniciando Deep Scan (Regex)...")
        content = await page.content()
        if "captcha" in content.lower() or "robot" in content.lower():
            self._log("🚨 BLOQUEIO: O site detectou o robô e pediu Captcha.")
            return None

        clean_text = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)
        matches = re.findall(r'R\$\s?([\d\.]+,\d{2})', clean_text)
        if matches:
            for m in matches:
                p = self._clean_price(m)
                if p and p > 1:
                    self._log(f"🎯 Capturado via Regex: {p}")
                    return p

        return None

    def _clean_price(self, price_str: str) -> Optional[float]:
        if not price_str: return None
        try:
            clean = re.sub(r'[^\d,.]', '', price_str)
            if ',' in clean and '.' in clean:
                clean = clean.replace('.', '').replace(',', '.')
            elif ',' in clean:
                clean = clean.replace(',', '.')
            val = float(clean)
            return val if val > 0 else None
        except Exception: return None

    async def _process_single_url(self, context, url: str) -> Dict:
        async with self.semaphore:
            max_retries = 2
            for attempt in range(max_retries):
                page = None
                try:
                    page = await context.new_page()
                    ua = config.get_random_ua("desktop")
                    await page.set_extra_http_headers({
                        "User-Agent": ua,
                        "Accept-Language": "pt-BR,pt;q=0.9",
                        "Referer": "https://www.google.com/"
                    })
                    
                    self._log(f"🌐 Navegando até: {url[:40]}...")
                    await page.goto(url, wait_until="load", timeout=45000)
                    await page.wait_for_timeout(3000) 

                    price = await self._extract_price_from_page(page)
                    site = self._detect_marketplace(url)
                    
                    return {"url": url, "price": price, "site": site, "success": True if price else False}
                except Exception as e:
                    if attempt < max_retries - 1:
                        self._log(f"⚠️ Tentativa {attempt + 1} falhou para {url[:30]}: {str(e)[:40]}. Retentando...")
                        if page:
                            await page.close()
                            page = None
                        continue
                    self._log(f"🛑 Erro em {url[:30]}: {str(e)[:50]}")
                    return {"url": url, "price": None, "site": "unknown", "success": False, "error": str(e)}
                finally:
                    if page: await page.close()

    def _detect_marketplace(self, url: str) -> str:
        url_lower = url.lower()
        for key in self.MARKETPLACE_FEES.keys():
            if key in url_lower: return key
        return "other"

    async def calculate_async(self, cost_price: float, urls: List[str]) -> Dict:
        from playwright.async_api import async_playwright
        
        self._log("🚀 MOTOR PLAYWRIGHT INICIADO - Carregando motor de busca...")
        
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            tasks = [self._process_single_url(context, url) for url in urls]
            
            completed = 0
            for task in asyncio.as_completed(tasks):
                res = await task
                results.append(res)
                completed += 1
                if self.progress_callback:
                    self.progress_callback(int((completed / len(urls)) * 100))
            
            await browser.close()

        final_results = [r for r in results if r["success"]]
        if not final_results:
            return {"success": False, "error": "Preços não capturados. Verifique os logs do terminal."}

        # Processamento Financeiro
        processed = []
        for r in final_results:
            price = r["price"]
            site = r["site"]
            fee = self.MARKETPLACE_FEES.get(site, self.MARKETPLACE_FEES["other"])
            tax = (price * fee["percent"]) + fee["fixed"]
            profit = price - cost_price - tax
            margin = (profit / price * 100) if price > 0 else 0
            roi = (profit / cost_price * 100) if cost_price > 0 else 0
            
            processed.append({
                **r,
                "marketplace_tax": round(tax, 2),
                "net_profit": round(profit, 2),
                "margin": round(margin, 1),
                "roi": round(roi, 1),
                "opportunity_score": min(max(int((margin * 2.5) + (roi / 2)), 0), 100)
            })

        processed.sort(key=lambda x: x["net_profit"], reverse=True)
        return {
            "success": True,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "cost_price": cost_price,
            "results": processed,
            "best_opportunity": processed[0],
            "summary": f"Oportunidade em {processed[0]['site'].upper()} com R$ {processed[0]['net_profit']} de lucro."
        }

    def calculate(self, cost_price: float, urls: List[str]) -> Dict:
        try:
            return asyncio.run(self.calculate_async(cost_price, urls))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(self.calculate_async(cost_price, urls))
