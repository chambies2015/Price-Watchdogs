import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 PriceWatchdogs/1.0"

class FetchError(Exception):
    pass


async def fetch_page(url: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            verify=True
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        raise FetchError(f"HTTP {e.response.status_code}: {e.response.reason_phrase}")
        
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching {url}")
        raise FetchError(f"Request timeout after {timeout} seconds")
        
    except httpx.RequestError as e:
        logger.error(f"Request error fetching {url}: {str(e)}")
        raise FetchError(f"Request failed: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {str(e)}")
        raise FetchError(f"Unexpected error: {str(e)}")

