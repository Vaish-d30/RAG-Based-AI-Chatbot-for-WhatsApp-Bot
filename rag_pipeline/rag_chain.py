import os
import json
import logging
from typing import Dict, List, Optional

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from rag_pipeline.vector_store import VectorStore

load_dotenv()
logger = logging.getLogger(__name__)

# =========================
# 🔥 SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = """You are a premium COMMANDO Networks AI customer support assistant.

Your role:
- Help users with product queries
- Provide company info (contact, website)
- Act like a real chatbot

STRICT RULES:
- DO NOT mention sources or "context"
- DO NOT hallucinate product specs
- Use context if available, otherwise answer normally using instructions

COMPANY INFO:
- Website: https://www.commandonetworks.com
- Email: info@commandonetworks.com
- Address: Navi Mumbai, India

SPECIAL INSTRUCTIONS:

If Query Type = greeting:
- Respond with friendly greeting

If Query Type = contact:
- Provide contact details

If Query Type = website:
- Provide website info

FORMATTING RULES (MANDATORY):
- ALWAYS structured
- ALWAYS bullet points (•)
- ALWAYS spacing between lines
- NO long paragraphs

FORMATS:

👋 Greeting:
• Welcome message  
• Capabilities  

📡 Product:
• Feature: Value  
• Feature: Value  

📞 Contact:
• Email  
• Address  

🌐 Website:
• Link  

🤖 Fallback:
• Suggest better queries  

Context:
{context}
"""

# =========================
# 🔥 CLEAN RESPONSE (FIXED SPACING)
# =========================
def clean_response(text: str) -> str:
    text = text.strip()

    unwanted = [
        "Based on the provided context,",
        "Based on the context,",
        "According to the context,"
    ]

    for phrase in unwanted:
        text = text.replace(phrase, "")

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    formatted = []
    for line in lines:

        # headings
        if line.startswith(("📡", "📞", "🌐", "👋", "🤖")):
            formatted.append(line)
            continue

        # bullet points
        if line.startswith("•"):
            formatted.append(line)
            continue

        # normal text
        formatted.append(line)

    # 🔥 ensure spacing between all lines
    return "\n\n".join(formatted).strip()


# =========================
# 🧠 MEMORY
# =========================
class ConversationMemory:
    def __init__(self, max_history: int = 10):
        self._store: Dict[str, List] = {}
        self.max_history = max_history

    def get_history(self, user_id: str) -> List:
        return self._store.get(user_id, [])

    def add_turn(self, user_id: str, human_msg: str, ai_msg: str):
        if user_id not in self._store:
            self._store[user_id] = []

        self._store[user_id].append(HumanMessage(content=human_msg))
        self._store[user_id].append(AIMessage(content=ai_msg))

        if len(self._store[user_id]) > self.max_history * 2:
            self._store[user_id] = self._store[user_id][-(self.max_history * 2):]


# =========================
# 🚀 RAG PIPELINE
# =========================
class RAGPipeline:
    def __init__(
        self,
        vector_store: VectorStore,
        llm_model: str = "gemini-2.5-flash",
        top_k: int = 8,
        google_api_key: Optional[str] = None,
    ):
        self.vector_store = vector_store
        self.top_k = top_k
        self.memory = ConversationMemory()

        api_key = google_api_key or os.getenv("GOOGLE_API_KEY")

        self.llm = ChatGoogleGenerativeAI(
            model=llm_model,
            temperature=0.2,
            google_api_key=api_key,
            convert_system_message_to_human=True,
        )

    # 🔥 Query Type Detection
    def detect_query_type(self, message: str) -> str:
        msg = message.lower().strip()

        if msg in ["hi", "hello", "hey", "hii"]:
            return "greeting"

        if any(w in msg for w in ["contact", "phone", "email"]):
            return "contact"

        if any(w in msg for w in ["website", "url", "link"]):
            return "website"

        return "general"

    # 🔥 Query Enhancement (context retention)
    def build_query(self, user_id: str, user_message: str) -> str:
        history = self.memory.get_history(user_id)

        last_msgs = [
            msg.content for msg in history if isinstance(msg, HumanMessage)
        ]

        if last_msgs:
            return last_msgs[-1] + " " + user_message

        return user_message

    # 🔥 PURE SEMANTIC SEARCH (FIXED)
    def retrieve_context(self, query: str) -> str:
        docs = self.vector_store.search(query, top_k=self.top_k)

        if not docs:
            return ""

        return "\n\n".join([doc.get("content", "") for doc in docs])

    # 🔥 MAIN RESPONSE
    def generate_response(self, user_id: str, user_message: str) -> str:

        query_type = self.detect_query_type(user_message)
        query = self.build_query(user_id, user_message)

        context = self.retrieve_context(query)
        history = self.memory.get_history(user_id)

        system_msg = SystemMessage(
            content=SYSTEM_PROMPT.format(context=context)
            + f"\nQuery Type: {query_type}"
        )

        messages = [system_msg] + history + [HumanMessage(content=user_message)]

        try:
            response = self.llm.invoke(messages)
            ai_reply = clean_response(response.content)
        except Exception as e:
            logger.error(e)
            ai_reply = "⚠️ Server error. Please try again."

        self.memory.add_turn(user_id, user_message, ai_reply)
        return ai_reply


# =========================
# 🔥 LOAD PIPELINE
# =========================
def load_pipeline(
    docs_path: str = "data/processed/documents.json",
    llm_model: str = "gemini-2.5-flash",
) -> RAGPipeline:

    store = VectorStore()

    if not store.load():
        with open(docs_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        store.build(docs)

    return RAGPipeline(vector_store=store, llm_model=llm_model)