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
from .collector_tool_prompts import file_collector_prompt, pyfile_collector_prompt, dir_agent_prompt
from langchain.agents import create_openai_tools_agent 
from langchain.agents import AgentExecutor 
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, PromptTemplate 

from language_models import turbo_lc as llm

class PyFileCollectorInput(BaseModel):
    pyfile_request_question: str = Field(description="A request for infomration formulated as a question. This question must be about the content of the python file.")

class PyFileCollectorTool(BaseTool):
    file : PyFileBase
    file_content : str
    name : str
    description : str
    args_schema: Type[BaseModel]
    def __init__(self, file:PyFileBase):
        super().__init__(file=file,
                         file_content=file.content,
                         name=format_name(f"Python file expert {file.name}"),
                         description=f"Expert for the file python file {file.name}. here is a description of the file : {file.description.description}.\nThis tool can answer questions about the content of the file. From a request will generate a response with the relevant code snippets and explanations.",
                         args_schema=PyFileCollectorInput)

    def _run(
        self,
        pyfile_request_question: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        prompt = pyfile_collector_prompt.format(pyfile_path=self.file.description.path,
                                                pyfile_content=self.file_content, 
                                                pyfile_request_question=pyfile_request_question)
        return llm.invoke(prompt)

    async def _arun(
        self,
        pyfile_request_question: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        prompt = pyfile_collector_prompt.format(pyfile_path=self.file.description.path,
                                                pyfile_content=self.file_content, 
                                                pyfile_request_question=pyfile_request_question)
        # Asynchronously invoking the language model or API
        response = await llm.ainvoke(prompt)
        return response


class FileCollectorInput(BaseModel):
    file_request_question: str = Field(description="A request for information formulated as a question. This question must be about the content of the file.")

class FileCollectorTool(BaseTool):
    file : FileBase
    file_content : str
    name : str
    description : str
    args_schema: Type[BaseModel]
    def __init__(self, file:FileBase):
        super().__init__(file=file,
                         file_content=file.content,
                         name=format_name(f"File expert_{file.name}"),
                         description=f"Expert for the file {file.name}. Here is a description of the file : {file.description.description}. \nThis tool can answer questions about the content of the file. From a request will generate a response with the relevant information.",
                         args_schema=FileCollectorInput)

    def _run(
        self, 
        file_request_question: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        prompt = file_collector_prompt.format(file_path=self.file.description.path,
                                              file_content=self.file_content, 
                                              file_request_question=file_request_question)
        return llm.invoke(prompt)

    async def _arun(
        self,
        file_request_question: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        prompt = file_collector_prompt.format(file_path=self.file.description.path,
                                              file_content=self.file_content, 
                                              file_request_question=file_request_question)
        response = await llm.ainvoke(prompt)
        return response
    


class DirCollectorInput(BaseModel):
    information_request: str = Field(description="A request for infomration formulated as a question. This question must be about the content of the directory.")

class DirCollectorTool(BaseTool):
    directory: DirBase
    name: str
    description: str
    args_schema: Type[BaseModel]
    collector_agent: AgentExecutor
    def __init__(self, directory:DirBase):
        super().__init__(directory=directory,
                         name=format_name(f"Directory expert {directory.name}"),
                         description=f"Subject matter expert for the subdirecotry: {directory.name}. here is a description of the directory : {directory.description.description}. \nThis tool can answer questions about the content of the directory and its subdirectories. From a request will generate a response with the relevant code snippets and explanations.",
                         args_schema=DirCollectorInput,
                         collector_agent=directory.get_collector())

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
    

def mk_collector_agent(tools:List[DirCollectorTool|FileCollectorTool|PyFileCollectorTool], 
                       directory:DirBase):
    
    system_message_template = dir_agent_prompt.format(directory_name=directory.description.name,
                                                      directory_structure=directory.description.directory_structure,
                                                        directory_description=directory.description.description)

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






