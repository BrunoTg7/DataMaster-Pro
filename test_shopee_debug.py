"""
Teste específico para Shopee - investigar estrutura da página
"""
import asyncio
from playwright.async_api import async_playwright

async def test_shopee():
    url = 'https://shopee.com.br/Par-de-Alian%C3%A7a-de-Namoro-Compromisso-Prata-Diamantada-Brilhante-fina-4mm-i.624486930.23892878119'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR'
        )
        page = await context.new_page()
        
        print("Navegando para Shopee...")
        await page.goto(url, wait_until='domcontentloaded', timeout=45000)
        await page.wait_for_timeout(3000)
        
        # Scroll
        for i in range(10):
            await page.evaluate('window.scrollBy(0, 800)')
            await page.wait_for_timeout(600)
            print(f"Scroll {i+1}/10")
        
        print("\n=== ANALISANDO ESTRUTURA ===")
        
        # Verificar títulos e seções
        sections = await page.evaluate('''() => {
            const results = [];
            
            // Buscar seções/títulos que podem indicar reviews
            document.querySelectorAll('h1, h2, h3, [class*="title"], [class*="heading"]').forEach(el => {
                const text = el.innerText?.trim() || '';
                if (text.length > 0 && text.length < 200) {
                    results.push({tag: el.tagName, text, className: el.className});
                }
            });
            
            return results;
        }''')
        
        print("\nTitulos/Headings encontrados:")
        for s in sections[:20]:
            print(f"  <{s['tag']}> [{s['className']}] {s['text'][:80]}")
        
        # Verificar todos os elementos com 'review' no nome da classe
        review_classes = await page.evaluate('''() => {
            const results = [];
            const allClasses = new Set();
            
            document.querySelectorAll('*').forEach(el => {
                const className = el.className || '';
                if (typeof className === 'string') {
                    className.split(' ').forEach(c => {
                        if (c.length > 3 && (c.includes('review') || c.includes('rating') || c.includes('comment') || c.includes('star'))) {
                            allClasses.add(c);
                        }
                    });
                }
            });
            
            return Array.from(allClasses);
        }''')
        
        print(f"\nClasses relacionadas a reviews: {len(review_classes)}")
        for c in review_classes[:30]:
            print(f"  {c}")
        
        # Verificar se há Reviews no conteúdo
        all_text = await page.evaluate('''() => {
            const texts = [];
            document.querySelectorAll('div, section, article, span, p').forEach(el => {
                const text = el.innerText?.trim() || '';
                if (text.toLowerCase().includes('avaliacao') || text.toLowerCase().includes('review') || text.toLowerCase().includes('comentario') || text.toLowerCase().includes('estrela')) {
                    texts.push({text: text.slice(0, 200), className: el.className});
                }
            });
            return texts;
        }''')
        
        print(f"\nElementos com palavras de review: {len(all_text)}")
        for t in all_text[:10]:
            print(f"  [{t['className']}] {t['text'][:100]}...")
        
        # Verificar se há iframes ou conteúdo carregado dinamicamente
        iframes = await page.query_selector_all('iframe')
        print(f"\nIframes encontrados: {len(iframes)}")
        
        await browser.close()

asyncio.run(test_shopee())