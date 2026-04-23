#!/usr/bin/env python3
"""
Test suite for web_tools.py — WebScraper, YouTubeSummarizer, FinanceScraper.
Tests import, instantiation, method signatures, and live functionality
where network is available.
"""

import sys
import os
import traceback

# Ensure we can import from the Agent-Larry directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

passed = 0
failed = 0
skipped = 0

def test(name, fn):
    global passed, failed, skipped
    try:
        result = fn()
        if result == "SKIP":
            skipped += 1
            print(f"  ⏭️  {name} — skipped")
        else:
            passed += 1
            print(f"  ✅ {name}")
    except Exception as e:
        failed += 1
        print(f"  ❌ {name}: {e}")
        traceback.print_exc()


print("=" * 60)
print("Web & Finance Tools — Test Suite")
print("=" * 60)

# ── 1. Import tests ──────────────────────────────────────────────────
print("\n📦 Import Tests:")

def test_imports():
    from web_tools import (
        WebScraper, YouTubeSummarizer, FinanceScraper,
        get_web_scraper, get_youtube_summarizer, get_finance_scraper,
    )
    assert WebScraper is not None
    assert YouTubeSummarizer is not None
    assert FinanceScraper is not None
test("Import all classes and factories", test_imports)


# ── 2. Instantiation tests ───────────────────────────────────────────
print("\n🔧 Instantiation Tests:")

from web_tools import (
    WebScraper, YouTubeSummarizer, FinanceScraper,
    get_web_scraper, get_youtube_summarizer, get_finance_scraper,
    BS4_AVAILABLE, HTML2TEXT_AVAILABLE, YT_TRANSCRIPT_AVAILABLE,
    PLAYWRIGHT_AVAILABLE,
)

ws = None
yt = None
fs = None

def test_web_scraper_init():
    global ws
    ws = get_web_scraper("/tmp/test_exports")
    assert ws is not None
    assert hasattr(ws, 'scrape')
    assert hasattr(ws, 'scrape_to_markdown')
    assert hasattr(ws, 'summarize_url')
    assert hasattr(ws, 'fetch_url')
test("WebScraper init + methods exist", test_web_scraper_init)

def test_youtube_init():
    global yt
    yt = get_youtube_summarizer("/tmp/test_exports")
    assert yt is not None
    assert hasattr(yt, 'summarize')
    assert hasattr(yt, 'get_transcript')
    assert hasattr(yt, 'get_video_summary')
    assert hasattr(yt, 'process_video')
    assert hasattr(yt, 'extract_video_id')
test("YouTubeSummarizer init + methods exist", test_youtube_init)

def test_finance_init():
    global fs
    fs = get_finance_scraper()
    assert fs is not None
    assert hasattr(fs, 'get_prices')
    assert hasattr(fs, 'get_sentiment')
    assert hasattr(fs, 'scrape_headlines')
    assert hasattr(fs, 'scrape_forexfactory')
    assert hasattr(fs, 'scrape_x_posts')
    assert hasattr(fs, 'scrape_page')
test("FinanceScraper init + methods exist", test_finance_init)


# ── 3. Dependency status ─────────────────────────────────────────────
print("\n📋 Dependency Status:")
print(f"  BeautifulSoup4: {'✅' if BS4_AVAILABLE else '❌'}")
print(f"  html2text:      {'✅' if HTML2TEXT_AVAILABLE else '❌'}")
print(f"  YouTube API:    {'✅' if YT_TRANSCRIPT_AVAILABLE else '❌'}")
print(f"  Playwright:     {'✅' if PLAYWRIGHT_AVAILABLE else '❌'}")


# ── 4. WebScraper functional tests ───────────────────────────────────
print("\n🌐 WebScraper Functional Tests:")

def test_fetch_url():
    if not ws:
        return "SKIP"
    content, success = ws.fetch_url("https://httpbin.org/html")
    assert success, f"fetch_url failed"
    assert len(content) > 100, f"Content too short: {len(content)}"
test("fetch_url (httpbin.org)", test_fetch_url)

def test_scrape():
    if not ws or not BS4_AVAILABLE:
        return "SKIP"
    result = ws.scrape("https://httpbin.org/html")
    assert result is not None, "scrape() returned None"
    assert len(result) > 50, f"Scrape result too short: {len(result)}"
test("scrape() returns markdown", test_scrape)

def test_html_to_markdown():
    if not ws or not BS4_AVAILABLE:
        return "SKIP"
    html = "<html><head><title>Test</title></head><body><h1>Hello</h1><p>World</p></body></html>"
    md = ws.html_to_markdown(html, "https://test.com")
    assert "Test" in md
    assert "Hello" in md or "World" in md
test("html_to_markdown conversion", test_html_to_markdown)


# ── 5. YouTubeSummarizer functional tests ────────────────────────────
print("\n📺 YouTubeSummarizer Functional Tests:")

def test_extract_video_id():
    assert yt.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert yt.extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert yt.extract_video_id("https://youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert yt.extract_video_id("https://youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert yt.extract_video_id("not a url") is None
test("extract_video_id (various formats)", test_extract_video_id)

def test_chunk_transcript():
    text = "Sentence one. " * 200  # ~2800 chars
    chunks = yt.chunk_transcript(text, chunk_size=500, overlap=100)
    assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"
    assert all("text" in c for c in chunks)
test("chunk_transcript splits correctly", test_chunk_transcript)

def test_summarize_method_exists():
    """Verify the summarize() alias exists and is callable."""
    assert callable(getattr(yt, 'summarize', None))
test("summarize() alias is callable", test_summarize_method_exists)


# ── 6. FinanceScraper functional tests ───────────────────────────────
print("\n📊 FinanceScraper Functional Tests:")

def test_crypto_prices():
    if not fs:
        return "SKIP"
    data = fs.get_prices(["bitcoin", "ethereum"], "crypto")
    # CoinGecko may rate-limit, so just check structure
    if "error" not in data:
        assert "bitcoin" in data, f"Missing bitcoin key: {data}"
        btc = data["bitcoin"]
        assert "price_usd" in btc, f"Missing price_usd: {btc}"
        print(f"      BTC=${btc['price_usd']}")
test("get_prices crypto (CoinGecko)", test_crypto_prices)

def test_forex_prices():
    if not fs:
        return "SKIP"
    data = fs.get_prices(["USD"], "forex")
    if "error" not in data:
        assert any("/" in k for k in data), f"No pair keys: {data}"
        for k, v in list(data.items())[:3]:
            print(f"      {k}={v}")
test("get_prices forex (open.er-api.com)", test_forex_prices)

def test_scrape_page_fallback():
    """Test scrape_page with requests fallback (no Playwright)."""
    if not fs:
        return "SKIP"
    text = fs._scrape_requests("https://httpbin.org/html")
    assert len(text) > 50, f"Too short: {len(text)}"
test("scrape_page requests fallback", test_scrape_page_fallback)

def test_headlines():
    if not fs:
        return "SKIP"
    result = fs.scrape_headlines("reuters")
    # May fail due to JS rendering, but should not crash
    assert isinstance(result, str)
    if result and not result.startswith(("Playwright error", "Request failed")):
        print(f"      First headline: {result.split(chr(10))[0][:80]}...")
test("scrape_headlines (reuters)", test_headlines)

def test_unknown_source():
    if not fs:
        return "SKIP"
    result = fs.scrape_headlines("nonexistent")
    assert "Unknown source" in result
test("scrape_headlines rejects unknown source", test_unknown_source)

def test_site_profiles():
    """Verify site profiles are correctly defined."""
    assert "forexfactory.com" in fs.SITE_PROFILES
    assert "x.com" in fs.SITE_PROFILES
    assert "wait" in fs.SITE_PROFILES["forexfactory.com"]
test("SITE_PROFILES configuration", test_site_profiles)


# ── 7. Integration: agent_v2 import check ────────────────────────────
print("\n🔌 Agent Integration Tests:")

def test_agent_import():
    """Verify agent_v2 can import the new exports."""
    # Simulate what agent_v2 does
    from web_tools import (
        WebScraper, YouTubeSummarizer, FinanceScraper,
        get_web_scraper, get_youtube_summarizer, get_finance_scraper,
    )
    scraper = get_web_scraper("/tmp/test")
    youtube = get_youtube_summarizer("/tmp/test")
    finance = get_finance_scraper()
    assert scraper.scrape is not None
    assert youtube.summarize is not None
    assert finance.get_sentiment is not None
test("agent_v2 import pattern works", test_agent_import)


# ── Summary ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
print("=" * 60)

if failed:
    sys.exit(1)
