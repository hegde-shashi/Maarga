import requests
from bs4 import BeautifulSoup
import re

def scrape_job(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        # We use a 15-second timeout and headers to bypass simple bot-checkers
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()

        html = res.text
        soup = BeautifulSoup(html, "html.parser")
        
        # Strip script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=" ")
        
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        
        return text

    except requests.RequestException as e:
        print(f"Error scraping job URL {url}: {e}")
        # Return empty string to trigger fallback to manual copy/paste in route
        return ""
