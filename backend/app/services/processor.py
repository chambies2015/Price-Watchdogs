import hashlib
import re
from typing import Tuple
from bs4 import BeautifulSoup
import bleach
import logging

logger = logging.getLogger(__name__)

ALLOWED_TAGS = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'tbody', 'thead']
ALLOWED_ATTRIBUTES = {'*': ['class', 'id']}

PRICING_SELECTORS = [
    '[class*="pric"]',
    '[class*="plan"]',
    '[class*="tier"]',
    '[class*="package"]',
    '[class*="subscription"]',
    '[class*="cost"]',
    '[class*="amount"]',
    '[id*="pric"]',
    '[id*="plan"]',
    '[id*="tier"]',
    '[id*="package"]',
    '[data-testid*="pric"]',
    '[data-testid*="plan"]',
    '[data-testid*="tier"]',
    'table',
]

NOISE_PATTERNS = [
    r'\d{1,2}:\d{2}:\d{2}',
    r'\d{1,2}/\d{1,2}/\d{2,4}',
    r'\d{4}-\d{2}-\d{2}',
    r'Updated:\s*\w+\s*\d{1,2},?\s*\d{4}',
    r'Last updated:.*',
    r'Cookie',
    r'Accept all cookies',
    r'We use cookies',
]


def sanitize_html(html: str) -> str:
    soup = BeautifulSoup(html, 'lxml')
    
    for tag in soup(['script', 'style', 'iframe', 'noscript', 'meta', 'link']):
        tag.decompose()
    
    for tag in soup.find_all(class_=re.compile(r'(ad|banner|cookie|tracking|analytics)', re.I)):
        tag.decompose()
    
    for tag in soup.find_all(id=re.compile(r'(ad|banner|cookie|tracking|analytics)', re.I)):
        tag.decompose()
    
    clean_html = bleach.clean(
        str(soup),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return clean_html


def extract_pricing_content(html: str, custom_selector: str = None) -> str:
    soup = BeautifulSoup(html, 'lxml')
    
    if custom_selector:
        selectors = [custom_selector]
    else:
        selectors = PRICING_SELECTORS
    
    extracted_elements = []
    
    for selector in selectors:
        try:
            elements = soup.select(selector)
            extracted_elements.extend(elements)
        except Exception as e:
            logger.warning(f"Error with selector {selector}: {e}")
            continue
    
    if extracted_elements:
        pricing_html = ' '.join(str(elem) for elem in extracted_elements)
        if pricing_html:
            return pricing_html
    
    price_pattern = re.compile(r'\$\d+(?:\.\d{2})?|\€\d+(?:\.\d{2})?|\£\d+(?:\.\d{2})?|\¥\d+', re.IGNORECASE)
    
    all_elements = soup.find_all(['div', 'section', 'article', 'table', 'tr', 'td', 'p', 'span', 'li'])
    pricing_elements = []
    
    for elem in all_elements:
        text = elem.get_text()
        if text and price_pattern.search(text):
            pricing_elements.append(elem)
    
    if pricing_elements:
        logger.info(f"Found {len(pricing_elements)} elements containing prices via pattern matching")
        pricing_html = ' '.join(str(elem) for elem in pricing_elements)
        return pricing_html
    
    return soup.get_text()


def extract_structured_pricing(text: str) -> str:
    price_pattern = re.compile(r'\$\d+(?:\.\d{2})?|\€\d+(?:\.\d{2})?|\£\d+(?:\.\d{2})?|\¥\d+')
    
    text = re.sub(r'\s+', ' ', text)
    
    plan_pattern = re.compile(
        r'((?:Standard|Premium|Basic|Pro|Plus|Free|Starter|Business|Enterprise|Individual|Family|Student|Essential|Ultimate|Unlimited|Limited|Advanced)[\w\s\-+&]*?)?'
        r'(?:with\s+ads?|no\s+ads?|ad-?free|ad-?supported)?[\s\-]*'
        r'(?:\d{3,4}p|[248]K|HD|4K|UHD)?[\s\-]*'
        r'(?:Monthly|Annual|Yearly)?[\s\-]*'
        r'(?:price|plan|tier|subscription)?[\s:]*'
        r'(\$\d+(?:\.\d{2})?)'
        r'(?:/mo|/month|/yr|/year)?',
        re.IGNORECASE
    )
    
    matches = plan_pattern.finditer(text)
    
    pricing_info = {}
    
    for match in matches:
        full_match = match.group(0).strip()
        price = match.group(2)
        
        if not price:
            continue
        
        full_match = re.sub(r'\s+', ' ', full_match)
        full_match = re.sub(r'\s*:\s*', ' ', full_match)
        
        full_match = re.sub(r'(\d+p)', r'\1 ', full_match)
        full_match = re.sub(r'(Monthly|Annual|Yearly)', r' \1 ', full_match)
        full_match = re.sub(r'(price)', r' \1 ', full_match)
        full_match = re.sub(r'\s+', ' ', full_match)
        
        if price not in pricing_info or len(full_match) > len(pricing_info[price]):
            pricing_info[price] = full_match
    
    if pricing_info:
        lines = []
        for price in sorted(pricing_info.keys(), key=lambda p: float(p.replace('$', '').replace('€', '').replace('£', '').replace('¥', ''))):
            lines.append(pricing_info[price])
        return '\n'.join(lines)
    
    price_matches = price_pattern.findall(text)
    if price_matches:
        unique_prices = []
        seen = set()
        for price in price_matches:
            if price not in seen:
                unique_prices.append(price)
                seen.add(price)
        
        if unique_prices:
            return "Prices found: " + ", ".join(unique_prices)
    
    return text[:500] if len(text) > 500 else text


def normalize_text(text: str, preserve_newlines: bool = False) -> str:
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    if preserve_newlines:
        lines = text.split('\n')
        lines = [re.sub(r'[ \t]+', ' ', line.strip()) for line in lines]
        text = '\n'.join([line for line in lines if line])
    else:
        text = re.sub(r'\s+', ' ', text)
    
    text = text.strip()
    
    return text


def generate_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def process_html(html: str, custom_selector: str = None) -> Tuple[str, str, str]:
    raw_hash = generate_hash(html)
    
    logger.info(f"Processing HTML: {len(html)} bytes")
    
    pricing_content = extract_pricing_content(html, custom_selector)
    logger.info(f"Extracted pricing content: {len(pricing_content)} bytes")
    
    sanitized = sanitize_html(pricing_content)
    logger.info(f"Sanitized content: {len(sanitized)} bytes")
    
    soup = BeautifulSoup(sanitized, 'lxml')
    text_content = soup.get_text()
    logger.info(f"Text content: {len(text_content)} chars")
    
    structured_content = extract_structured_pricing(text_content)
    logger.info(f"Structured pricing: {len(structured_content)} chars")
    
    normalized = normalize_text(structured_content, preserve_newlines=True)
    logger.info(f"Normalized content: {len(normalized)} chars")
    
    normalized_hash = generate_hash(normalized)
    
    return raw_hash, normalized_hash, normalized

