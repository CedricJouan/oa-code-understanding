import dspy
from models import *

# I think dspy is just not ready for agents...

class PyFileCollectorToolSignature(dspy.Signature):
    code_content = dspy.InputField(desc='The content of a python file')
    code_request_question = dspy.InputField(desc="The complete description of what the agent is looking for in this python file")
    output_code_snippets = dspy.OutputField(desc="The relevant code snippets extracted from the code content.")

class PyFileCollectorTool(dspy.Module):
    def __init__(self, file:PyFileBase):
        super().__init__()
        self.file = file
        self.name = f"{self.file.name} Code Snippet Extractor"
        self.desc = f"Extracts code snippets from the {self.file.name} file that best answer the request."
        self.input_variable = "code_request_question" # weird.... 
        self.code_extractor = dspy.ChainOfThought(PyFileCollectorToolSignature)
    def forward(self):
        return self.code_extractor(self.file.content)

class FileCollectorToolSignature(dspy.Signature):
    code_content = dspy.InputField(desc='The content of a python file')
    code_request_question = dspy.InputField(desc="The complete description of what the agent is looking for in this python file")
    output_extracted_information = dspy.OutputField(desc="The relevant information extracted from the code content.")

class FileCollectorTool(dspy.Module):
    def __init__(self, file:FileBase):
        super().__init__()
        self.file = file
        self.name = f"{self.file.name}  Extractor"
        self.desc = f"Extracts information from the {self.file.name} file that best answer the request."
        self.input_variable = "code_request_question"
        self.code_extractor = dspy.ChainOfThought(FileCollectorToolSignature)
    def forward(self):
        return self.code_extractor(self.file.content)

class DirCollectorToolSignature(dspy.Signature):
    code_request_question = dspy.InputField(desc="A request formulated as a question or a statement that can be answered with code snippets from the code directory.")
    code_snipet_answer = dspy.OutputField(desc="The list of code snipets extracted from the directory that best answer the question. \
                                          The code snipets should come with explanations explaining why they are relevant to the request. \
                                          The code snipets should be extracted from the code files in the directory.")


def mk_react_collector(file_collectors, dir_collectors):
    return dspy.ReAct(signature=DirCollectorToolSignature, tools = file_collectors + dir_collectors)
