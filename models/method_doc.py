
# pydantic model to represent all the context of a method
from typing import List


class MethodDoc(BaseModel):
    name: str
    docstring: str
    code: str
    deps: List[str] = []
    context: str = ""
    path: str = ""
    
