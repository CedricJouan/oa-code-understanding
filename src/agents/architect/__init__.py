
from .architect_prompts import architect_prompt

from models import *
from utils import format_name
from language_models import turbo_lc
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from typing import Optional, Type, List
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.agents import create_openai_tools_agent 
from langchain.agents import AgentExecutor 
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, PromptTemplate 

from language_models import turbo_lc as llm



class RepoCollectorInput(BaseModel):
    information_request: str = Field(description="A request for infomration formulated as a question. This question must be about the content of the directory.")

class RepoCollectorTool(BaseTool):
    repo : DirBase
    name : str
    description : str
    args_schema : Type[BaseModel]
    collector_agent : AgentExecutor
    def __init__(self, repo:DirBase):
        super().__init__(repo=repo,
                         name = format_name(f"{repo.name} Repo expert"),
                         description=f"Subject matter expert for the repository: {repo.name}. This tool can answer questions about the content of the entire repository and its subdirectories. From a request will generate a response with the relevant code snippets and explanations.",
                         args_schema=RepoCollectorInput,
                         collector_agent=repo.get_collector())

    def _run(
        self, 
        information_request: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        return self.collector_agent.invoke({"input":information_request})

    async def _arun(
        self,
        information_request: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        response = await self.collector_agent.ainvoke({"input":information_request})
        return response
        

def mk_architect_agent(repo:DirBase):
    tools = [RepoCollectorTool(repo=repo)]
    system_message_template = architect_prompt.format(directory_name=repo.description.name,
                                                      directory_structure=repo.description.directory_structure,
                                                        directory_description=repo.description.description)

    prompt = ChatPromptTemplate.from_messages( 
        [   SystemMessagePromptTemplate(prompt=PromptTemplate(input_variables=[], template=system_message_template)),
            MessagesPlaceholder(variable_name='chat_history', optional=True), 
            HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='{input}')), 
            MessagesPlaceholder(variable_name='agent_scratchpad')
        ] 
    )
    agent = create_openai_tools_agent(turbo_lc, tools, prompt) 
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)
    return agent_executor
