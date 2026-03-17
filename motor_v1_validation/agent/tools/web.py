"""Web tools — web_search, web_fetch."""

import re
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

FETCH_TIMEOUT = 15
MAX_CONTENT_LEN = 15000


def _strip_html(html: str) -> str:
    """Strip HTML tags and extract text content. No dependencies."""
    # Remove script/style blocks
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Decode common entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tool_web_search(query: str, max_results: int = 5) -> str:
    """Search the web via DuckDuckGo HTML scraping (no API key needed)."""
    import urllib.parse
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"

    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', str(FETCH_TIMEOUT),
             '-H', 'User-Agent: Mozilla/5.0 (compatible; CodeOS/2.0)',
             url],
            capture_output=True, text=True, timeout=FETCH_TIMEOUT + 5
        )
        if result.returncode != 0:
            return f"ERROR: Search failed (rc={result.returncode})"

        html = result.stdout
        # Extract results from DuckDuckGo HTML
        results = []
        # Find result links
        links = re.findall(r'<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                          html, re.DOTALL)
        snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
                             html, re.DOTALL)

        for i, (link, title) in enumerate(links[:max_results]):
            title_clean = _strip_html(title)
            snippet = _strip_html(snippets[i]) if i < len(snippets) else ""
            # Decode DuckDuckGo redirect URL
            if 'uddg=' in link:
                import urllib.parse as up
                match = re.search(r'uddg=([^&]+)', link)
                if match:
                    link = up.unquote(match.group(1))
            results.append(f"{i+1}. {title_clean}\n   {link}\n   {snippet}\n")

        if not results:
            return f"No results found for: {query}"
        return "\n".join(results)

    except subprocess.TimeoutExpired:
        return f"ERROR: Search timed out after {FETCH_TIMEOUT}s"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def tool_web_fetch(url: str) -> str:
    """Fetch a URL and return text content (HTML stripped)."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', str(FETCH_TIMEOUT),
             '-L',  # follow redirects
             '-H', 'User-Agent: Mozilla/5.0 (compatible; CodeOS/2.0)',
             url],
            capture_output=True, text=True, timeout=FETCH_TIMEOUT + 5
        )
        if result.returncode != 0:
            return f"ERROR: Fetch failed (rc={result.returncode})"

        content = result.stdout
        if not content:
            return "ERROR: Empty response"

        # If it looks like HTML, strip tags
        if '<html' in content.lower() or '<body' in content.lower():
            content = _strip_html(content)

        if len(content) > MAX_CONTENT_LEN:
            content = content[:MAX_CONTENT_LEN] + "\n... [TRUNCATED]"

        return content

    except subprocess.TimeoutExpired:
        return f"ERROR: Fetch timed out after {FETCH_TIMEOUT}s"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("web_search", {
        "name": "web_search",
        "description": "Search the web via DuckDuckGo. Returns top results with titles, URLs, snippets.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Max results. Default: 5"}
        }, "required": ["query"]}
    }, lambda a: tool_web_search(a["query"], a.get("max_results", 5)), category="web")

    registry.register("web_fetch", {
        "name": "web_fetch",
        "description": "Fetch a URL and return text content (HTML tags stripped).",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "description": "URL to fetch"}
        }, "required": ["url"]}
    }, lambda a: tool_web_fetch(a["url"]), category="web")
