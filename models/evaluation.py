from langchain_openrouter import ChatOpenRouter

_model = None


def get_model():
    global _model
    if _model is None:
        _model = ChatOpenRouter(
            model="openai/gpt-oss-120b:free",
            temperature=0.8,
        )
    return _model


model = get_model
