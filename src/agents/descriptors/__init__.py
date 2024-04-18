
import dspy
from models import *
from typing import List


class FileDescriptorSignature(dspy.Signature): # WE maybe want to give more context in input here... like what's the direcory around him about??...
    file_name = dspy.InputField(desc='The name of the file')
    file_content = dspy.InputField(desc='Content of the File')
    long_description = dspy.OutputField(desc="A description of the file content and purpose.") # we don;t really hint the length here... 

class FileDescriptor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.file_descriptor = dspy.ChainOfThought(FileDescriptorSignature)

    def forward(self, file_name:str, file_content:str):
        long_description = self.file_descriptor(
            file_name=file_name,
            file_content=file_content
        )
        return long_description
    
###################################################
##########  Python File descriptor  ###############
###################################################

class PyFileSignature(dspy.Signature):
    file_name = dspy.InputField(desc='The name of the Python file')
    file_content = dspy.InputField(desc='Content of the Python file')
    long_description = dspy.OutputField(desc="Detailed description of the Python file.\
                                        the description must contain the documentation for the function classes and methods. \
                                        The description must contain the imports and the dependencies of the file.")

class PyFileDescriptor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.analyzer = dspy.ChainOfThought(PyFileSignature)

    def forward(self, file_name: str, file_content: str):
        long_description = self.analyzer(
            file_name=file_name,
            file_content=file_content
        )
        return long_description
    


class DirDescriptorSignature(dspy.Signature):
    directory_structure = dspy.InputField(desc='The structure of the directory')
    files_descriptions = dspy.InputField(desc='The descriptions of the files in the directory.')
    children_descriptions = dspy.InputField(desc='The descriptions of the children directories in the directory.')
    long_description = dspy.OutputField(desc="Detailed descrition of the content of the directory.")

class DirDescriptonSummarizerSignature(dspy.Signature):
    long_description = dspy.InputField(desc='A detailed description of the directory')
    short_description = dspy.OutputField(desc="Summary of the content of the directory.\
                                                 By looking at this summary, a software engineer should be able to quickly understand what is in the directory and what it is used for.")
    
class DirDescriptor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.dir_descriptor = dspy.ChainOfThought(DirDescriptorSignature)
        self.dir_summarizer = dspy.ChainOfThought(DirDescriptonSummarizerSignature)

    def forward(self, children_descriptions: List[DirDescription], files_descriptions: List[FileDescription], directory_structure : str):
        long_description = self.dir_descriptor(
            children_descriptions="\n".join([f"Child Directory: {d.name}\n:{d.description}" for d in children_descriptions]),
            files_descriptions="\n".join([f"File: {f.name}\n:{f.description}" for f in files_descriptions]),
            directory_structure=directory_structure
        )
        long_description_str = long_description.get("long_description")
        short_description = self.dir_summarizer(long_description=long_description_str)
        return long_description, short_description

