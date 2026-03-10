import re
import requests

def scrape_job(url):
    try:
        # User requested to use the Jina Reader API exclusively
        print(f"Loading URL using Jina Reader API: {url}")
        
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "Accept": "text/plain",
            "X-Return-Format": "markdown" 
        }
        
        # We increase the timeout slightly because remote rendering takes time
        res = requests.get(jina_url, headers=headers, timeout=20)
        res.raise_for_status()

        text = res.text
        
        # Clean up excessive newlines and whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    except Exception as e:
        print(f"Jina Reader API failed on {url}: {e}")
        # Always return empty string when blocked, triggering the manual fallback gracefully
        return ""
