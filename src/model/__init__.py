from models import *
from agents.descriptors import FileDescriptor, PyFileDescriptor, DirDescriptor
from agents.dspy_collectors import mk_react_collector, PyFileCollectorTool, FileCollectorTool
import dspy
import os
import pickle
from typing import List, Optional


class File(FileBase):
    name: str
    content: str
    description: Optional[FileDescription] = None
    collector: Optional[dspy.Module] = None

    class Config:
        arbitrary_types_allowed = True

    def __repr__(self):
        return f"File(name={self.name})"
    
    def get_collector(self):
        if self.collector is None:
            self.collector = FileCollectorTool(file=self)
        return self.collector
    
    def get_description(self):
        if self.description is None:
            descriptor = FileDescriptor()
            description = descriptor(self.name, self.content)
            self.description = FileDescription(name=self.name, 
                                               description=description.get("long_description"))
        return self.description

class PyFile(PyFileBase):
    name: str
    content: str
    description: Optional[PyFileDescription] = None
    collector: Optional[dspy.Module] = None

    class Config:
        arbitrary_types_allowed = True

    def __repr__(self):
        return f"PyFile(name={self.name}"
    
    def get_collector(self):
        if self.collector is None:
            self.collector = PyFileCollectorTool(file=self)
        return self.collector
    
    def get_description(self):
        if self.description is None:
            python_descriptor = PyFileDescriptor()
            description = python_descriptor(self.name, self.content)
            self.description = PyFileDescription(name=self.name,
                                                description=description.get("long_description"))
        return self.description

class Directory(DirBase):
    name: str
    parent: Optional['Directory'] = None
    children: List['Directory'] = []
    files: List[File] = []
    description: Optional[DirDescription] = None
    collector: Optional[dspy.Module] = None
    
    class Config:
        arbitrary_types_allowed = True

    def get_collector(self):
        if self.collector is None:
            file_collectors = [f.get_collector() for f in self.files]
            dir_collectors = [c.get_collector() for c in self.children]
            self.collector = mk_react_collector(file_collectors, dir_collectors)
        return self.collector

    def get_description(self):
        if self.description is None:
            descriptor = DirDescriptor()
            children_descriptions = [d.get_description() for d in self.children]
            files_descriptions = [f.get_description() for f in self.files]
            directory_structure = self.get_structure()
            long_description, short_description = descriptor(children_descriptions, files_descriptions, directory_structure)
            self.description = DirDescription(name=self.name, 
                                              description=short_description.get("short_description"),
                                              long_description=long_description.get("long_description"))
        return self.description
    

    def add_file(self, file):
        self.files.append(file)

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

    def __repr__(self):
        return f"Directory(name={self.name})"

    def get_structure(self, indent=0):
        output = []
        output.append(' ' * indent + self.name + '/')
        for file in self.files:
            output.append(' ' * (indent + 4) + repr(file))
        for child in self.children:
            output.append(child.get_structure(indent + 4))
        return '\n'.join(output)

class Repo(Directory):
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
                if filename.endswith('.py'):
                    current_dir.add_file(PyFile(name=filename, content=file_content))
                elif filename.endswith('.txt'):
                    current_dir.add_file(File(name=filename, content=file_content))


    def save_to_file(self, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load_from_file(file_path):
        with open(file_path, 'rb') as f:
            return pickle.load(f)