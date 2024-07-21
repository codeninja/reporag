

# pydantic model to represent a source file, it's dependencies, and classes and methods
from pydantic import BaseModel
from typing_extensions import Annotated

from models.code_context import CodeContext

class FileContext(BaseModel):
    path: Annotated[str, "The path to the source file"]
    dependencies: Annotated[list[str], "List of dependencies of the file"]
    classes: Annotated[list[CodeContext], "List of classes in the file"]
    methods: Annotated[list[CodeContext], "List of methods in the file"]
