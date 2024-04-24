import dspy
from langchain_openai import ChatOpenAI 

gpt4 = dspy.OpenAI(model="gpt-4-0125-preview", max_tokens=4096)
turbo_lc = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)