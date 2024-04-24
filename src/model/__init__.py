from models import *
from agents.descriptors import FileDescriptor, PyFileDescriptor, DirDescriptor
from agents.collectors import DirCollectorTool, FileCollectorTool, PyFileCollectorTool, mk_collector_agent
from agents.architect import mk_architect_agent
from langchain.agents import AgentExecutor 
import os
import pickle
from typing import List, Optional


class File(FileBase):
    name: str
    content: str
    parent : Optional['Directory'] = None
    collector_tool: Optional[FileCollectorTool] = None
    description: Optional[FileDescription] = None

    def __repr__(self):
        return f"File(name={self.name})"
    
    def get_file_path(self):
        return os.path.join(self.parent.get_file_path(), self.name)
    
    def get_tool(self):
        if self.collector_tool is None:
            self.collector_tool = FileCollectorTool(file=self)
        return self.collector_tool
    
    def get_description(self):
        if self.description is None:
            descriptor = FileDescriptor()
            description = descriptor(self.name, self.content)
            self.description = FileDescription(name=self.name, 
                                               path=self.get_file_path(),
                                               description=description.get("long_description"))
        return self.description

class PyFile(PyFileBase):
    name: str
    content: str
    parent : Optional['Directory'] = None
    collector_tool: Optional[PyFileCollectorTool] = None
    description: Optional[PyFileDescription] = None

    def __repr__(self):
        return f"PyFile(name={self.name}"
    
    def get_file_path(self):
        return os.path.join(self.parent.get_file_path(), self.name)
    
    def get_tool(self):
        if self.collector_tool is None:
            self.collector_tool = PyFileCollectorTool(file=self)
        return self.collector_tool
    
    def get_description(self):
        if self.description is None:
            python_descriptor = PyFileDescriptor()
            description = python_descriptor(self.name, self.content)
            self.description = PyFileDescription(name=self.name,
                                                 path=self.get_file_path(),
                                                description=description.get("long_description"))
        return self.description

class Directory(DirBase):
    name: str
    children: List['Directory'] = []
    files: List[File] = []
    parent: Optional['Directory'] = None
    collector_tool: Optional[DirCollectorTool] = None
    description: Optional[DirDescription] = None
    collector: Optional[AgentExecutor] = None

    def __repr__(self):
        return f"Directory(name={self.name})"
    
    def get_file_path(self):
        if self.parent is None:
            return self.name
        return os.path.join(self.parent.get_file_path(), self.name)
    
    def get_tool(self):
        if self.collector_tool is None:
            self.collector_tool = DirCollectorTool(directory=self)
        return self.collector_tool
    
    def get_collector(self):
        if self.collector is None:
            file_tools = [f.get_tool() for f in self.files]
            dir_tools = [d.get_tool() for d in self.children]
            self.collector = mk_collector_agent(tools=file_tools + dir_tools, directory=self)
        return self.collector

    def get_description(self):
        if self.description is None:
            descriptor = DirDescriptor()
            children_descriptions = [d.get_description() for d in self.children]
            files_descriptions = [f.get_description() for f in self.files]
            directory_structure = self.get_structure()
            long_description, short_description = descriptor(children_descriptions, files_descriptions, directory_structure)
            self.description = DirDescription(name=self.name, 
                                              path=self.get_file_path(),
                                              description=short_description.get("short_description"),
                                              long_description=long_description.get("long_description"),
                                              directory_structure=directory_structure)
        return self.description
    

    def add_file(self, file_name, file_content):
        if file_name.endswith('.py'):
            self.files.append(PyFile(name=file_name, content=file_content, parent=self))
        else:
            self.files.append(File(name=file_name, content=file_content, parent=self))

    def add_directory(self, directory_name):
        new_directory = Directory(name=directory_name, parent=self)
        self.children.append(new_directory)
        return new_directory

    def remove_file(self, file_name):
        self.files = [file for file in self.files if file.name != file_name]

    def find_directory(self, path):
        if path == self.name:
            return self
        for child in self.children:
            result = child.find_directory(path)
            if result:
                return result
        return None

    def get_structure(self, indent=0):
        output = []
        output.append(' ' * indent + self.name + '/')
        for file in self.files:
            output.append(' ' * (indent + 4) + repr(file))
        for child in self.children:
            output.append(child.get_structure(indent + 4))
        return '\n'.join(output)

class Repo(Directory):
    architect : Optional[AgentExecutor] = None
    def __init__(self, root_path: Optional[str] = None, skip_hidden: bool = True):
        super().__init__(name=os.path.basename(root_path) if root_path else 'root')
        if root_path:
            self.load_structure(root_path, skip_hidden)

    def load_structure(self, root_path, skip_hidden):
        allowed_extensions = ('.py', '.txt')  # Define allowed file extensions
        if not os.path.isdir(root_path):
            return None
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
            current_dir = self.find_directory(os.path.basename(dirpath) or dirpath)
            if current_dir is None:
                continue
            if skip_hidden:
                dirnames[:] = [d for d in dirnames if not d.startswith('.')]
                filenames = [f for f in filenames if not f.startswith('.')]
            for dirname in dirnames:
                current_dir.add_directory(dirname)
            for filename in filenames:
                if not filename.endswith(allowed_extensions):
                    continue
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'r') as file:
                    file_content = file.read()
                current_dir.add_file(file_name=filename, file_content=file_content)

    def init_architect(self):
        _ = self.get_description()
        _ = self.get_collector()
        self.architect = mk_architect_agent(repo=self)

    def query(self, information_request):
        if self.architect is None:
            self.init_architect()
        return self.architect.invoke({"input": information_request})

    def save_to_file(self, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load_from_file(file_path):
        with open(file_path, 'rb') as f:
            return pickle.load(f)