import sys
import os
from dotenv import load_dotenv

# ✅ Load env first
load_dotenv()

from rag_pipeline.rag_chain import load_pipeline

if __name__ == "__main__":
    user_id = sys.argv[1]
    message = sys.argv[2]

    pipeline = load_pipeline()

    response = pipeline.generate_response(user_id, message)

    print(response)