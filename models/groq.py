
from langchain_groq import ChatGroq


model = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.6,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

