import httpx
from typing import Optional
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 PriceWatchdogs/1.0"

class FetchError(Exception):
    pass


async def fetch_page(url: str, timeout: int = 30) -> str:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                ]
            )
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            )
            
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            page = await context.new_page()
            
            await page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            
            await page.wait_for_timeout(3000)
            
            logger.info(f"Scrolling page {url} to trigger lazy-loaded content")
            
            total_height = await page.evaluate('document.body.scrollHeight')
            logger.info(f"Page height: {total_height}px")
            
            for i in range(8):
                scroll_pos = (i + 1) * 12.5
                await page.evaluate(f'window.scrollTo({{top: document.body.scrollHeight * {scroll_pos} / 100, behavior: "smooth"}})')
                await page.wait_for_timeout(1000)
                
                if i == 3 or i == 6:
                    await page.mouse.move(500, 500)
                    await page.wait_for_timeout(500)
            
            await page.evaluate('window.scrollTo({top: 0, behavior: "smooth"})')
            await page.wait_for_timeout(2000)
            
            try:
                price_info = await page.evaluate("""() => {
                    const text = document.body.innerText;
                    const pricePattern = /\$\d+(?:\.\d{2})?|\€\d+(?:\.\d{2})?|\£\d+(?:\.\d{2})?|\¥\d+/g;
                    const matches = text.match(pricePattern);
                    
                    const textLength = text.length;
                    const textSample = text.substring(0, 500).replace(/\s+/g, ' ').trim();
                    
                    return {
                        found: matches && matches.length > 0,
                        count: matches ? matches.length : 0,
                        sample: matches ? matches.slice(0, 5).join(', ') : '',
                        textLength: textLength,
                        textSample: textSample
                    };
                }""")
                
                if price_info['found']:
                    logger.info(f"✓ Found {price_info['count']} prices on {url}: {price_info['sample']}")
                else:
                    logger.warning(f"✗ No pricing patterns found on {url}")
                
                logger.info(f"Page text length: {price_info['textLength']} chars")
                logger.info(f"Text sample: {price_info['textSample'][:200]}")
                
            except Exception as e:
                logger.warning(f"Error checking for prices on {url}: {str(e)}")
            
            await page.wait_for_timeout(3000)
            
            content = await page.content()
            logger.info(f"Captured HTML content length: {len(content)} bytes")
            
            await browser.close()
            
            return content
            
    except PlaywrightTimeoutError:
        logger.error(f"Timeout fetching {url}")
        raise FetchError(f"Request timeout after {timeout} seconds")
        
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        raise FetchError(f"Failed to fetch page: {str(e)}")

