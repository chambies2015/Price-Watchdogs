import httpx
from typing import Optional
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

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
            
            content = await page.content()
            
            await browser.close()
            
            return content
            
    except PlaywrightTimeoutError:
        logger.error(f"Timeout fetching {url}")
        raise FetchError(f"Request timeout after {timeout} seconds")
        
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        raise FetchError(f"Failed to fetch page: {str(e)}")

