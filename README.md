# 🤖 RAG-Based WhatsApp AI Chatbot

An end-to-end **Retrieval-Augmented Generation (RAG)** chatbot built using **LangChain, FAISS, and Gemini**, capable of answering domain-specific queries with **semantic search** and maintaining **conversation context across multiple users**.

The chatbot is deployed as a **WhatsApp bot**, enabling real-time interaction through natural language.

---

## 🚀 Features

* 🔍 **Semantic Search (RAG)**

  * Uses FAISS + Sentence Transformers for high-quality retrieval
  * Cross-encoder reranking for improved relevance

* 🧠 **Context Retention**

  * Maintains per-user conversation history
  * Handles follow-up questions intelligently

* 📄 **Multi-Source Data Ingestion**

  * Web scraping + PDF + CSV + Excel support
  * Structured chunking optimized for semantic retrieval

* 🤖 **LLM Integration**

  * Google Gemini (via LangChain)
  * Generates structured, human-like responses

* 📱 **WhatsApp Bot Integration**

  * Built using `whatsapp-web.js`
  * FastAPI backend for real-time responses

---

## 🏗️ Architecture

```text
User (WhatsApp)
      ↓
Node.js (WhatsApp Bot)
      ↓
FastAPI Backend (/chat)
      ↓
RAG Pipeline
  ├── Vector Store (FAISS)
  ├── Retriever (Semantic Search + Reranking)
  ├── LLM (Gemini)
  └── Memory (Per-user context)
      ↓
Response → WhatsApp
```

---

## 📂 Project Structure

```bash
RAG-WhatsApp-Bot/
│
├── data_scraper/        # Web scraping + PDF downloader
├── rag_pipeline/        # RAG logic (vector store + chain)
│
├── api.py               # FastAPI backend
├── bot.js               # WhatsApp bot (Node.js)
├── test_bot.py          # Local testing (CLI)
├── setup.py             # Full pipeline setup
├── requirements.txt     # Dependencies
├── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone Repository

```bash
git clone <your-repo-link>
cd RAG-WhatsApp-Bot
```

---

### 2. Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Set Environment Variables

Create a `.env` file:

```env
GOOGLE_API_KEY=your_api_key_here
```

---

### 5. Run Full Pipeline

```bash
python setup.py
```

This will:

* Scrape website data
* Download PDFs
* Process & chunk data
* Build FAISS vector store

---

### 6. Run Backend

```bash
python api.py
```

---

### 7. Run WhatsApp Bot

```bash
node bot.js
```

* Scan QR code
* Start chatting with the bot

---

## 🧪 Local Testing (Without WhatsApp)

```bash
python test_bot.py
```

---

## 💬 Sample Queries

* Which switches support stacking?
* What are the models available in it?
* What is the PoE budget for 24-port switches?
* Does it support VLAN?

---

## 🧠 Key Design Decisions

* **Pure Semantic Retrieval**

  * No keyword-based hardcoding
  * Fully embedding-driven search

* **Two-Stage Chunking**

  * Section-based + recursive splitting
  * Prevents mixing product specifications

* **Reranking Layer**

  * Cross-encoder improves accuracy of top results

* **Conversation Memory**

  * Maintains user-specific dialogue context

---

## 📦 Tech Stack

* **Backend:** FastAPI, Python
* **LLM:** Google Gemini
* **RAG:** LangChain
* **Vector DB:** FAISS
* **Embeddings:** Sentence Transformers
* **Frontend:** WhatsApp (whatsapp-web.js)
* **Parsing:** BeautifulSoup, PDFPlumber

---

## 🔮 Future Improvements

* Deploy on cloud (AWS / GCP)
* Add authentication & user session storage (Redis/DB)
* Improve latency with caching
* Add UI dashboard for analytics
* Support multi-language queries

---

## 🎥 Demo

A short demo video showcasing:

* Product queries
* Follow-up questions (context retention)
* WhatsApp interaction

---

## 📌 Conclusion

This project demonstrates a production-ready **RAG chatbot system** with:

* Accurate semantic retrieval
* Context-aware conversations
* Real-world deployment via WhatsApp

---

