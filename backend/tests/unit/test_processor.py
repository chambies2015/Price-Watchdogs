import pytest
from app.services.processor import (
    sanitize_html,
    extract_pricing_content,
    normalize_text,
    generate_hash,
    process_html
)


def test_sanitize_html():
    html = """
    <html>
        <head><script>alert('test')</script></head>
        <body>
            <div class="pricing">$10/month</div>
            <script>tracking();</script>
            <style>.hidden { display: none; }</style>
        </body>
    </html>
    """
    
    sanitized = sanitize_html(html)
    
    assert "<script>" not in sanitized
    assert "<style>" not in sanitized
    assert "pricing" in sanitized


def test_extract_pricing_content():
    html = """
    <div class="pricing-table">
        <div class="plan">Basic: $10/month</div>
        <div class="plan">Pro: $20/month</div>
    </div>
    <div class="footer">Copyright 2024</div>
    """
    
    extracted = extract_pricing_content(html)
    
    assert "Basic" in extracted or "$10" in extracted
    assert "Pro" in extracted or "$20" in extracted


def test_normalize_text():
    text = """
    Price:   $10/month
    
    Updated: December 18, 2024
    Cookie banner here
    """
    
    normalized = normalize_text(text)
    
    assert "  " not in normalized
    assert "Cookie" not in normalized or "cookie" not in normalized.lower()


def test_generate_hash_consistency():
    content = "test content"
    
    hash1 = generate_hash(content)
    hash2 = generate_hash(content)
    
    assert hash1 == hash2
    assert len(hash1) == 64


def test_generate_hash_different():
    hash1 = generate_hash("content1")
    hash2 = generate_hash("content2")
    
    assert hash1 != hash2


def test_process_html():
    html = """
    <html>
        <head><script>alert('test')</script></head>
        <body>
            <div class="pricing">
                <h2>Plans</h2>
                <p>Basic: $10/month</p>
                <p>Pro: $20/month</p>
            </div>
        </body>
    </html>
    """
    
    raw_hash, normalized_hash, normalized_content = process_html(html)
    
    assert len(raw_hash) == 64
    assert len(normalized_hash) == 64
    assert raw_hash != normalized_hash
    assert "Plans" in normalized_content or "$10" in normalized_content

