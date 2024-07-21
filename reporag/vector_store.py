import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

class VectorStore:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("code_snippets")

    def add_code_snippet(self, snippet_id: str, snippet_text: str, metadata: dict):
        self.collection.add(
            documents=[snippet_text],
            metadatas=[metadata],
            ids=[snippet_id]
        )

    def search_similar_snippets(self, query: str, n_results: int = 5):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def update_code_snippet(self, snippet_id: str, new_snippet_text: str, new_metadata: dict):
        self.collection.update(
            ids=[snippet_id],
            documents=[new_snippet_text],
            metadatas=[new_metadata]
        )

    def delete_code_snippet(self, snippet_id: str):
        self.collection.delete(ids=[snippet_id])

# Add more methods as needed for managing the vector store