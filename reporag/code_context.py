# src/reporag/code_context.py
from os.path import splitext
from .models.code_context import CodeContext
import ast

import subprocess
import json

def get_file_context(file_path: str) -> CodeContext:
    """ 
    - Parses the file into AST structure with the ast module 
    - then parses the AST structure into a graph tuple representation. (see neo4j_tuple_instructions)
    - then parses any dependencies in the file into a graph tuple representation. (see neo4j_tuple_instructions)
    - then 
    :param file_path: Path to the code file
    :return: A CodeContext object
    """
    with open(file_path, 'r') as file:
        code = file.read()
    
    file_name = splitext(file_path)[0]
    lang = splitext(file_path)[1][1:]
    parsedAst = ast.parse(code, type_comments=True)
    context = CodeContext(
        name=file_name,
        lang=lang,
        path=file_path,
        source=code,
        ast=parsedAst,
        graph=[],
        depGraph=[],
        summary=""
    )
    return context

def get_code_context(file_path: str, line_number: int) -> str:
    """
    Get the context of a specific line in a code file using grep-ast.
    
    :param file_path: Path to the code file
    :param line_number: The line number to get context for
    :return: A string containing the code context
    """
    with open(file_path, 'r') as file:
        code = file.read()
    
    lang = filename_to_lang(file_path)
    if not lang:
        return "Unable to determine language for file"
    
    context = TreeContext(file_path, code)
    context.add_lines_of_interest([line_number])
    return context.format()

def search_codebase(pattern: str, directory: str) -> list[dict]:
    """
    Search the codebase for a specific pattern using grep-ast.
    
    :param pattern: The regex pattern to search for
    :param directory: The root directory of the codebase
    :return: A list of dictionaries containing file paths and matching lines with context
    """
    from grep_ast import grep_ast
    results = []
    for match in grep_ast(pattern, [directory]):
        results.append({
            'file': match.filename,
            'line': match.lineno,
            'context': get_code_context(match.filename, match.lineno)
        })
    return results