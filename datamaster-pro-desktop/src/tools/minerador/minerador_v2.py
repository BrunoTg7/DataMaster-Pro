"""
Minerador Pro v3.1 - Sistema Híbrido de Mineração e Rastreio
Suporte a: Busca por Palavra-Chave, Listas de Links e Arquivos Excel/CSV.
"""
import asyncio
import re
import random
import os
import sys
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any

# Importa configurações globais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import config

class Minerador:
    """Minerador profissional com suporte a links diretos e buscas"""

    def __init__(self, progress_callback=None, log_callback=None, max_concurrency: int = 3):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def _log(self, message: str):
        print(f"[Minerador] {message}", flush=True)
        if self.log_callback:
            self.log_callback(message)

    async def _extract_product_data(self, page, url: str) -> Dict:
        """Extrai dados de um único link de produto usando o motor robusto"""
        try:
            # Título
            title_el = await page.query_selector("h1, .ui-pdp-title, .product-title, #productTitle")
            title = await title_el.inner_text() if title_el else "Produto sem título"
            
            # Preço (usa lógica compartilhada)
            from src.tools.calculadora_lucratividade.calculadora_lucratividade_v2 import CalculadoraLucratividade
            calc = CalculadoraLucratividade()
            price = await calc._extract_price_from_page(page)

            return {
                "success": True,
                "title": title.strip(),
                "price": price or 0.0,
                "url": url,
                "status": "Capturado" if price else "Preço não encontrado"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}

    async def mine_from_links_async(self, urls: List[str]) -> Dict:
        from playwright.async_api import async_playwright
        
        self._log(f"🚀 Iniciando extração de {len(urls)} links...")
        results = []
        errors = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            tasks = [self._process_single_link(context, url) for url in urls]
            
            completed = 0
            total = len(urls)
            for task in asyncio.as_completed(tasks):
                res = await task
                if res.get("success"):
                    results.append(res)
                else:
                    errors.append(res)
                
                completed += 1
                if self.progress_callback:
                    self.progress_callback(completed, total, int((completed / total) * 100))
            
            await browser.close()

        return {
            "success": True,
            "results": results,
            "errors": errors,
            "total": total,
            "collected": len(results)
        }

    async def _process_single_link(self, context, url: str) -> Dict:
        async with self.semaphore:
            page = None
            try:
                page = await context.new_page()
                # Usa a nova função estratégica de User Agent
                ua = config.get_random_ua("desktop")
                await page.set_extra_http_headers({"User-Agent": ua})
                
                self._log(f"Processando: {url[:40]}...")
                await page.goto(url, wait_until="load", timeout=60000)
                await page.wait_for_timeout(2000)
                
                return await self._extract_product_data(page, url)
            except Exception as e:
                return {"success": False, "error": str(e), "url": url}
            finally:
                if page: await page.close()

    def mine_from_links(self, urls: List[str]) -> Dict:
        try:
            return asyncio.run(self.mine_from_links_async(urls))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(self.mine_from_links_async(urls))

    def mine_from_file(self, file_path: str, max_links: int = None) -> Dict:
        try:
            df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
            url_col = next((c for c in df.columns if any(x in str(c).lower() for x in ['url', 'link', 'produto', 'site'])), None)
            
            if not url_col:
                return {"success": False, "error": "Coluna de links não encontrada."}

            urls = df[url_col].dropna().astype(str).tolist()
            if max_links: urls = urls[:max_links]
            
            return self.mine_from_links(urls)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def export_results(self, results: List[Dict], output_path: str):
        pd.DataFrame(results).to_excel(output_path, index=False)
        self._log(f"✅ Arquivo gerado: {output_path}")

    async def minerar_async(self, queries: List[str], marketplace: str = "mercadolivre") -> Dict:
        # Futura implementação de busca por nicho
        return {"success": True, "data": []}