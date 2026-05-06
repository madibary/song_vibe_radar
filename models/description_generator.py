
from langchain_groq import ChatGroq

_model = None


def get_model():
    global _model
    if _model is None:
        _model = ChatGroq(
            model="qwen/qwen3-32b",
            temperature=0.6,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
    return _model


model = get_model
