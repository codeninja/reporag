
# pydantic model to represent all the context of a method
from pydantic import BaseModel
from typing_extensions import Annotated

neo4j_tuple_instructions = """
## Neo4j Tuple representation of the method:
- Each tuple in the list represents a relationship between two nodes in the Neo4j graph database.
- Each node represents a token in the method.
- The relationship represents the type of relationship between the two nodes.
    - 'D': Dependency relationship between two tokens.
    - 'U': Usage relationship between two tokens.
    - 'C': Control relationship between two tokens.
    - 'T': Type relationship between two tokens. (Infer the type based upon the functionalty if it's not explicitly mentioned. e.g. 'x' is a string in `x = 'hello'`. Use python types like 'str', 'int', 'float', 'List[str]', etc.)
    - 'P': Parameter relationship between two tokens. (e.g. 'x' is a parameter in `def foo(x):`)
- The list of tuples can be used to create the Neo4j graph representation of the method.
- The tuple is of the form:
    (source_node, relationship, destination_node)

### Example imports:
```
from os.path import splitext
import subprocess
import json
```

### Example Neo4j Tuple representation:
```
[('from', 'D', 'os.path'), ('from', 'D', 'import'), ('from', 'U', 'splitext'), ('import', 'D', 'subprocess'), ('import', 'D', 'json')]
```

### Example Code with Dependencies: 
```
from os.path import splitext
def foo(x):
    if x != '':
        return splitext(x)
```

### Example Neo4j Tuple representation:
```
[('foo', 'D', 'os.path'), ('foo', 'D', 'splitext'), ('foo', 'C', 'x'), ('x', 'T', 'str'), ('x', 'P', 'foo'), ('x', 'U', 'splitext'), ('splitext', 'T', 'List[str]')]
```

"""
# instructions for creating the graph representation of the method
graph_instructions = f"""
## Graph representation of the method:
{neo4j_tuple_instructions}
"""

# instructions for creating the AST representation of the method
ast_instructions = """
## AST representation of the method:
- The AST representation is a string that represents the Abstract Syntax Tree of the method.
- The AST string is generated conforming to the format of the AST representation in the Python ast module.

### Example code:
```
from os.path import splitext
def foo(x):
    if x != '':
        return splitext(x)
```

### Example AST representation:
```
Module(body=[Import(names=[alias(name='splitext', asname=None)], level=0), FunctionDef(name='foo', args=arguments(posonlyargs=[], args=[arg(arg='x', annotation=None, type_comment=None)], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=[If(test=Compare(left=Name(id='x', ctx=Load()), ops=[NotEq()], comparators=[Str(s='')])), Return(value=Call(func=Name(id='splitext', ctx=Load()), args=[Name(id='x', ctx=Load())], keywords=[]))], decorator_list=[], returns=None)])
```
"""

summary_instructions = """
## Concise Method Summary:
- The summary is a concise description of the method and its use.
- It should provide a brief overview of the method's functionality and purpose and mention any important dependencies or side effects.
- The summary should be written in a clear and understandable way so that developers can quickly understand what the method does.

### Example code for src/example.py:
```
from os.path import splitext
def foo(x):
    if x != '':
        return splitext(x)
```

### Example summary:

`Method Foo: accepts a string x and returns the file extension using the splitext function from the os.path module.`

"""

depGraph_instructions = f"""
## Dependency Graph representation of the method:
{neo4j_tuple_instructions}
"""


class CodeContext(BaseModel):
    name: Annotated[str, "Name of the file, method, or class: Examples: `example.py`, `example.py:Foo:bar()`"]
    lang: Annotated[str, "Extension of the code: Examples: `py`, `js`"]
    path: Annotated[str, "Path of the file containing the code."]
    source: Annotated[str, "The source code"]
    # optional summary
    summary: Annotated[str, summary_instructions, None]
    # array of Tuples, graph representation of the method.
    graph: Annotated[list[tuple[str, str, str]], graph_instructions, None]
    depGraph: Annotated[list[tuple[str, str, str]], depGraph_instructions, None]
    # AST representation of the method.
    ast: Annotated[object, ast_instructions, None]

    