import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from ai_crawler_cli.tools.registry import registry
from ai_crawler_cli.utils.logger import log

@registry.register(name="fetch_url", description="Fetch text content from a URL.")
def fetch_url(url: str, extract_text: bool = True) -> str:
    """Fetch content from a given URL. If extract_text is true, it parses HTML to text."""
    try:
        log.debug(f"Fetching URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        if extract_text and "text/html" in response.headers.get("Content-Type", ""):
            soup = BeautifulSoup(response.text, "lxml")
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=" ", strip=True)
            return text[:5000] # Return truncated text to fit in context
        
        return response.text[:5000]
    except Exception as e:
        log.error(f"Error fetching {url}: {e}")
        return f"Error: {e}"

@registry.register(name="search_duckduckgo", description="Search the web using DuckDuckGo.")
def search_duckduckgo(query: str, max_results: int = 5) -> str:
    """Search DuckDuckGo Lite and return basic results."""
    # simple implementation for demonstration
    try:
        url = f"https://lite.duckduckgo.com/lite/"
        data = {"q": query}
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.post(url, data=data, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")
        results = []
        for result in soup.find_all('tr'):
            td = result.find('td', class_='result-snippet')
            if td:
                results.append(td.get_text(strip=True))
        return "\n".join(results[:max_results])
    except Exception as e:
        return f"Search error: {e}"
