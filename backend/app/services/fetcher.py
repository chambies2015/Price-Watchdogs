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
    browser = None
    try:
        async with async_playwright() as p:
            logger.info("Launching Chromium...")
            browser = await asyncio.wait_for(
                p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-software-rasterizer',
                        '--disable-extensions',
                        '--disable-background-networking',
                        '--single-process',
                    ]
                ),
                timeout=30
            )
            logger.info("Browser launched successfully")
            
            context = await asyncio.wait_for(
                browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                    }
                ),
                timeout=10
            )
            logger.info("Browser context created")
            
            try:
                logger.info("Adding anti-bot detection scripts...")
                await asyncio.wait_for(
                    context.add_init_script(r"""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        window.chrome = {
                            runtime: {}
                        };
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                    """),
                    timeout=5
                )
                logger.info("Anti-bot scripts added")
            except asyncio.TimeoutError:
                logger.warning("Init script timeout, continuing...")
            except Exception as e:
                logger.warning(f"Failed to add init script, continuing: {str(e)}")
            
            logger.info("Creating new page...")
            page = await asyncio.wait_for(
                context.new_page(),
                timeout=10
            )
            logger.info("Page created successfully")
            
            try:
                logger.info(f"Navigating to {url}...")
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=15000)
                    logger.info("Page loaded (networkidle)")
                except PlaywrightTimeoutError:
                    logger.warning(f"Network idle timeout, trying load state...")
                    try:
                        await page.goto(url, wait_until='load', timeout=10000)
                        logger.info("Page loaded (load state)")
                    except:
                        logger.warning(f"Load timeout, trying domcontentloaded...")
                        await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                        logger.info("Page loaded (domcontentloaded)")
                except Exception as e:
                    logger.error(f"Failed to navigate to {url}: {str(e)}")
                    raise
                
                await page.wait_for_timeout(3000)
                logger.info(f"Initial wait complete")
                
                logger.info("Waiting for pricing content to appear...")
                try:
                    await page.wait_for_selector(
                        '[class*="pric"], [class*="plan"], [class*="tier"], [id*="pric"], [id*="plan"], [id*="tier"], [data-testid*="pric"], [data-testid*="plan"]',
                        timeout=5000,
                        state='attached'
                    )
                    logger.info("Pricing-related elements found")
                except:
                    logger.warning("No pricing selectors found, continuing anyway...")
                
                await page.wait_for_timeout(2000)
                
                logger.info(f"Scrolling page to trigger lazy-loaded content")
                
                try:
                    initial_height = await page.evaluate('document.body.scrollHeight')
                    logger.info(f"Initial page height: {initial_height}px")
                    
                    scroll_positions = [0, 0.25, 0.5, 0.75, 1.0]
                    for i, pos in enumerate(scroll_positions):
                        await page.evaluate(f'window.scrollTo({{top: document.body.scrollHeight * {pos}, behavior: "smooth"}})')
                        await page.wait_for_timeout(1000)
                        
                        new_height = await page.evaluate('document.body.scrollHeight')
                        if new_height > initial_height:
                            logger.info(f"Page expanded to {new_height}px at scroll position {i+1}")
                            initial_height = new_height
                    
                    await page.evaluate('window.scrollTo({top: 0, behavior: "smooth"})')
                    await page.wait_for_timeout(2000)
                    
                    final_height = await page.evaluate('document.body.scrollHeight')
                    logger.info(f"Final page height: {final_height}px")
                    logger.info("Scrolling complete")
                except Exception as e:
                    logger.warning(f"Scrolling failed, but continuing: {str(e)}")
                
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
                        logger.info(f"✓ Found {price_info['count']} prices on {url}: {price_info['sample']}")
                    else:
                        logger.warning(f"✗ No pricing patterns found on {url}")
                    
                    logger.info(f"Page text length: {price_info['textLength']} chars")
                    logger.info(f"Text sample: {price_info['textSample'][:200]}")
                    
                except Exception as e:
                    logger.warning(f"Error checking for prices on {url}: {str(e)}")
                
                logger.info("Waiting for final content stabilization...")
                await page.wait_for_timeout(3000)
                
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000)
                    logger.info("Network idle confirmed")
                except:
                    logger.warning("Network idle timeout, proceeding anyway...")
                
                content = await page.content()
                logger.info(f"✓ Captured HTML content: {len(content)} bytes")
                
                return content
            finally:
                try:
                    if browser:
                        await browser.close()
                        logger.info("Browser closed")
                except Exception as e:
                    logger.warning(f"Error closing browser: {str(e)}")
    except asyncio.TimeoutError as e:
        logger.error(f"Browser setup timed out: {str(e)}")
        if browser:
            try:
                await browser.close()
            except:
                pass
        raise
    except Exception as e:
        logger.error(f"Playwright error: {type(e).__name__}: {str(e)}")
        if browser:
            try:
                await browser.close()
            except:
                pass
        raise


async def fetch_page(url: str, timeout: int = 60) -> str:
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

