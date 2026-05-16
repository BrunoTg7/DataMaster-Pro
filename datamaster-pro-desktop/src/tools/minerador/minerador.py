"""
Minerador - Captura preços de sites concorrentes
"""
import pandas as pd
import os
import re
import requests
import json
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from bs4 import BeautifulSoup
import logging

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright nao instalado. Execute: pip install playwright && python -m playwright install chromium")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Minerador:
    def __init__(self, progress_callback: Callable = None, log_callback: Callable = None):
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Chromium";v="125", "Google Chrome";v="125", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Ch-Ua-Platform-Version": '"14.0.0"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)
        self.price_patterns = [
            r"R\$\s*[\d.,]+",
            r"[\d.,]+\s*reais",
            r"por\s*R\$\s*[\d.,]+",
            r"[\d.,]+"
        ]
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self._processed_count = 0
        self._total_count = 0
    
    def _log(self, message: str):
        logger.info(message)
        if self.log_callback:
            try:
                # Remover caracteres especiais (emojis) para evitar problemas de encoding
                clean_message = message.encode('ascii', errors='replace').decode('ascii')
                self.log_callback(clean_message)
            except Exception as e:
                logger.error(f"Erro no log_callback: {e}")

    def _fetch_with_playwright(self, url: str) -> Optional[Dict]:
        """Busca página usando Playwright para renderizar JavaScript"""
        if not PLAYWRIGHT_AVAILABLE:
            return None
        
        try:
            self._log(f"  [Playwright] Iniciando...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    locale="pt-BR",
                    viewport={"width": 1920, "height": 1080}
                )
                
                page = context.new_page()
                page.set_default_timeout(45000)
                
                # Usar wait_until="load" em vez de "networkidle" para evitarTimeouts em sites lentos
                try:
                    page.goto(url, wait_until="load", timeout=45000)
                    # Esperar um pouco para JavaScript carregar
                    page.wait_for_timeout(3000)
                except Exception as e:
                    self._log(f"  [Playwright] Timeout no load, tentando domcontentloaded...")
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(5000)
                
                content = page.content()
                title = page.title()
                
                browser.close()
                
                self._log(f"  [Playwright] Pagina carregada")
                
                return {
                    "html": content,
                    "title": title
                }
                
        except Exception as e:
            self._log(f"  [Playwright] Erro: {str(e)[:50]}")
            return None

    def mine_from_links(self, links: List[str], max_workers: int = 5, min_success_threshold: float = 0.3, max_rounds: int = 3, initial_batch_size: int = 10, min_success_count: int = 3) -> Dict:
        """
        Captura preços de uma lista de links
        
        Args:
            links: Lista de URLs para minerar
            max_workers: Número máximo de threads simultâneas
            min_success_threshold: Taxa mínima de sucesso (0.3 = 30%) para continuar processando links restantes
            max_rounds: Número máximo de rodadas de processamento
            initial_batch_size: Quantos links processar na primeira leva (padrão: 10)
            min_success_count: Mínimo de preços válidos necessários na primeira leva (padrão: 3)
        
        Returns:
            Dict com status e dados coletados
        """
        self._log("🚀 Iniciando mineração...")
        self._log(f"📊 Total de links: {len(links)}")
        
        if not links:
            self._log("⚠️ Nenhum link fornecido")
            return {"success": False, "error": "Nenhum link fornecido"}

        results = []
        errors = []
        self._processed_count = 0
        self._total_count = len(links)
        
        all_links = list(links)
        processed_links = set()
        round_num = 0
        initial_batch_processed = False

        try:
            import requests
            from bs4 import BeautifulSoup
            self._log("✅ Bibliotecas requests e beautifulsoup4 OK")
        except ImportError as e:
            self._log(f"❌ Erro ao importar bibliotecas: {e}")
            return {"success": False, "error": "requests ou beautifulsoup4 não instalados"}

        while round_num < max_rounds:
            round_num += 1
            
            if not initial_batch_processed:
                batch_links = all_links[:initial_batch_size]
                remaining_links = [l for l in batch_links if l not in processed_links]
            else:
                remaining_links = [l for l in all_links if l not in processed_links]
            
            if not remaining_links:
                self._log("✅ Todos os links já foram processados")
                break
            
            self._log(f"🔄 Rodada {round_num}/{max_rounds} - {len(remaining_links)} links restantes")
            self._log(f"🔧 Iniciando {max_workers} workers...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_link = {executor.submit(self._mine_single, link): link for link in remaining_links}
                self._log(f"📋 {len(future_to_link)} tarefas submetidas")

                round_results = []
                round_errors = []
                
                for future in as_completed(future_to_link):
                    link = future_to_link[future]
                    try:
                        result = future.result()
                        self._processed_count += 1
                        processed_links.add(link)
                        
                        if result:
                            round_results.append(result)
                            results.append(result)
                            
                            if result.get("status") == "success" and result.get("price"):
                                self._log(f"✅ [{self._processed_count}/{self._total_count}] {result.get('price', 'N/A')}")
                            elif result.get("status") == "error":
                                self._log(f"⚠️ [{self._processed_count}/{self._total_count}] Erro: {result.get('error', 'Desconhecido')}")
                            else:
                                self._log(f"⚠️ [{self._processed_count}/{self._total_count}] Preço vazio")
                        else:
                            self._log(f"⚠️ [{self._processed_count}/{self._total_count}] Resultado vazio")
                        
                        if self.progress_callback:
                            progress = int((self._processed_count / self._total_count) * 100)
                            self.progress_callback(self._processed_count, self._total_count, progress)
                            
                    except Exception as e:
                        round_errors.append({"link": link, "error": str(e)})
                        errors.append({"link": link, "error": str(e)})
                        self._log(f"❌ [{self._processed_count}/{self._total_count}] {str(e)}")

            success_count = sum(1 for r in round_results if r.get("status") == "success" and r.get("price"))
            success_rate = success_count / len(round_results) if round_results else 0
            
            self._log(f"📊 Rodada {round_num}: {success_count}/{len(round_results)} coletados (taxa: {success_rate:.1%})")

            if not initial_batch_processed:
                total_success = sum(1 for r in results if r.get("status") == "success" and r.get("price"))
                self._log(f"📊 Primeira leva: {total_success}/{min(initial_batch_size, len(all_links))} preços encontrados (mínimo necessário: {min_success_count})")
                
                if total_success >= min_success_count:
                    self._log(f"✅ Quantidade mínima atingida ({total_success} >= {min_success_count})")
                    initial_batch_processed = True
                else:
                    remaining = len(all_links) - len(processed_links)
                    if remaining > 0:
                        self._log(f"⚠️ Quantidade insuficiente ({total_success} < {min_success_count}), continuando com {remaining} links restantes...")
                        initial_batch_processed = True
                    else:
                        self._log("✅ Todos os links processados")
                        break
            else:
                if success_rate >= min_success_threshold or len(processed_links) >= len(all_links):
                    self._log(f"✅ Taxa de sucesso atingiu o limite ({success_rate:.1%} >= {min_success_threshold:.1%})")
                    break

        logger.info(f"🏁 Mineração concluída: {len(results)}/{len(links)} coletados, {len(errors)} erros")
        return {
            "success": True,
            "total": len(links),
            "collected": len(results),
            "results": results,
            "errors": errors if errors else None
        }

    def _mine_single(self, url: str) -> Optional[Dict]:
        """Minerar um único site"""
        self._log(f"Processando: {url[:50]}...")
        
        try:
            from bs4 import BeautifulSoup

            time.sleep(1.5)
            
            # Adicionar referer para evitar bloqueios
            headers = self.default_headers.copy()
            headers["Referer"] = "https://www.google.com/"
            
            # Usar sessão para manter cookies
            response = self.session.get(url, headers=headers, timeout=20, allow_redirects=True)
            
            # Se bloqueado, tentar com headers diferentes
            if response.status_code in [403, 429]:
                self._log(f"  Bloqueado, tentando alternativas...")
                alt_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                }
                time.sleep(3)
                response = requests.get(url, headers=alt_headers, timeout=20)
            
            self._log(f"  Status: {response.status_code}")

            if response.status_code != 200:
                self._log(f"  Erro: Status {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, "html.parser")
            self._log(f"  HTML parseado")

            title = self._extract_title(soup)
            self._log(f"  Titulo: {title[:30] if title else 'N/A'}...")

            price = self._extract_price(soup, response.text)
            self._log(f"  Preco (requests): {price}")
            
            # Se preço vazio e Playwright disponível, tentar renderizar JS
            if (not price or price == "") and PLAYWRIGHT_AVAILABLE:
                self._log(f"  Preco vazio, tentando Playwright...")
                playwright_result = self._fetch_with_playwright(url)
                
                if playwright_result:
                    html = playwright_result.get("html", "")
                    title = playwright_result.get("title", title)
                    
                    soup_pw = BeautifulSoup(html, "html.parser")
                    price_pw = self._extract_price(soup_pw, html)
                    
                    self._log(f"  Preco (Playwright): {price_pw}")
                    
                    if price_pw:
                        price = price_pw

            self._log(f"  Preco final: {price}")

            return {
                "url": url,
                "title": title,
                "price": price if price else "",
                "status": "success"
            }

        except requests.exceptions.Timeout:
            self._log(f"  Timeout")
            return {
                "url": url,
                "error": "Timeout",
                "status": "error"
            }
        except requests.exceptions.RequestException as e:
            self._log(f"  Erro: {str(e)[:50]}")
            return {
                "url": url,
                "error": str(e),
                "status": "error"
            }
        except Exception as e:
            self._log(f"  Erro: {str(e)[:50]}")
            return {
                "url": url,
                "error": str(e),
                "status": "error"
            }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrai o título do produto"""
        selectors = [
            "h1.product-title",
            "h1[itemprop='name']",
            ".product-name h1",
            "h1.product-name",
            "h1.product__title",
            ".product-header h1",
            "[itemprop='name']",
            ".product-title h1",
            ".product-info h1",
            "h1.title",
            "h1"
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 3:
                    return title[:100]  # Limitar tamanho

        # Fallback: procurar em title tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)[:100]

        return ""

    def _extract_price_from_jsonld(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrai o preço usando dados estruturados JSON-LD (schema.org)"""
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if not script.string:
                    continue
                try:
                    data = json.loads(script.string)
                    # O JSON-LD pode ser um objeto único ou uma lista
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        # Procura por esquemas de "Product" ou "Offer"
                        if item.get('@type') == 'Product' and 'offers' in item:
                            offers = item['offers']
                            if isinstance(offers, list) and len(offers) > 0:
                                price = offers[0].get('price')
                            else:
                                price = offers.get('price')
                            
                            if price:
                                cleaned = self._clean_price(str(price))
                                if cleaned and 10 <= float(cleaned) <= 100000:
                                    return cleaned
                        
                        if item.get('@type') == 'Offer' and 'price' in item:
                            price = item.get('price')
                            if price:
                                cleaned = self._clean_price(str(price))
                                if cleaned and 10 <= float(cleaned) <= 100000:
                                    return cleaned
                        
                        # Procura recursivamente em propriedades aninhadas
                        if '@graph' in item:
                            for graph_item in item['@graph']:
                                if graph_item.get('@type') == 'Product' and 'offers' in graph_item:
                                    offers = graph_item['offers']
                                    if isinstance(offers, list) and len(offers) > 0:
                                        price = offers[0].get('price')
                                    else:
                                        price = offers.get('price')
                                    if price:
                                        cleaned = self._clean_price(str(price))
                                        if cleaned and 10 <= float(cleaned) <= 100000:
                                            return cleaned
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue
        except Exception as e:
            pass
        
        return None

    def _extract_price_from_metatags(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrai o preço a partir de metatags (OpenGraph, Twitter, product)"""
        try:
            # Metatags comuns para preço
            meta_properties = [
                "product:price:amount",
                "og:price:amount",
                "twitter:data1",
                "price",
                "product:price",
                "offers"
            ]
            
            meta_names = [
                "price",
                "product:price",
                "product_price",
                "productPrice",
                "amount",
                "og:price:amount",
            ]
            
            # Tentar property
            for prop in meta_properties:
                meta = soup.find("meta", property=prop)
                if meta and meta.get("content"):
                    price = self._clean_price(meta["content"])
                    if price and 10 <= float(price) <= 100000:
                        return price
            
            # Tentar name
            for name in meta_names:
                meta = soup.find("meta", attrs={"name": name})
                if meta and meta.get("content"):
                    price = self._clean_price(meta["content"])
                    if price and 10 <= float(price) <= 100000:
                        return price
            
        except Exception as e:
            pass
        
        return None

    def _extract_price(self, soup: BeautifulSoup, html: str) -> Optional[str]:
        """Extrai o preço do produto usando múltiplos métodos"""
        
        # Método 1: JSON-LD (dados estruturados) - MAIS PRECISO
        price = self._extract_price_from_jsonld(soup)
        if price:
            return price
        
        # Método 2: Metatags (OpenGraph, Twitter, product)
        price = self._extract_price_from_metatags(soup)
        if price:
            return price
        
        # Método 3: Atributos estruturados itemprop (schema.org)
        price_element = soup.find(attrs={"itemprop": "price"})
        if price_element:
            price = price_element.get("content") or price_element.get("text") or price_element.get("value") or price_element.get_text(strip=True)
            if price:
                cleaned = self._clean_price(price)
                if cleaned and 10 <= float(cleaned) <= 100000:
                    return cleaned
        
        # Método 4: Atributos data- (data-price, data-value, etc)
        for attr in ["data-price", "data-product-price", "data-value", "data-amount", "data-precio", "data-preco"]:
            price_element = soup.find(attrs={attr: True})
            if price_element:
                cleaned = self._clean_price(price_element.get(attr))
                if cleaned and 10 <= float(cleaned) <= 100000:
                    return cleaned
        
        # Método 5: Seletores CSS expandidos (muito mais abrangentes)
        selectors = [
            # Genéricos
            "[data-testid='price']",
            "[data-test-id='price']",
            "[class*='price'][class*='amount']",
            "[class*='preco'][class*='valor']",
            
            # Samsung - seletores específicos
            ".pd-price-main",
            ".product-price-v2",
            ".price-area",
            "[class*='samsung-price']",
            "[data-product-price]",
            ".priceSales",
            ".product-detail__price",
            
            # Dell - seletores específicos
            "span.ps-price-value",
            ".ps-dell-price",
            ".dell-price",
            ".price-dell",
            "[class*='dell-price']",
            ".dell-price-container",
            ".dells-product-price",
            
            # Apple - seletores específicos
            "span.rc-prices-fullprice",
            "span[data-autom='full-price']",
            ".apple-price",
            "[class*='apple-price']",
            ".pricing-price",
            ".we-Price",
            ".as-price",
            ".price-message",
            ".hero-price",
            "[class*='rc-prices']",
            
            # Xbox/Microsoft - seletores específicos
            "[data-automation='listing-price']",
            "span[itemprop='price']",
            ".xbox-price",
            ".microsoft-price",
            "[class*='xbox-price']",
            ".price-microsoft",
            ".priceXbox",
            ".xboxs-price",
            
            # PlayStation - seletores específicos
            ".ps-price",
            ".ps5-price",
            "[class*='playstation-price']",
            ".price-ps",
            ".price--medium",
            ".ProductPrice",
            
            # Nintendo - seletores específicos
            ".nintendo-price",
            "[class*='switch-price']",
            ".price-nintendo",
            ".nintendo-eshop-price",
            
            # Magazine Luiza
            "[data-testid='price-value']",
            ".price-template__price",
            ".price__SalesPrice",
            ".price-value",
            ".PriceCard-Price",
            "[class*='magazine-price']",
            ".magalu-price",
            ".product-price__container",
            ".price-tag",
            "[class*='magalu']",
            ".sc-ebJcbR",
            ".sc-hMQzhW",
            
            # Mercado Livre
            ".ui-pdp-price__symbol",
            ".ui-pdp-price__fraction",
            ".ui-pdp-price__subtotal",
            ".price-tag",
            ".price-tag__wrapper",
            ".price-tag__flex",
            ".price-tag__content",
            ".andes-money-amount",
            "[class*='mercadolivre']",
            "[class*='mercado-livre']",
            ".ui-pdp-container__row--main-actions",
            ".ui-pdp-price__part",
            ".price-text",
            
            # Shopee
            "_1OIVk3",
            ".product-price",
            ".product-detail__price",
            ".shopee-price",
            ".product-item-price",
            "[class*='shopee-price']",
            ".flex.items-center.h-full",
            ".quantity",
            ".price-before-discount",
            ".stardust-icon",
            
            # AliExpress
            ".price-value",
            ".product-price-value",
            ".price",
            "[class*='aliexpress-price']",
            ".ma-spec-price",
            ".price-line",
            ".current-price",
            
            # Americanas / Submarino / Shoptime
            ".price-card",
            ".price-card__price",
            ".price-card__content",
            ".price-tag",
            ".best-price",
            ".product__price",
            ".regular-price",
            "[class*='americanas']",
            "[class*='submarino']",
            "[class*='shoptime']",
            
            # Casas Bahia
            ".price-card__info",
            ".price-tag__wrapper",
            ".product-price-container",
            "[class*='casas-bahia']",
            ".cb-price",
            
            # Amazon Brasil
            ".a-price-whole",
            ".a-price__whole",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            ".a-offscreen",
            "#corePrice_feature_div",
            "#corePriceDisplay",
            
            # Extra / Pão de Açúcar / Carrefur
            "[class*='extra-price']",
            "[class*='paodeacucar-price']",
            ".store-price",
            
            # Riachuelo
            ".riachuelo-price",
            ".product-price-riachuelo",
            
            # Centauro
            ".centauro-price",
            ".product-price-centauro",
            
            # Other Brasil e-commerces
            ".lojas american price",
            ".mobly-price",
            ".quinto-andar-price",
            "[class*='ponto-frio']",
            ".magazine-price",
            
            # International
            ".ebay-price",
            ".walmart-price",
            ".target-price",
            ".bestbuy-price",
            ".newegg-price",
            ".aliexpress-price",
            
            # Populares
            ".price-value",
            ".price__value",
            ".price-amount",
            ".price-current",
            ".price-new",
            ".current-price",
            ".product-price",
            ".product__price",
            ".product-price-amount",
            ".valor-produto",
            ".valor-preco",
            ".preco-final",
            ".preco-venda",
            ".preco-atual",
            
            # Amazon style
            ".a-price__value",
            ".a-price-whole",
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            
            # Shopify
            ".product-form__price",
            ".price__value",
            "[data-product-price]",
            
            # WooCommerce
            ".woocommerce-Price-amount",
            ".amount",
            ".price",
            
            # Vtex e variações
            ".best-price",
            ".sale-price",
            ".offer-price",
            ".selling-price",
            ".deal-price",
            ".prc-val",
            ".priceValue",
            ".priceSale",
            ".priceNow",
            
            # Class wildcards
            "[class*='Price']",
            "[class*='price']",
            "[class*='Valor']",
            "[class*='valor']",
            "[class*='Preco']",
            "[class*='preco']",
            "[class*='PRICE']",
            "[class*='Valor']",
            
            # IDs
            "#price",
            "#product-price",
            "#selling-price",
            
            # Tags com atributos específicos
            "span[data-price]",
            "div[data-price]",
            "b[data-price]",
            "strong[data-price]",
            
            # Últimos recursos
            ".ui-price",
            ".product__final-price",
            ".product-price-container",
            ".price-container",
            "[itemprop='price']",
            
            # LG e outras marcas
            ".lg-price",
            "[class*='product-price']",
            ".shop-price",
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get("content") or element.get("data-price") or element.get("data-value") or element.get_text(strip=True)
                if price_text and len(price_text) > 0:
                    cleaned = self._clean_price(price_text)
                    if cleaned:
                        value = float(cleaned)
                        # Ignorar preços muito baixos (< R$ 10) ou muito altos (> R$ 100.000)
                        # Permitir produtos de diferentes categorias (acessórios até eletrônicos)
                        if 10 <= value <= 100000:
                            return cleaned
        
        # Método 6: Buscar padrões de preço em reais/outras moedas no HTML completo
        # REFINADO: Evita capturar valores muito altos ou muito baixos
        patterns = [
            # BR: R$ com decimal obrigatória (1.234,56) - mais restritivo
            r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
            # BR: R$ com parte decimal opcional (R$ 1234 ou R$ 1234,56) - limitar a 7 dígitos
            r"R\$\s*(\d{1,7}(?:\.\d{3})*(?:,\d{1,2})?)",
            # BR: "por R$" + valor
            r"por\s+R\$\s*(\d{1,7}(?:\.\d{3})*(?:,\d{1,2})?)",
            
            # USD: $ com decimal limitada
            r"(?:USD|US\$|\$)\s*(\d{1,6}(?:,\d{3})*(?:\.\d{2})?)",
            
            # JSON-LD Offers: evitar capturar preços de outras entidades
            r'(?:["\']offers["\']|["\']price["\'])\s*:\s*(?:["\'])?(\d+(?:\.\d+)?)(?:["\'])?',
            
            # data attributes: data-price="1234.56" - com limite
            r'data-(?:price|amount|value)\s*=\s*["\'](\d{1,6}(?:\.\d+)?)["\']',
            
            # Metatags: <meta property="product:price:amount" content="1234">
            r'<meta\s+(?:property|name)=["\'](?:product:price:amount|og:price:amount)["\'][^>]+content=["\'](\d{1,6})["\']',
            
            # Itemprop: <span itemprop="price" content="1234">
            r'<[^>]+itemprop=["\']price["\'][^>]+content=["\'](\d{1,6})["\']',
            
            # Preço em texto próximo a palavras-chave
            r'(?:preco|preço|valor|price|amount)["\s:]+["\']?(\d{1,6}(?:[\.,]\d{2})?)["\']?',
            
            # Script data com price
            r'"price"\s*:\s*(\d+(?:\.\d+)?)',
            r'"amount"\s*:\s*(\d+)',
            
            # SVG price symbols
            r'<svg[^>]*>.*?R\$\s*(\d{1,7}(?:[\.,]\d{2})?)',
            
            # Magazine Luiza patterns
            r'(?:magalu|magazine)\s*["\']?\s*:\s*["\']?(\d{3,7}(?:[.,]\d{2})?)',
            r'data-price=["\'](\d{3,7}(?:[.,]\d{2})?)',
            
            # Mercado Livre patterns
            r'(?:mercado)[-_\s]livre.*?price.*?(\d{3,7}(?:[.,]\d{2})?)',
            r'andes-money-amount.*?(\d{3,7})',
            
            # Shopee patterns
            r'shopee.*?price.*?(\d{3,7}(?:[.,]\d{2})?)',
            r'_1OIVk3.*?(\d{3,7}(?:[.,]\d{2})?)',
            
            # AliExpress patterns
            r'aliexpress.*?price.*?(\d{2,7}(?:[.,]\d{2})?)',
            
            # Americanas patterns
            r'americanas.*?price.*?(\d{3,7}(?:[.,]\d{2})?)',
            
            # Amazon patterns
            r'(?:priceblock|price).*?(\d{2,6}(?:[.,]\d{2})?)',
            r'A0DPois6M3XFLWd.*?(\d{3,7})',
            
            # Generic price extraction
            r'valor["\s:]+(\d{1,7}(?:[.,]\d{2})?)',
            r'price["\s:]+(\d{1,7}(?:[.,]\d{2})?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.MULTILINE)
            if matches:
                prices = []
                for m in matches:
                    cleaned = self._clean_price(m)
                    if cleaned:
                        value = float(cleaned)
                        # Ignorar preços muito baixos (< R$ 1000) ou muito altos (> R$ 50.000)
                        if 10 <= value <= 100000:
                            prices.append(value)
                if prices:
                    # Retornar o maior preço válido
                    return str(int(max(prices))) if max(prices) == int(max(prices)) else f"{max(prices):.2f}"
        
        return ""

    def _clean_price(self, price_str: str) -> str:
        """Limpa o preço extraído - Remove símbolos de moeda, espaços e normaliza formatação"""
        if not price_str:
            return None
        
        price_str = str(price_str).strip()
        if not price_str:
            return None
        
        # Remove símbolos de moeda e espaços extras
        price_str = re.sub(r"[R$US$€£¥]+", "", price_str)  # Remove símbolos de moeda
        price_str = re.sub(r"\s+", " ", price_str).strip()  # Remove espaços extras
        
        # Remove tudo exceto números, vírgula, ponto e espaço
        price_str = re.sub(r"[^\d,.\s]", "", price_str)
        price_str = re.sub(r"\s+", "", price_str)  # Remove espaços após limpeza
        
        if not price_str or price_str == "":
            return None
        
        # Detectar e normalizar formato
        # Formato brasileiro: 1.234,56 -> 1234.56
        # Formato americano: 1234.56 ou 1,234.56 -> 1234.56
        
        if "," in price_str and "." in price_str:
            # Ambos separadores presentes
            if price_str.rfind(",") > price_str.rfind("."):
                # BR: 1.234,56 -> 1234.56
                price_str = price_str.replace(".", "").replace(",", ".")
            else:
                # US: 1,234.56 -> 1234.56
                price_str = price_str.replace(",", "")
        elif "," in price_str:
            # Apenas vírgula
            parts = price_str.split(",")
            if len(parts) == 2 and len(parts[1]) == 2:
                # BR decimal: 13,99 -> 13.99
                price_str = price_str.replace(",", ".")
            elif len(parts) == 2 and len(parts[1]) > 2:
                # BR milhar: 1.234, -> remover vírgula (tratado como decimal)
                price_str = price_str.replace(",", ".")
            else:
                # BR milhar com múltiplas partes ou número inteiro: 1.234.567,89
                price_str = price_str.replace(",", ".")
        elif "." in price_str:
            # Apenas ponto - pode ser BR milhar ou US decimal
            parts = price_str.split(".")
            if len(parts[-1]) == 2:
                # Provavelmente US decimal (x.yy) - manter
                pass
            elif len(parts[-1]) == 3:
                # Provavelmente BR milhar (x.yyy) - já está ok
                pass
            else:
                # Ambíguo - manter como está
                pass
        
        try:
            value = float(price_str)
            if value > 0:
                # Retorna como string de número com 2 casas decimais
                if value == int(value):
                    return str(int(value))
                else:
                    return f"{value:.2f}"
        except (ValueError, TypeError):
            pass
        
        return None

    def mine_from_file(self, input_file: str, url_column: str = "url", max_links: int = None) -> Dict:
        """Minerar preços a partir de arquivo com URLs"""
        self._log(f"📁 Lendo arquivo: {input_file}")
        
        if not os.path.exists(input_file):
            self._log("❌ Arquivo não encontrado")
            return {"success": False, "error": "Arquivo não encontrado"}

        try:
            ext = os.path.splitext(input_file)[1].lower()
            self._log(f"📄 Extensão: {ext}")
            
            if ext in [".xlsx", ".xls"]:
                try:
                    df = pd.read_excel(input_file, engine='openpyxl')
                except:
                    df = pd.read_excel(input_file)
            else:
                df = pd.read_csv(input_file, encoding="utf-8")
            
            self._log(f"📊 Linhas: {len(df)}")
            self._log(f"📋 Colunas: {list(df.columns)}")

            # Buscar coluna que contenha URLs (começam com http)
            url_col = None
            for col in df.columns:
                sample = df[col].dropna().head(5).tolist()
                if any(str(s).startswith("http") for s in sample):
                    url_col = col
                    self._log(f"🔗 Coluna de URL detectada: {col}")
                    break
            
            if not url_col:
                # Tentar usar a coluna original
                if url_column not in df.columns:
                    self._log(f"❌ Nenhuma coluna com URLs (http) encontrada")
                    return {"success": False, "error": "Nenhuma coluna com URLs encontrada"}
                url_col = url_column

            links = df[url_col].dropna().tolist()
            # Filtrar apenas URLs válidas
            links = [l for l in links if isinstance(l, str) and l.startswith("http")]
            
            if max_links and len(links) > max_links:
                self._log(f"⚠️ Limite de {max_links} links por execução. processando {max_links} de {len(links)}")
                links = links[:max_links]
            else:
                self._log(f"🔗 URLs encontradas: {len(links)}")
            return self.mine_from_links(links)

        except Exception as e:
            self._log(f"❌ Erro: {str(e)}")
            return {"success": False, "error": str(e)}

    def export_results(self, results: List[Dict], output_path: str) -> Dict:
        """Exporta resultados para Excel/CSV"""
        try:
            df = pd.DataFrame(results)
            ext = os.path.splitext(output_path)[1].lower()

            if ext == ".csv":
                df.to_csv(output_path, index=False)
            else:
                df.to_excel(output_path, index=False, engine="openpyxl")

            return {"success": True, "output_path": output_path, "total": len(results)}

        except Exception as e:
            return {"success": False, "error": str(e)}