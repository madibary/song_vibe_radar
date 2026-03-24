from langchain_openrouter import ChatOpenRouter
from tools.tools import get_word_count


model = ChatOpenRouter(
    model="stepfun/step-3.5-flash:free",
    temperature=0.8,
)
model_with_tools = model.bind_tools([get_word_count])
