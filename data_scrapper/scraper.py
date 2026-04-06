import os
import json
import time
import logging
from collections import deque
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.commandonetworks.com"
START_URL = BASE_URL + "/"

DOWNLOAD_EXTENSIONS = {".pdf", ".csv", ".doc", ".docx", ".xls", ".xlsx", ".zip"}

DOWNLOAD_PATH_HINTS = [
    "/datasheet/download",
    "/download/",
    "/downloads/",
    "/catalog/download",
]

SKIP_PREFIXES = ["mailto:", "tel:", "javascript:", "#"]
INTERNAL_HOSTS = {"", "commandonetworks.com", "www.commandonetworks.com"}


def normalize_url(url: str) -> str:
    try:
        for _ in range(3):
            url = unquote(url)
    except:
        pass
    return url.split("#")[0].rstrip("/")


def is_internal(url):
    return urlparse(url).netloc in INTERNAL_HOSTS


def is_download(url):
    path = urlparse(url).path.lower()
    return (
        any(path.endswith(ext) for ext in DOWNLOAD_EXTENSIONS)
        or any(h in path for h in DOWNLOAD_PATH_HINTS)
    )

def clean_text(soup):
    # remove useless tags
    for tag in soup(["script", "style"]):
        tag.decompose()

    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", class_="content")
        or soup.body
    )

    if not main:
        return ""

    # 🔥 FIX: DO NOT FILTER SHORT LINES
    text = main.get_text(" ", strip=True)

    return text

class CommandoScraper:
    def __init__(self, output_dir="data/raw"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

        self.visited = set()
        self.queued = set()
        self.pages = []
        self.pdf_links = set()

    def fetch(self, url):
        try:
            res = self.session.get(url, timeout=15)
            if "html" not in res.headers.get("Content-Type", "").lower():
                return None
            return res.text
        except:
            return None

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")

        page_links, pdf_links = [], []

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            if not href or any(href.startswith(p) for p in SKIP_PREFIXES):
                continue

            full = normalize_url(urljoin(base_url, href))

            if full.count("%") > 5:
                continue

            if not is_internal(full):
                continue

            if "/gallery" in full:
                continue

            if is_download(full):
                pdf_links.append(full)
            else:
                page_links.append(full)

        # hidden datasheet buttons
        for tag in soup.find_all(attrs={"data-href": True}):
            href = tag["data-href"].strip()
            full = normalize_url(urljoin(base_url, href))
            if is_download(full):
                pdf_links.append(full)

        return list(set(page_links)), list(set(pdf_links))

    def scrape_all(self, max_pages=2000):
        queue = deque([START_URL])
        self.queued.add(START_URL)

        while queue and len(self.pages) < max_pages:
            url = normalize_url(queue.popleft())

            if url in self.visited:
                continue

            self.visited.add(url)

            if is_download(url):
                self.pdf_links.add(url)
                continue

            logger.info(f"[{len(self.pages)+1}] {url}")

            html = self.fetch(url)
            if not html:
                continue

            try:
                soup = BeautifulSoup(html, "html.parser")
                text = clean_text(soup)
            except:
                continue

            links, pdfs = self.extract_links(html, url)

            self.pages.append({
                "url": url,
                "content": text,
                "pdfs": pdfs
            })

            self.pdf_links.update(pdfs)

            for link in links:
                if link not in self.visited and link not in self.queued:
                    queue.append(link)
                    self.queued.add(link)

            time.sleep(0.2)

        logger.info(f"Pages: {len(self.pages)} | PDFs: {len(self.pdf_links)}")
        return self.pages

    # 🔥 CLEAN SAVE (NO PATH LOGIC)
    def save(self, pages_file=None, pdf_file=None):
        if not pages_file:
            pages_file = os.path.join(self.output_dir, "scraped_data.json")

        if not pdf_file:
            pdf_file = os.path.join(self.output_dir, "pdf_links.json")

        os.makedirs(os.path.dirname(pages_file), exist_ok=True)
        os.makedirs(os.path.dirname(pdf_file), exist_ok=True)

        with open(pages_file, "w", encoding="utf-8") as f:
            json.dump(self.pages, f, indent=2, ensure_ascii=False)

        with open(pdf_file, "w", encoding="utf-8") as f:
            json.dump(list(self.pdf_links), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved pages → {pages_file}")
        logger.info(f"Saved PDFs → {pdf_file}")

if __name__ == "__main__":
    scraper = CommandoScraper()
    scraper.scrape_all(max_pages=2000)
    scraper.save()
