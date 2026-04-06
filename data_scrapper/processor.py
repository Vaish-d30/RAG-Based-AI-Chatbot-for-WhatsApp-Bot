import os
import json
import logging
import re
from typing import List, Dict

import pdfplumber
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self, raw_json_path, pdf_dir, output_path):
        self.raw_json_path = raw_json_path
        self.pdf_dir = pdf_dir
        self.output_path = output_path

        # ✅ OPTIMIZED FOR SEMANTIC SEARCH
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    # -----------------------------
    # 🔥 PRODUCT EXTRACTION
    # -----------------------------
    def extract_product_name(self, text: str) -> str:
        match = re.search(r"[A-Z]{2,}-[A-Z0-9\-]+", text)
        return match.group(0) if match else ""

    # -----------------------------
    # 🔥 SECTION SPLITTING
    # -----------------------------
    def split_by_sections(self, text: str) -> List[str]:
        """
        Splits text into logical sections based on headings.
        Helps prevent mixing multiple products/specs in one chunk.
        """
        sections = re.split(r"\n(?=[A-Z][A-Z\s]{5,})", text)

        clean_sections = []
        for sec in sections:
            sec = sec.strip()
            if len(sec) > 100:
                clean_sections.append(sec)

        return clean_sections

    # -----------------------------
    # 🔥 CLEAN TEXT (IMPORTANT)
    # -----------------------------
    def clean_text(self, text: str) -> str:
        text = re.sub(r"\n+", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    # -----------------------------
    # 🔥 PDF EXTRACTION
    # -----------------------------
    def extract_pdf_text(self, file_path: str) -> str:
        full_text = ""

        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    text = self.clean_text(text)
                    full_text += text + "\n"

                    # Extract tables properly
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            row_text = " | ".join(
                                [str(cell).strip() for cell in row if cell]
                            )
                            if row_text:
                                full_text += row_text + "\n"

        except Exception as e:
            logger.warning(f"PDF error: {file_path} → {e}")

        return full_text.strip()

    # -----------------------------
    # 🔥 FILE TEXT EXTRACTION
    # -----------------------------
    def extract_text_from_file(self, file_path: str) -> str:
        if file_path.endswith(".pdf"):
            return self.extract_pdf_text(file_path)

        elif file_path.endswith(".csv"):
            return open(file_path, encoding="utf-8", errors="ignore").read()

        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)
            return df.to_string()

        return ""

    # -----------------------------
    # 🔥 CHUNKING PIPELINE (2-STAGE)
    # -----------------------------
    def chunk_text(self, text: str) -> List[str]:
        text = self.clean_text(text)

        sections = self.split_by_sections(text)

        chunks = []
        for sec in sections:
            small_chunks = self.text_splitter.split_text(sec)
            chunks.extend(small_chunks)

        return chunks

    # -----------------------------
    # 🔥 PROCESS HTML DATA
    # -----------------------------
    def process_html(self, data: List[Dict]) -> List[Dict]:
        documents = []

        for item in data:
            content = item.get("content", "")
            url = item.get("url", "")

            if not content or len(content) < 50:
                continue

            chunks = self.chunk_text(content)

            for i, chunk in enumerate(chunks):
                product = self.extract_product_name(chunk)

                documents.append({
                    "id": f"html__{url}__{i}",
                    "source": url,
                    "title": url.split("/")[-1],
                    "content": chunk,
                    "product": product,
                    "type": "html"
                })

        logger.info(f"HTML chunks created: {len(documents)}")
        return documents

    # -----------------------------
    # 🔥 PROCESS FILES (PDF/CSV/EXCEL)
    # -----------------------------
    def process_files(self) -> List[Dict]:
        documents = []

        if not os.path.exists(self.pdf_dir):
            logger.warning("PDF directory not found.")
            return documents

        files = os.listdir(self.pdf_dir)
        logger.info(f"Processing {len(files)} files...")

        for file in files:
            file_path = os.path.join(self.pdf_dir, file)

            text = self.extract_text_from_file(file_path)

            if not text or len(text) < 50:
                continue

            chunks = self.chunk_text(text)

            for i, chunk in enumerate(chunks):
                product = self.extract_product_name(chunk)

                documents.append({
                    "id": f"file__{file}__{i}",
                    "source": file,
                    "title": file.replace(".pdf", ""),
                    "content": chunk,
                    "product": product,
                    "type": "file"
                })

        logger.info(f"File chunks created: {len(documents)}")
        return documents

    # -----------------------------
    # 🔥 MAIN PROCESS
    # -----------------------------
    def process(self) -> List[Dict]:
        if not os.path.exists(self.raw_json_path):
            logger.error("Raw JSON file not found!")
            return []

        with open(self.raw_json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        logger.info("Processing HTML data...")
        html_docs = self.process_html(raw_data)

        logger.info("Processing files...")
        file_docs = self.process_files()

        all_docs = html_docs + file_docs

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(all_docs, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ TOTAL CHUNKS CREATED: {len(all_docs)}")

        return all_docs


# -----------------------------
# 🔥 RUN STANDALONE
# -----------------------------
if __name__ == "__main__":
    processor = DataProcessor(
        raw_json_path="data/raw/scraped_data.json",
        pdf_dir="data/raw/pdfs",
        output_path="data/processed/documents.json"
    )

    processor.process()