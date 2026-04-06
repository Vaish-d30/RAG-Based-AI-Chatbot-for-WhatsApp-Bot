import os
import requests
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class PDFDownloader:
    def __init__(self, save_dir="data/raw/pdfs"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.session = requests.Session()

    # 🔥 -------- UNIQUE FILENAME --------
    def generate_filename(self, url, index, content_type):
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")

        # extract product name safely
        if len(parts) >= 3:
            name = parts[-3]
        else:
            name = f"file_{index}"

        name = name.replace("+", "").replace(" ", "_")

        # detect extension
        if "pdf" in content_type:
            ext = ".pdf"
        elif "csv" in content_type:
            ext = ".csv"
        elif "excel" in content_type or "sheet" in content_type:
            ext = ".xlsx"
        else:
            ext = ".bin"

        return f"{name}_{index}{ext}"

    # 🔥 -------- DOWNLOAD SINGLE FILE --------
    def download_file(self, url, index):
        try:
            response = self.session.get(url, timeout=20)

            content_type = response.headers.get("Content-Type", "").lower()

            filename = self.generate_filename(url, index, content_type)
            file_path = os.path.join(self.save_dir, filename)

            # prevent overwrite
            if os.path.exists(file_path):
                base, ext = os.path.splitext(filename)
                filename = f"{base}_dup{ext}"
                file_path = os.path.join(self.save_dir, filename)

            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Saved: {filename} ({content_type})")
            return filename  # ✅ return filename instead of True

        except Exception as e:
            logger.error(f"Download failed: {url} → {e}")
            return None

    # 🔥 -------- DOWNLOAD ALL --------
    def download_all(self, urls):
        saved_files = []

        logger.info(f"Downloading {len(urls)} resource links…")

        for i, url in enumerate(urls, start=1):
            logger.info(f"[{i}/{len(urls)}] {url}")

            result = self.download_file(url, i)

            if result:
                saved_files.append(result)

        logger.info(f"Downloaded {len(saved_files)} files to {self.save_dir}")
        return saved_files  # ✅ return LIST

    # 🔥 -------- LOAD FROM JSON --------
    def download_from_json(self, json_path):
        import json

        with open(json_path, "r", encoding="utf-8") as f:
            urls = json.load(f)

        logger.info(f"Loaded {len(urls)} download links from JSON")

        return self.download_all(urls)