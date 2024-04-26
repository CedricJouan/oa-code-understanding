from pydantic import BaseModel
from typing import Optional

class DirDescription(BaseModel):
    name : str
    path : str
    description : str
    long_description : str
    directory_structure : str

class FileDescription(BaseModel):
    name : str
    path : str
    long_description : str
    description : str

class PyFileDescription(BaseModel):
    name : str
    path : str
    long_description : str
    description : str

class FileBase(BaseModel):
    name : str
    content : str
    description : FileDescription
    class Config:
        arbitrary_types_allowed = True

class PyFileBase(BaseModel):
    name : str
    content : str
    description : PyFileDescription
    class Config:
        arbitrary_types_allowed = True

class DirBase(BaseModel):
    name : str
    description : DirDescription
    class Config:
        arbitrary_types_allowed = True