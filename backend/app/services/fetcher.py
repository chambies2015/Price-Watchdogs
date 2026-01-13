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
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            await page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            
            await page.wait_for_timeout(2000)
            
            logger.info(f"Scrolling page {url} to trigger lazy-loaded content")
            for i in range(5):
                scroll_pos = (i + 1) * 20
                await page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {scroll_pos} / 100)')
                await page.wait_for_timeout(800)
            
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(1500)
            
            try:
                price_info = await page.evaluate("""() => {
                    const text = document.body.innerText;
                    const pricePattern = /\$\d+|\€\d+|\£\d+|\¥\d+/g;
                    const matches = text.match(pricePattern);
                    return {
                        found: matches && matches.length > 0,
                        count: matches ? matches.length : 0,
                        sample: matches ? matches.slice(0, 3).join(', ') : ''
                    };
                }""")
                
                if price_info['found']:
                    logger.info(f"Found {price_info['count']} prices on {url}: {price_info['sample']}")
                else:
                    logger.warning(f"No pricing patterns found on page {url}")
            except Exception as e:
                logger.warning(f"Error checking for prices on {url}: {str(e)}")
            
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            
            await browser.close()
            
            return content
            
    except PlaywrightTimeoutError:
        logger.error(f"Timeout fetching {url}")
        raise FetchError(f"Request timeout after {timeout} seconds")
        
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        raise FetchError(f"Failed to fetch page: {str(e)}")

