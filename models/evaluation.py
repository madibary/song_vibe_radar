from langchain_openrouter import ChatOpenRouter 

model = ChatOpenRouter(
    model="openai/gpt-oss-120b:free",
    temperature=0.8,
)
