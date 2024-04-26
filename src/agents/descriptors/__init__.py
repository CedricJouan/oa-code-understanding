
import dspy
from models import *
from typing import List

class FileDescriptorSignature(dspy.Signature): # WE maybe want to give more context in input here... like what's the direcory around him about??...
    file_name = dspy.InputField(desc='The name of the file')
    file_content = dspy.InputField(desc='Content of the File')
    long_description = dspy.OutputField(desc="A description of the file content and purpose.\
                                            The description should be consice and only describe in high level what the file contains.") # we don;t really hint the length here... 

class FileSummarizerSignature(dspy.Signature):
    long_description = dspy.InputField(desc='A detailed description of a file')
    short_description = dspy.OutputField(desc="A summary of the file description. In few short sentences descript what is the file about.\
                                                The summary should be short and only contain the most important information about the file.")

class FileDescriptor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.file_descriptor = dspy.Predict(FileDescriptorSignature)
        self.file_summarizer = dspy.Predict(FileSummarizerSignature)

    def forward(self, file_name:str, file_content:str):
        long_description = self.file_descriptor(
            file_name=file_name,
            file_content=file_content
        )
        long_description_str = long_description.get("long_description")
        short_description = self.file_summarizer(long_description=long_description_str)
        return long_description, short_description
    
###################################################
##########  Python File descriptor  ###############
###################################################

class PyFileSignature(dspy.Signature):
    file_name = dspy.InputField(desc='The name of the Python file')
    file_content = dspy.InputField(desc='Content of the Python file')
    long_description = dspy.OutputField(desc="Detailed description of the Python file.\
                                        The description must contain the documentation for the function classes and methods. \
                                        The description must contain the imports and the dependencies of the file.")
class PyFileSummarizerSignature(dspy.Signature):
    long_description = dspy.InputField(desc='A detailed description of a file')
    short_description = dspy.OutputField(desc="A summary of the file description. In few short sentences descript what is the python file about.\
                                                The summary should be short and only contain the most important information about the file.")

class PyFileDescriptor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.pyfile_descriptor = dspy.Predict(PyFileSignature)
        self.pyfile_summarizer = dspy.Predict(PyFileSummarizerSignature)

    def forward(self, file_name: str, file_content: str):
        long_description = self.pyfile_descriptor(
            file_name=file_name,
            file_content=file_content
        )
        long_description_str = long_description.get("long_description")
        short_description = self.pyfile_summarizer(long_description=long_description_str)
        return long_description, short_description
    

###################################################
################  Dir descriptor  ###############
###################################################

class DirDescriptorSignature(dspy.Signature):
    directory_structure = dspy.InputField(desc='The structure of the directory')
    files_descriptions = dspy.InputField(desc='The descriptions of the files in the directory.')
    children_descriptions = dspy.InputField(desc='The descriptions of the children directories in the directory.')
    long_description = dspy.OutputField(desc="Detailed descrition of the content of the directory.")

class DirDescriptonSummarizerSignature(dspy.Signature):
    long_description = dspy.InputField(desc='A detailed description of the directory')
    short_description = dspy.OutputField(desc="Summary of the content of the directory.\
                                                By looking at this summary, a software engineer should be able to quickly understand what is in the directory and what it is used for.\
                                                The summary should be short only containing a overview of what is in each file and subdirectories.")
    
class DirDescriptor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.dir_descriptor = dspy.Predict(DirDescriptorSignature)
        self.dir_summarizer = dspy.Predict(DirDescriptonSummarizerSignature)

    def forward(self, children_descriptions: List[DirDescription], files_descriptions: List[FileDescription], directory_structure : str):
        long_description = self.dir_descriptor(
            children_descriptions="\n".join([f"Child Directory: {d.name}\n:{d.description}" for d in children_descriptions]),
            files_descriptions="\n".join([f"File: {f.name}\n:{f.description}" for f in files_descriptions]),
            directory_structure=directory_structure
        )
        long_description_str = long_description.get("long_description")
        short_description = self.dir_summarizer(long_description=long_description_str)
        return long_description, short_description

