from pydantic import BaseModel
from typing import Optional

class DirDescription(BaseModel):
    name : str
    description : str
    long_description : str

class FileDescription(BaseModel):
    name : str
    description : str

class PyFileDescription(BaseModel):
    name : str
    description : str

class FileBase(BaseModel):
    name : str
    content : str

class PyFileBase(BaseModel):
    name : str
    content : str

class DirBase(BaseModel):
    name : str
