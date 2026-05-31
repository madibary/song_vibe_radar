
from langchain_openai import ChatOpenAI

_model = None


def get_model():
    global _model
    if _model is None:
        _model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=1.0,
            max_retries=2,
        )
    return _model


model = get_model
