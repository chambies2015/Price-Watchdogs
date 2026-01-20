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
    r'Terms apply',
    r'Plans available with or without ads\*+',
    r'\bStep\s*\d+\s*of\s*\d+\b',
    r'\bChoose the plan\b',
    r'\bSign In\b',
    r'\bLog In\b',
    r'\bNext\b',
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
    price_pattern = re.compile(r'\$\d+(?:\.\d{2})?|\€\d+(?:\.\d{2})?|\£\d+(?:\.\d{2})?|\¥\d+', re.IGNORECASE)
    plan_hint_pattern = re.compile(r'\b(plan|tier|bundle|duo|trio|basic|standard|premium|mobile)\b', re.IGNORECASE)
    
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
    
    selector_html = ''
    selector_text = ''
    if extracted_elements:
        selector_html = ' '.join(str(elem) for elem in extracted_elements)
        if selector_html:
            selector_text = BeautifulSoup(selector_html, 'lxml').get_text(' ', strip=True)

    all_elements = soup.find_all(['div', 'section', 'article', 'table', 'tr', 'td', 'p', 'span', 'li'])
    pricing_elements = []
    
    for elem in all_elements:
        text = elem.get_text()
        if text and price_pattern.search(text):
            pricing_elements.append(elem)
    
    if pricing_elements:
        logger.info(f"Found {len(pricing_elements)} elements containing prices via pattern matching")
        candidates = []
        seen = set()
        all_found_prices = set()
        for elem in pricing_elements:
            all_found_prices.update(price_pattern.findall(elem.get_text(' ', strip=True) or ''))
            cur = elem
            for _ in range(4):
                if cur is None or getattr(cur, "name", None) is None:
                    break
                key = id(cur)
                if key not in seen:
                    seen.add(key)
                    candidates.append(cur)
                cur = cur.parent

        def score(node) -> tuple[int, int, int]:
            t = node.get_text(' ', strip=True) if node else ''
            prices = set(price_pattern.findall(t))
            hints = len(plan_hint_pattern.findall(t))
            return (len(prices), hints, len(t))

        best_node = max(candidates, key=score)
        currency_html = str(best_node)
        currency_text = best_node.get_text(' ', strip=True)
        currency_prices = set(price_pattern.findall(currency_text)) if currency_text else set()

        if len(currency_prices) < 2 and len(all_found_prices) >= 2 and candidates:
            chosen = []
            chosen_prices = set()
            for node in sorted(candidates, key=score, reverse=True):
                t = node.get_text(' ', strip=True) if node else ''
                node_prices = set(price_pattern.findall(t)) if t else set()
                if not node_prices:
                    continue
                if not (node_prices - chosen_prices):
                    continue
                chosen.append(node)
                chosen_prices.update(node_prices)
                if chosen_prices >= all_found_prices or len(chosen) >= 8:
                    break
            if chosen and len(chosen_prices) > len(currency_prices):
                currency_html = ' '.join(str(n) for n in chosen)
                currency_text = ' '.join(n.get_text(' ', strip=True) for n in chosen)
                currency_prices = chosen_prices

        selector_prices = set(price_pattern.findall(selector_text)) if selector_text else set()
        selector_plan_hints = len(plan_hint_pattern.findall(selector_text)) if selector_text else 0
        currency_plan_hints = len(plan_hint_pattern.findall(currency_text)) if currency_text else 0

        if selector_html and selector_prices:
            if len(currency_prices) > len(selector_prices):
                return currency_html
            if selector_plan_hints == 0 and currency_plan_hints > 0:
                return currency_html
            return selector_html
        return currency_html

    if selector_html and selector_text and price_pattern.search(selector_text):
        return selector_html
    
        return soup.get_text()
    

def extract_structured_pricing(text: str) -> str:
    price_re = r'(?:\$\d+(?:\.\d{2})?|\€\d+(?:\.\d{2})?|\£\d+(?:\.\d{2})?|\¥\d+)'
    price_pattern = re.compile(price_re)

    text = re.sub(r'\s+', ' ', text).strip()
    price_matches = list(price_pattern.finditer(text))
    if not price_matches:
        return text[:500] if len(text) > 500 else text

    bad_plan_fragments = (
        'choose the plan',
        'choose your plan',
        'step 1 of',
        'step 2 of',
        'step 3 of',
        'sign in',
        'log in',
        'next',
        'continue',
        'back',
        'learn more about plan',
    )

    def unit_for(after: str) -> str:
        m = re.search(r'(?:/|per)\s*(month|mo|year|yr)\b', after, re.IGNORECASE)
        if m:
            u = m.group(1).lower()
            return ' / month' if u in ('month', 'mo') else ' / year'
        if re.search(r'\bmonthly\b', after, re.IGNORECASE):
            return ' / month'
        if re.search(r'\b(annual|yearly)\b', after, re.IGNORECASE):
            return ' / year'
        return ''

    def pick_plan(window: str, price_rel: int) -> str:
        candidates = []
        for m in re.finditer(r'([A-Za-z][A-Za-z0-9+,&/\-\s]{2,90}?\b(?:Bundle|Plan|Tier)\b)', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(1).strip()))
        for m in re.finditer(r'([A-Za-z][A-Za-z0-9+,&/\-\s]{2,110}?\b(?:Duo|Trio)\b(?:\s+(?:Basic|Premium))?)', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(1).strip()))
        for m in re.finditer(r'\b(Prime\s+(?:Monthly|Annual|for\s+Young\s+Adults|Access))\b', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(1).strip()))
        for m in re.finditer(r'\b(Paramount\+\s+(?:Premium|Essential))\b', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(1).strip()))
        for m in re.finditer(r'\b(Apple\s+TV\+)\b', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(1).strip()))
        for m in re.finditer(r'\b(Premium\s+Plus)\b', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(1).strip()))
        for m in re.finditer(r'\b(Select|Individual|Student|Family)\b', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(1).strip()))
        for m in re.finditer(r'((?:Disney\+|Hulu|ESPN\+|Max|HBO\s*Max)[A-Za-z0-9+,&/\-\s]{2,140}?(?:Bundle|Duo|Trio|Premium|Basic|Standard|Hulu|ESPN\+|Disney\+|Max|HBO\s*Max))', window, re.IGNORECASE):
            val = m.group(1).strip()
            if sum(1 for k in ('disney+', 'hulu', 'espn+', 'max') if k in val.lower()) >= 2 or re.search(r'\b(bundle|duo|trio)\b', val, re.IGNORECASE):
                candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), val))
        for m in re.finditer(r'\b(Basic|Standard|Premium|Premium\s+Plus|Select|Mobile)\b(?:\s+(?:with\s+ads|ad[- ]free|no\s+ads))?', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(0).strip()))
        for m in re.finditer(r'\b(With\s+Ads|Ad[- ]Free|Ultimate\s+Ad[- ]Free)\b', window, re.IGNORECASE):
            candidates.append((abs(((m.start() + m.end()) // 2) - price_rel), m.group(0).strip()))
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return ''

    def clean_plan(plan: str) -> str:
        plan = re.sub(r'\s+', ' ', plan).strip(' -—|')
        plan = re.sub(r'^Select\s+(?=(?:Disney\+|Hulu|ESPN\+|Max|HBO\s*Max)\b)', '', plan, flags=re.IGNORECASE).strip()
        plan = re.sub(r'^(?:month|monthly|year|yearly|annual)\b\s*', '', plan, flags=re.IGNORECASE).strip()
        plan = re.sub(r'^\d+(?:\.\d+)?\s*(?:/|per)\s*(?:month|mo|year|yr)\b\s*', '', plan, flags=re.IGNORECASE).strip()
        plan = re.sub(r'^\d+\s*/\s*(?:month|mo|year|yr)\b\s*', '', plan, flags=re.IGNORECASE).strip()
        plan = re.sub(r'^(?:\d+\s*)?(?:mo|mos|month|months)\b[^,–—]*\s*(?:,|–|—)\s*', '', plan, flags=re.IGNORECASE).strip()
        plan = re.sub(r'^(?:for\s+your\s+first|over\s+your\s+first)\s+\d+\s+months?\b[^,–—]*\s*(?:,|–|—)\s*', '', plan, flags=re.IGNORECASE).strip()
        plan = re.sub(r'^mo\s+(?:thereafter|for\s+your\s+first)\b[^,–—]*\s*(?:,|–|—)\s*', '', plan, flags=re.IGNORECASE).strip()
        plan = re.sub(r'^(Starting at|From)\s+', '', plan, flags=re.IGNORECASE)
        plan = re.sub(r'\b(Terms apply|Plans available with or without ads)\b.*$', '', plan, flags=re.IGNORECASE).strip()
        plan_l0 = plan.lower()
        is_bundleish = bool(re.search(r'\b(bundle|duo|trio)\b', plan_l0))
        services_in_plan = sum(1 for k in ('disney+', 'hulu', 'espn+', 'max') if k in plan_l0)
        if plan_l0.startswith('netflix '):
            plan = plan.split(' ', 1)[1].strip()
        elif plan_l0.startswith('disney+ ') and not is_bundleish and services_in_plan <= 1:
            plan = plan.split(' ', 1)[1].strip()
        elif plan_l0.startswith('hulu ') and not is_bundleish and services_in_plan <= 1:
            plan = plan.split(' ', 1)[1].strip()
        elif plan_l0.startswith('espn+ ') and not is_bundleish and services_in_plan <= 1:
            plan = plan.split(' ', 1)[1].strip()
        plan_l = plan.lower()
        services_in_plan2 = sum(1 for k in ('disney+', 'hulu', 'espn+', 'max') if k in plan_l)
        if services_in_plan2 >= 2 and not is_bundleish:
            if 'disney+' in plan_l and 'hulu' in plan_l and 'espn+' in plan_l:
                plan = 'Disney+, Hulu, ESPN+ Bundle'
            elif 'disney+' in plan_l and 'hulu' in plan_l and 'max' in plan_l:
                plan = 'Disney+, Hulu, Max Bundle'
            elif 'disney+' in plan_l and 'hulu' in plan_l:
                plan = 'Disney+, Hulu Bundle'
            elif 'disney+' in plan_l and 'espn+' in plan_l:
                plan = 'Disney+, ESPN+ Bundle'
        if re.search(r'\byoutube\s+tv\s+base\s+plan\b', plan, re.IGNORECASE):
            plan = 'YouTube TV Base Plan'
        if any(frag in plan.lower() for frag in bad_plan_fragments):
            return ''
        if re.search(r'\bincluded with any\b.*\bplan\b', plan, re.IGNORECASE):
            return ''
        plan = re.sub(r'\b(YouTube TV Base Plan)(?:\s+\1)+\b', r'\1', plan, flags=re.IGNORECASE).strip()
        canonical = {
            'basic': 'Basic',
            'standard': 'Standard',
            'premium': 'Premium',
            'premium plus': 'Premium Plus',
            'select': 'Select',
            'mobile': 'Mobile',
            'standard with ads': 'Standard with Ads',
            'with ads': 'Basic with Ads',
            'ad-free': 'Standard',
            'ad free': 'Standard',
            'ultimate ad-free': 'Premium',
            'ultimate ad free': 'Premium',
        }
        plan_l = plan.lower()
        if plan_l in canonical:
            return canonical[plan_l]
        return plan

    def merge_best(pairs: list[tuple[str, str, str]]) -> list[str]:
        by_plan: dict[str, tuple[str, str, str]] = {}
        for plan, price, unit in pairs:
            if not plan:
                continue
            key = plan.lower()
            if key not in by_plan:
                by_plan[key] = (plan, price, unit)
                continue
            prev_plan, prev_price, prev_unit = by_plan[key]
            if prev_unit == ' / year' and unit == ' / month':
                by_plan[key] = (plan, price, unit)
                continue
            if not prev_unit and unit:
                by_plan[key] = (plan, price, unit)
                continue
            if prev_price == price and prev_unit == unit:
                continue
            by_plan[key] = (prev_plan, prev_price, prev_unit)
        ordered = sorted(by_plan.values(), key=lambda x: x[0].lower())
        return [f"{plan} — {price}{unit}" for plan, price, unit in ordered]

    pairs: list[tuple[str, str, str]] = []
    pair_patterns = [
        re.compile(rf'(?P<plan>(?:Disney\+|Hulu|ESPN(?:\s+Select|\s+Unlimited)?|Max|HBO\s*Max)[A-Za-z0-9+,&/\-\s]{{2,220}}?\bBundle\b(?:\s+Premium|\s+Legacy|\s*\(.*?\))?)(?P<body>.{{0,2600}}?)\b(?P<label>Monthly|Annual|Yearly)\s*:\s*(?P<price>{price_re})', re.IGNORECASE),
        re.compile(rf'(?P<plan>Disney\+[A-Za-z0-9+,&/\-\s]{{2,160}}?\bBundle\b)(?P<body>.{{0,2600}}?)\bStarting\s+at\b\s*(?P<price>{price_re})\s*(?:/|per)\s*(?P<unit>month|mo|year|yr)\b', re.IGNORECASE),
        re.compile(rf'(?P<plan>\bPrime\s+(?:Monthly|Annual|for\s+Young\s+Adults|Access)\b)(?P<body>.{{0,140}}?)\s*(?P<price>{price_re})\s*(?:/|per)\s*(?P<unit>month|mo|year|yr)\b', re.IGNORECASE),
        re.compile(rf'(?P<plan>\bApple\s+TV\+\b)(?P<body>.{{0,220}}?)\s*(?P<price>{price_re})(?P<tail>.{{0,60}})', re.IGNORECASE),
        re.compile(rf'(?P<plan>\bParamount\+\s+(?:Premium|Essential)\b)(?P<body>.{{0,140}}?)\s*(?P<price>{price_re})\s*(?:/|per)\s*(?P<unit>month|mo|year|yr)\b', re.IGNORECASE),
        re.compile(rf'(?P<plan>\b(?:Select|Premium\s+Plus|Premium)\b)(?P<body>.{{0,140}}?)\s*(?P<price>{price_re})\s*(?:/|per)\s*(?P<unit>month|mo|year|yr)\b', re.IGNORECASE),
        re.compile(rf'(?P<plan>\b(?:Individual|Student|Duo|Family)\b)(?P<body>.{{0,180}}?)\s*(?P<price>{price_re})\s*(?:/|per)\s*(?P<unit>month|mo|year|yr)\b', re.IGNORECASE),
        re.compile(rf'(?P<plan>[A-Za-z][A-Za-z0-9+,&/\-\s]{{2,80}}?\b(?:Bundle|Plan|Tier)\b)\s*(?:[-–—:|]\s*)?(?P<price>{price_re})(?P<tail>.{{0,40}})', re.IGNORECASE),
        re.compile(rf'(?P<plan>\b(?:Basic|Standard(?:\s+with\s+ads)?|Premium|Mobile|With\s+Ads|Ad[- ]Free|Ultimate\s+Ad[- ]Free)\b(?:\s+(?:with\s+ads|ad[- ]free|no\s+ads))?)\s*(?P<body>.{{0,60}}?)\s*(?P<price>{price_re})(?P<tail>(?:(?!\b(?:Basic|Standard|Premium|Mobile|With\s+Ads|Ad[- ]Free|Ultimate\s+Ad[- ]Free)\b).){{0,80}})', re.IGNORECASE),
        re.compile(rf'(?P<price>{price_re})\s*(?:/|per)\s*(?P<unit>month|mo|year|yr)\b(?P<tail>.{{0,40}}?)\s*(?P<plan>[A-Za-z][A-Za-z0-9+,&/\-\s]{{2,80}}?\b(?:Bundle|Plan|Tier)\b)', re.IGNORECASE),
        re.compile(rf'(?P<plan>(?:(?:Disney\+|Hulu|ESPN\+|Max|HBO\s*Max)[A-Za-z0-9+,&/\-\s]{{2,150}}?)(?:Duo|Trio|Bundle|Premium|Basic|Standard|Hulu|ESPN\+|Disney\+|Max|HBO\s*Max))\s*(?:[-–—:|]\s*)?(?P<price>{price_re})(?P<tail>.{{0,60}})', re.IGNORECASE),
    ]
    for pat in pair_patterns:
        for m in pat.finditer(text):
            plan = clean_plan(m.group('plan'))
            price = m.group('price')
            tail = (m.groupdict().get('tail') or '') + ' ' + (m.groupdict().get('body') or '')
            unit = ''
            if m.groupdict().get('unit'):
                unit = ' / month' if m.group('unit').lower() in ('month', 'mo') else ' / year'
            if not unit and m.groupdict().get('label'):
                unit = ' / month' if m.group('label').lower() == 'monthly' else ' / year'
            if not unit:
                unit = unit_for(tail)
            if plan:
                pairs.append((plan, price, unit))
    merged = merge_best(pairs)
    if merged:
        if any(re.search(r' — \\$(?!0(?:\\.00)?\\b)', line) for line in merged):
            merged = [line for line in merged if not re.search(r' — \\$0(?:\\.00)?\\b', line)]
        parsed: list[tuple[str, str, str]] = []
        for line in merged:
            if ' — ' not in line:
                continue
            plan, rest = line.split(' — ', 1)
            m = re.search(r'(\$\d+(?:\.\d{2})?|\€\d+(?:\.\d{2})?|\£\d+(?:\.\d{2})?|\¥\d+)(.*)$', rest)
            if not m:
                continue
            parsed.append((plan.strip(), m.group(1), m.group(2).strip()))
        keep = [True] * len(parsed)
        for i in range(len(parsed)):
            pi, pri, ui = parsed[i]
            for j in range(len(parsed)):
                if i == j:
                    continue
                pj, prj, uj = parsed[j]
                if pri == prj and ui == uj and pi.lower() in pj.lower() and len(pj) > len(pi):
                    keep[i] = False
                    break
        filtered = [merged[i] for i in range(len(merged)) if i < len(keep) and keep[i]]
        return '\n\n'.join(f"• {line}" for line in (filtered or merged))

    lines = []
    seen = set()
    for match in price_matches:
        price = match.group(0)
        after = text[match.end():match.end() + 120]
        unit = unit_for(after)

        plan = ''
        for before_chars, after_chars in ((450, 250), (900, 800)):
            w_start = max(0, match.start() - before_chars)
            w_end = min(len(text), match.end() + after_chars)
            window = text[w_start:w_end]
            price_rel = match.start() - w_start
            plan = clean_plan(pick_plan(window, price_rel))
            if plan:
                break
        key = (plan.lower(), price, unit)
        if key in seen:
            continue
        seen.add(key)

        if plan:
            lines.append(f"{plan} — {price}{unit}")

    if lines:
        return '\n\n'.join(f"• {line}" for line in lines)

    unique_prices = []
    seen_prices = set()
    for match in price_matches:
        p = match.group(0)
        if p not in seen_prices:
            unique_prices.append(p)
            seen_prices.add(p)
    return "Prices found: " + ", ".join(unique_prices)


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
    
    soup = BeautifulSoup(pricing_content, 'lxml')
    text_content = soup.get_text(separator=' ', strip=True)
    logger.info(f"Text content extracted: {len(text_content)} chars")
    
    structured_content = extract_structured_pricing(text_content)
    logger.info(f"Structured pricing: {len(structured_content)} chars")
    
    normalized = normalize_text(structured_content, preserve_newlines=True)
    logger.info(f"Normalized content: {len(normalized)} chars")
    
    normalized_hash = generate_hash(normalized)
    
    return raw_hash, normalized_hash, normalized

