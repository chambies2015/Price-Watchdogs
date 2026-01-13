import httpx
from typing import Optional
import logging
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import re

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 PriceWatchdogs/1.0"

class FetchError(Exception):
    pass


async def _fetch_page_playwright(url: str) -> str:
    logger.info("Launching Playwright browser...")
    async with async_playwright() as p:
        logger.info("Launching Chromium...")
        browser = await p.chromium.launch(
            headless=True,
            timeout=45000,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
            ]
        )
        logger.info("Browser launched successfully")
        
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        logger.info("Browser context created")
        
        try:
            logger.info("Adding anti-bot detection scripts...")
            await context.add_init_script(r"""
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
            logger.info("Anti-bot scripts added")
        except Exception as e:
            logger.warning(f"Failed to add init script: {str(e)}")
        
        logger.info("Creating new page...")
        try:
            page = await asyncio.wait_for(context.new_page(), timeout=15)
            logger.info("Page created successfully")
        except asyncio.TimeoutError:
            logger.error("Page creation timed out after 15s")
            raise
        
        logger.info(f"Navigating to {url}...")
        try:
            await asyncio.wait_for(
                page.goto(url, wait_until='domcontentloaded', timeout=30000),
                timeout=35
            )
            logger.info("Page loaded (domcontentloaded)")
        except asyncio.TimeoutError:
            logger.error("Navigation timed out after 35s")
            raise
        
        logger.info("Waiting for JavaScript execution...")
        await page.wait_for_timeout(3000)
        
        logger.info("Waiting for pricing content to appear...")
        try:
            await page.wait_for_selector(
                '[class*="pric"], [class*="plan"], [class*="tier"], [id*="pric"], [id*="plan"], [id*="tier"]',
                timeout=5000,
                state='attached'
            )
            logger.info("Pricing-related elements found")
            await page.wait_for_timeout(1000)
        except:
            logger.warning("No pricing selectors found, waiting longer...")
            await page.wait_for_timeout(3000)
        
        logger.info("Scrolling page to trigger lazy-loaded content")
        try:
            await page.evaluate('window.scrollTo({top: document.body.scrollHeight})')
            await page.wait_for_timeout(1000)
            await page.evaluate('window.scrollTo({top: 0})')
            await page.wait_for_timeout(1000)
            logger.info("Scrolling complete")
        except Exception as e:
            logger.warning(f"Scrolling failed: {str(e)}")
        
        try:
            price_info = await page.evaluate(r"""() => {
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
                logger.info(f"✓ Found {price_info['count']} prices: {price_info['sample']}")
            else:
                logger.warning(f"✗ No pricing patterns found")
            
            logger.info(f"Page text: {price_info['textLength']} chars")
            logger.info(f"Sample: {price_info['textSample'][:200]}")
            
        except Exception as e:
            logger.warning(f"Error checking prices: {str(e)}")
        
        logger.info("Capturing content...")
        await page.wait_for_timeout(1000)
        content = await page.content()
        logger.info(f"✓ Captured {len(content)} bytes")
        
        return content


async def fetch_page(url: str, timeout: int = 90) -> str:
    logger.info(f"Attempting to fetch page: {url}")
    
    try:
        content = await asyncio.wait_for(
            _fetch_page_playwright(url),
            timeout=timeout
        )
        return content
    except asyncio.TimeoutError:
        logger.error(f"Playwright operation timed out after {timeout}s for {url}")
        logger.info("Attempting fallback to simple HTTP fetch...")
        return await fallback_fetch(url, 30)
    except PlaywrightTimeoutError as e:
        logger.error(f"Playwright timeout for {url}: {str(e)}")
        logger.info("Attempting fallback to simple HTTP fetch...")
        return await fallback_fetch(url, 30)
    except Exception as e:
        logger.error(f"Playwright error for {url}: {type(e).__name__}: {str(e)}")
        logger.info("Attempting fallback to simple HTTP fetch...")
        return await fallback_fetch(url, 30)


async def fallback_fetch(url: str, timeout: int = 30) -> str:
    logger.info(f"Using fallback HTTP fetcher for {url}")
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={'User-Agent': USER_AGENT})
            response.raise_for_status()
            logger.info(f"✓ Fallback fetch successful: {len(response.text)} bytes")
            return response.text
    except Exception as e:
        logger.error(f"Fallback fetch also failed for {url}: {str(e)}")
        raise FetchError(f"Both Playwright and fallback fetch failed: {str(e)}")

