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
    
    price_matches = list(price_pattern.finditer(text))
    if not price_matches:
        return text[:500] if len(text) > 500 else text
    
    pricing_info = {}
    
    for match in price_matches:
        price = match.group(0)
        if price in pricing_info:
            continue
        
        pos = match.start()
        
        before_start = max(0, pos - 250)
        before_text = text[before_start:pos]
        
        after_end = min(len(text), match.end() + 50)
        after_text = text[match.end():after_end]
        
        words_before = before_text.split()
        words_after = after_text.split()
        
        start_idx = max(0, len(words_before) - 20)
        before_snippet = ' '.join(words_before[start_idx:])
        
        end_idx = min(len(words_after), 8)
        after_snippet = ' '.join(words_after[:end_idx])
        
        full_snippet = f"{before_snippet} {price} {after_snippet}".strip()
        
        full_snippet = re.sub(r'(Starting at|starting at)\s*', '', full_snippet, flags=re.IGNORECASE)
        full_snippet = re.sub(r'\s+', ' ', full_snippet).strip()
        
        service_names = re.findall(r'\b(Disney\+|Hulu|ESPN|HBO|Max|Netflix|Prime|YouTube|Paramount|Peacock|Apple|Amazon)\b', full_snippet, re.IGNORECASE)
        
        bundle_pattern = re.search(r'([\w\+,\s]+Bundle|[\w\+,\s]+plan|[\w\+,\s]+tier)', full_snippet, re.IGNORECASE)
        
        has_context = service_names or bundle_pattern
        
        if has_context and len(full_snippet) > 5:
            if len(full_snippet) > 150:
                full_snippet = full_snippet[-150:]
                full_snippet = full_snippet[full_snippet.find(' ')+1:]
            
            pricing_info[price] = full_snippet
    
    if pricing_info:
        lines = []
        for price in sorted(pricing_info.keys(), key=lambda p: float(p.replace('$', '').replace('€', '').replace('£', '').replace('¥', ''))):
            lines.append(f"• {pricing_info[price]}")
        return '\n\n'.join(lines)
    
    unique_prices = []
    seen = set()
    for match in price_matches:
        price = match.group(0)
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

