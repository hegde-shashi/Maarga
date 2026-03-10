import cloudscraper
import re
from bs4 import BeautifulSoup

def scrape_job(url):
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        res = scraper.get(url, timeout=15)
        res.raise_for_status()

        html = res.text
        soup = BeautifulSoup(html, "html.parser")
        
        for script in soup(["script", "style", "noscript"]):
            script.extract()
            
        text = soup.get_text(separator=" ")
        text = re.sub(r"\s+", " ", text).strip()
        print(text[:200])
        return text

    except Exception as e:
        print(f"Cloudscraper failed on {url}: {e}")
        return ""

scrape_job("https://www.google.com")
