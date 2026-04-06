from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from rag_pipeline.rag_chain import load_pipeline

app = FastAPI()

# ✅ Load ONCE (important)
pipeline = load_pipeline()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    response = pipeline.generate_response(req.user_id, req.message)
    return {"response": response}