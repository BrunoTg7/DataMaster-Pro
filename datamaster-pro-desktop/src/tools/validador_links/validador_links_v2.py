"""
Validador de Links Pro v3.0 - Validação Universal e Inteligente
Verifica integridade de links, disponibilidade de produtos e metadados.
Otimizado para performance com concorrência controlada.
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

class ValidadorLinks:
    """Validador profissional de links com detecção inteligente de conteúdo"""
    
    # Padrões para identificar sites fora do ar ou erros comuns (mais específicos)
    NOT_FOUND_PATTERNS = [
        r'\b404\b', r'não encontrado', r'\bnot found\b', r'página não existe',
        r'erro 404', r'página não encontrada', r'conteúdo removido'
    ]
    
    # Padrões para identificar bloqueios de robôs
    ACCESS_DENIED_PATTERNS = [
        r'access denied', r'acesso negado', r'challenge-running', 
        r'verify you are human', r'bloqueio de segurança', r'unusual activity'
    ]

    # Padrões de estoque (E-commerce)
    OUT_OF_STOCK_PATTERNS = [
        r'esgotado', r'indisponível', r'produto\s+esgotado',
        r'fora\s+de\s+estoque', r'não\s+temos\s+em\s+estoque', 
        r'produto\s+indisponível', r'previsão\s+de\s+entrada', 
        r'sold\s+out', r'out\s+of\s+stock'
    ]
    
    # Seletores de botões de compra (comuns em diversos frameworks)
    BUY_BUTTON_SELECTORS = [
        'button[class*="buy"]', 'button[class*="comprar"]',
        'a[class*="buy"]', 'a[class*="comprar"]',
        '[data-testid*="buy"]', '[data-testid*="comprar"]',
        '.buy-button', '#buy-button', '.add-to-cart',
        'button:contains("Comprar")', 'button:contains("Adicionar")',
        'a:contains("Comprar")'
    ]

    USER_AGENTS = config.USER_AGENTS

    def __init__(self, progress_callback=None, log_callback=None, max_concurrency: int = 5):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.browser = None
        self.context = None
        self.playwright = None

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    async def _init_browser(self):
        """Inicializa o navegador com configurações anti-bot"""
        from playwright.async_api import async_playwright
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            self.context = await self.browser.new_context(
                user_agent=config.get_random_ua("desktop"),
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={"Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"}
            )

    async def _close_browser(self):
        """Fecha instâncias do navegador"""
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        self.context = self.browser = self.playwright = None

    async def _validate_single_link(self, url: str) -> Dict[str, Any]:
        """Valida um link individualmente com análise profunda"""
        result = {
            "url": url,
            "status_code": 0,
            "status_type": "unknown", 
            "title": "N/A",
            "is_product": False,
            "available": False,
            "message": "",
            "response_time": 0
        }

        async with self.semaphore:
            page = None
            try:
                start_time = datetime.now()
                page = await self.context.new_page()
                page.set_default_timeout(20000)
                
                # Intercepta erros de navegação antes mesmo do carregamento
                response = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                result["response_time"] = (datetime.now() - start_time).total_seconds()

                if not response:
                    result.update({"status_type": "broken", "message": "Sem resposta do servidor"})
                    return result

                result["status_code"] = response.status
                result["title"] = (await page.title()).strip() or "Página sem título"

                # Extrai apenas o TEXTO visível para evitar falsos positivos com Scripts/HTML
                body_text = (await page.inner_text("body")).lower()
                title_lower = result["title"].lower()
                
                # 1. Verificar Status HTTP Direto
                if response.status >= 400:
                    if response.status in [403, 429]:
                        result.update({"status_type": "restricted", "message": f"Acesso negado (Status {response.status})"})
                    else:
                        result.update({"status_type": "broken", "message": f"Erro HTTP {response.status}"})
                    return result

                # 2. Verificar Bloqueios por Conteúdo (apenas se status for 200)
                if any(re.search(p, body_text) for p in self.ACCESS_DENIED_PATTERNS) or "access denied" in title_lower:
                    result.update({"status_type": "restricted", "message": "Proteção anti-bot detectada no conteúdo"})
                    return result

                # 3. Verificar "Not Found" mascarado (Soft 404)
                if any(re.search(p, body_text) for p in self.NOT_FOUND_PATTERNS) or "not found" in title_lower:
                    result.update({"status_type": "broken", "message": "Página não encontrada (Soft 404)"})
                    return result

                # 4. Detecção Inteligente de Produto
                has_buy_button = await self._check_buy_button(page)
                # Verifica se há indicadores de preço no texto
                has_price = any(x in body_text for x in ["r$", "price", "preço", "por:"])
                is_product = has_buy_button or has_price
                result["is_product"] = is_product

                # 5. Verificação de Disponibilidade
                is_out_of_stock = any(re.search(p, body_text) for p in self.OUT_OF_STOCK_PATTERNS)
                
                if is_product:
                    if is_out_of_stock:
                        result.update({"status_type": "out_of_stock", "available": False, "message": "Produto esgotado"})
                    elif not has_buy_button and has_price:
                        # Se tem preço mas não tem botão, pode estar indisponível ou ser apenas vitrine
                        result.update({"status_type": "out_of_stock", "available": False, "message": "Botão de compra não encontrado"})
                    else:
                        result.update({"status_type": "active", "available": True, "message": "Produto disponível"})
                else:
                    result.update({"status_type": "active", "available": True, "message": "Link ativo e acessível"})

                return result

            except Exception as e:
                err_msg = str(e).lower()
                if "timeout" in err_msg:
                    msg = "Timeout: Site lento ou inacessível"
                elif "net::err" in err_msg:
                    msg = "Erro de conexão: DNS ou Host inválido"
                else:
                    msg = f"Erro: {str(e)[:50]}"
                
                result.update({"status_type": "broken", "message": msg})
                return result
            finally:
                if page: await page.close()

    async def _check_buy_button(self, page) -> bool:
        """Busca exaustiva por botões de ação de compra"""
        for selector in self.BUY_BUTTON_SELECTORS:
            try:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    return True
            except Exception: continue
        return False

    async def _run_validation(self, urls: List[str]) -> List[Dict]:
        """Gerencia a execução paralela das validações"""
        await self._init_browser()
        tasks = []
        for url in urls:
            tasks.append(self._validate_single_link(url))
        
        results = []
        total = len(urls)
        
        # Processa conforme as tarefas terminam para atualizar progresso
        for i, task in enumerate(asyncio.as_completed(tasks)):
            res = await task
            results.append(res)
            
            if self.progress_callback:
                self.progress_callback(int(((i + 1) / total) * 100))
            
            status_emoji = "✅" if res["status_type"] == "active" else "❌" if res["status_type"] == "broken" else "⚠️"
            self._log(f"{status_emoji} {res['url'][:40]}... -> {res['status_type']}")

        await self._close_browser()
        return results

    def validate_links(self, urls: List[str]) -> Dict:
        """Ponto de entrada principal (Síncrono para compatibilidade)"""
        if not urls: return {"success": False, "error": "Lista de URLs vazia"}
        
        # Gerenciamento robusto do loop de eventos
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(self._run_validation(urls))
        except Exception as e:
            # Fallback para asyncio.run se estivermos em um ambiente simplificado
            try:
                results = asyncio.run(self._run_validation(urls))
            except Exception:
                return {"success": False, "error": f"Erro fatal de concorrência: {str(e)}"}
        
        # Sumarização profissional
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(urls),
                "active": sum(1 for r in results if r["status_type"] == "active"),
                "broken": sum(1 for r in results if r["status_type"] == "broken"),
                "out_of_stock": sum(1 for r in results if r["status_type"] == "out_of_stock"),
                "restricted": sum(1 for r in results if r["status_type"] == "restricted"),
            },
            "results": results
        }

# Exemplo de uso
if __name__ == "__main__":
    import sys
    # Força saída UTF-8 no terminal para evitar erros de emoji
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    val = ValidadorLinks(log_callback=print, progress_callback=lambda p: print(f"Progresso: {p}%"))
    teste_urls = [
        "https://www.google.com",
        "https://www.amazon.com.br",
        "https://site-que-nao-existe-123456.com",
    ]
    print(val.validate_links(teste_urls))