from langchain_openai import ChatOpenAI

_model = None


def get_model():
    global _model
    if _model is None:
        _model = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8,
        )
    return _model


model = get_model
