import requests
from bs4 import BeautifulSoup

def scrape_site(url):

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        texts = []

        for p in soup.find_all("p")[:15]:
            t = p.get_text().strip()
            if len(t) > 40:
                texts.append(t)

        return " ".join(texts)

    except:
        return ""
