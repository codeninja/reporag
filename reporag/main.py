import os
from dotenv import load_dotenv
from reporag.repo_monitor import RepoMonitor
from reporag.graph_builder import GraphBuilder
from reporag.vector_store import VectorStore
from reporag.dependency_indexer import DependencyIndexer
from reporag.docstring_generator import DocstringGenerator
from reporag.llm_interface import LLMInterface
from reporag.logger import logger

def main():
    logger.info("Starting RepoRAG process")
    
    # Load environment variables
    load_dotenv()
    logger.info("Environment variables loaded")

    # Initialize components
    repo_path = os.getenv("REPO_PATH")
    repo_name = os.getenv("REPO_NAME")
    repo_monitor = RepoMonitor(repo_name)
    graph_builder = GraphBuilder()
    vector_store = VectorStore()
    dependency_indexer = DependencyIndexer(repo_path, graph_builder)
    docstring_generator = DocstringGenerator(os.getenv("OPENAI_API_KEY"))
    llm_interface = LLMInterface()
    logger.info("All components initialized")

    dependency_indexer.index_all_files()
    
    # dependency_indexer.index_all_dependencies()

    # # index all files in the repository
    # if repo_monitor.check_for_updates():
    #     logger.info("Updates detected in the repository. Processing changes...")
    #     changed_files = repo_monitor.get_changed_files()
    #     # Process each changed file
    #     for file_path in changed_files:
    #         logger.info(f"Processing file: {file_path}")
    #         # Update graph
    #         graph_builder.add_file_to_graph(file_path)
    #         logger.info(f"Graph updated for file: {file_path}")

    #         # Update vector store
    #         with open(file_path, 'r') as file:
    #             content = file.read()
    #             vector_store.add_code_snippet(file_path, content, {"file_path": file_path})
    #         logger.info(f"Vector store updated for file: {file_path}")

    #         # Generate docstrings if it's a Python file
    #         if file_path.endswith('.py'):
    #             docstring = docstring_generator.generate_docstring(file_path, "example_method", 1)
    #             logger.info(f"Generated docstring for {file_path}:")
    #             logger.info(docstring)

    #     # Update dependencies
    #     dependency_indexer.index_all_dependencies()
    #     logger.info("Dependencies indexed")

    #     logger.info("Finished processing changes.")

    # # /bug
    
    # Example of using the LLM interface
    logger.info("Starting LLM conversation")
    assistant = llm_interface.create_assistant("CodeExpert", "You are an expert in Python and JavaScript programming.")
    user_proxy = llm_interface.create_user_proxy("User")
    # conversation = llm_interface.run_conversation(user_proxy, assistant, "Explain the code in this project. how does it .")

    # logger.info("LLM Conversation Result:")
    # for message in conversation:
    #     logger.info(f"{message['role']}: {message['content']}")

    logger.info("RepoRAG initialization and update complete.")

if __name__ == "__main__":
    main()
