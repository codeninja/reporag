import os
from dotenv import load_dotenv
from code_graph_rag.repo_monitor import RepoMonitor
from code_graph_rag.graph_builder import GraphBuilder
from code_graph_rag.vector_store import VectorStore
from code_graph_rag.dependency_indexer import DependencyIndexer
from code_graph_rag.docstring_generator import DocstringGenerator
from code_graph_rag.llm_interface import LLMInterface

def main():
    # Load environment variables
    load_dotenv()

    # Initialize components
    repo_path = os.getenv("REPO_PATH")
    repo_name = os.getenv("REPO_NAME")
    repo_monitor = RepoMonitor(repo_name)
    graph_builder = GraphBuilder()
    vector_store = VectorStore()
    dependency_indexer = DependencyIndexer(repo_path, graph_builder)
    docstring_generator = DocstringGenerator(os.getenv("OPENAI_API_KEY"))
    llm_interface = LLMInterface()

    # Check for updates in the repository
    if repo_monitor.check_for_updates():
        print("Updates detected in the repository. Processing changes...")
        changed_files = repo_monitor.get_changed_files()
        # Process each changed file
        for file_path in changed_files:
            # Update graph
            graph_builder.add_file_to_graph(file_path)

            # Update vector store
            with open(file_path, 'r') as file:
                content = file.read()
                vector_store.add_code_snippet(file_path, content, {"file_path": file_path})

            # Generate docstrings if it's a Python file
            if file_path.endswith('.py'):
                docstring = docstring_generator.generate_docstring(file_path, "example_method", 1)
                print(f"Generated docstring for {file_path}:")
                print(docstring)

        # Update dependencies
        dependency_indexer.index_all_dependencies()

        print("Finished processing changes.")

    # Example of using the LLM interface
    assistant = llm_interface.create_assistant("CodeExpert", "You are an expert in Python and JavaScript programming.")
    user_proxy = llm_interface.create_user_proxy("User")
    conversation = llm_interface.run_conversation(user_proxy, assistant, "Explain the code in this project. how does it .")

    print("LLM Conversation Result:")
    for message in conversation:
        print(f"{message['role']}: {message['content']}")

    print("RepoRAG initialization and update complete.")

if __name__ == "__main__":
    main()