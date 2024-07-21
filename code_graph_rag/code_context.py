# src/code_graph_rag/code_context.py

from grep_ast import TreeContext, filename_to_lang

def get_file_context(file_path: str) -> str:
    """
    Get the context of a specific file using grep-ast.
    
    :param file_path: Path to the code file
    :return: A string containing the code context
    """
    with open(file_path, 'r') as file:
        code = file.read()
    
    lang = filename_to_lang(file_path)
    if not lang:
        return "Unable to determine language for file"
    
    context = TreeContext(file_path, code)
    return context.format()

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