import os
import time
from dotenv import load_dotenv
from reporag.repo_monitor import RepoMonitor
from reporag.graph_builder import GraphBuilder
from reporag.vector_store import VectorStore
from reporag.dependency_indexer import DependencyIndexer
from reporag.docstring_generator import DocstringGenerator

def process_file(file_path, graph_builder, vector_store, docstring_generator):
    print(f"Processing file: {file_path}")

    # Update graph
    graph_builder.add_file_to_graph(file_path)

    # Update vector store
    with open(file_path, 'r') as file:
        content = file.read()
        vector_store.add_code_snippet(file_path, content, {"file_path": file_path})

    # Generate docstrings if it's a Python file
    if file_path.endswith('.py'):
        # In a real implementation, you'd want to parse the file and generate
        # docstrings for all methods/functions, not just a single example
        docstring = docstring_generator.generate_docstring(file_path, "example_method", 1)
        print(f"Generated docstring for {file_path}:")
        print(docstring)

def index_service():
    # Load environment variables
    load_dotenv()

    # Initialize components
    repo_path = os.getenv("REPO_PATH")
    repo_monitor = RepoMonitor(repo_path)
    graph_builder = GraphBuilder()
    vector_store = VectorStore()
    dependency_indexer = DependencyIndexer(repo_path, graph_builder)
    docstring_generator = DocstringGenerator(os.getenv("OPENAI_API_KEY"))

    print("Starting RepoRAG indexing service...")

    # Initial indexing of the entire repository
    print("Performing initial indexing of the repository...")
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            process_file(file_path, graph_builder, vector_store, docstring_generator)
    
    dependency_indexer.index_all_dependencies()
    print("Initial indexing complete.")

    # Continuous monitoring and indexing
    while True:
        print("Checking for updates...")
        if repo_monitor.check_for_updates():
            print("Updates detected. Processing changes...")
            changed_files = repo_monitor.get_changed_files()

            for file_path in changed_files:
                process_file(file_path, graph_builder, vector_store, docstring_generator)

            dependency_indexer.index_all_dependencies()
            print("Finished processing changes.")
        else:
            print("No updates detected.")

        # Wait for a specified interval before checking again
        time.sleep(int(os.getenv("CHECK_INTERVAL", 300)))  # Default to 5 minutes if not specified

if __name__ == "__main__":
    index_service()