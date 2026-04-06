#!/usr/bin/env python3
"""
setup.py — COMMANDO Networks RAG Bot — Full Clean Pipeline
"""

import os
import sys
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── CLI flags ─────────────────────────────────────────────
FORCE     = "--force"     in sys.argv
NO_SCRAPE = "--no-scrape" in sys.argv
NO_PDFS   = "--no-pdfs"   in sys.argv

# ── Paths ────────────────────────────────────────────────
RAW_DIR         = "data/raw"
PDF_DIR         = "data/raw/pdfs"
PAGES_JSON      = "data/raw/scraped_data.json"
PDF_LINKS_JSON  = "data/raw/pdf_links.json"
PROCESSED_JSON  = "data/processed/documents.json"

# ─────────────────────────────────────────────────────────
def banner(msg: str):
    print(f"\n{'='*62}\n  {msg}\n{'='*62}")


def step(n: int, total: int, msg: str):
    print(f"\n{'─'*62}")
    print(f"  Step {n}/{total} — {msg}")
    print(f"{'─'*62}")


def abort(msg: str):
    logger.error(msg)
    sys.exit(1)


# ─────────────────────────────────────────────────────────
def clear_data():
    if os.path.exists("data"):
        shutil.rmtree("data")
        print("🧹  Old data/ directory removed.\n")


# ─────────────────────────────────────────────────────────
def run_scraper():
    from data_scraper.scraper import CommandoScraper

    scraper = CommandoScraper(output_dir=RAW_DIR)
    pages = scraper.scrape_all(max_pages=2000)

    # ✅ FULL PATHS HERE ONLY
    scraper.save(
        pages_file=PAGES_JSON,
        pdf_file=PDF_LINKS_JSON
    )

    print(f"\n  ✓ Pages scraped       : {len(pages)}")
    print(f"  ✓ Download links found: {len(scraper.pdf_links)}")

    return len(scraper.pdf_links)


# ─────────────────────────────────────────────────────────
def run_pdf_downloader():
    try:
        from data_scraper.pdf_downloader import PDFDownloader
    except ImportError:
        abort("Cannot import PDFDownloader")

    if not os.path.exists(PDF_LINKS_JSON):
        logger.warning("pdf_links.json not found — skipping PDF downloads.")
        return 0

    dl = PDFDownloader(save_dir=PDF_DIR)
    saved = dl.download_from_json(PDF_LINKS_JSON)

    print(f"\n  ✓  PDFs downloaded: {len(saved)}")
    return len(saved)


# ─────────────────────────────────────────────────────────
def run_processor():
    try:
        from data_scraper.processor import DataProcessor
    except ImportError:
        abort("Cannot import DataProcessor")

    processor = DataProcessor(
        raw_json_path=PAGES_JSON,
        pdf_dir=PDF_DIR,
        output_path=PROCESSED_JSON,
    )

    docs = processor.process()
    print(f"\n  ✓  Document chunks created: {len(docs)}")
    return len(docs)


# ─────────────────────────────────────────────────────────
def run_vector_store():
    try:
        from rag_pipeline.vector_store import build_vector_store_from_json
    except ImportError:
        abort("Cannot import vector store")

    build_vector_store_from_json(PROCESSED_JSON)
    print("\n  ✓  Vector store built successfully")


# ─────────────────────────────────────────────────────────
def main():
    banner("COMMANDO Networks RAG Bot — Full Setup Pipeline")

    if FORCE:
        clear_data()

    total_steps = 4

    # ── Step 1 ───────────────────────────────────────────
    step(1, total_steps, "Crawling website & extracting datasheets")
    if NO_SCRAPE and os.path.exists(PAGES_JSON):
        print("  ⏭   Skipping scrape (using existing data)")
    else:
        run_scraper()

    # ── Step 2 ───────────────────────────────────────────
    step(2, total_steps, "Downloading PDFs")
    if NO_PDFS:
        print("  ⏭   Skipping PDF download")
    else:
        run_pdf_downloader()

    # ── Step 3 ───────────────────────────────────────────
    step(3, total_steps, "Processing & chunking")
    run_processor()

    # ── Step 4 ───────────────────────────────────────────
    step(4, total_steps, "Building vector store")
    run_vector_store()

    # ── DONE ─────────────────────────────────────────────
    banner("✅ SETUP COMPLETE")
    print("""
  Next:
    python test_bot.py
    python -m whatsapp_bot.app
""")


if __name__ == "__main__":
    main()