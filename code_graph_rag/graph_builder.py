from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from .code_context import get_code_context

load_dotenv()

class GraphBuilder:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_file_to_graph(self, file_path: str):
        with self.driver.session() as session:
            session.write_transaction(self._create_file_node, file_path)

    def add_method_to_graph(self, file_path: str, method_name: str, start_line: int, end_line: int):
        context = get_code_context(file_path, start_line)
        with self.driver.session() as session:
            session.write_transaction(self._create_method_node, file_path, method_name, start_line, end_line, context)

    @staticmethod
    def _create_file_node(tx, file_path):
        query = (
            "MERGE (f:File {path: $file_path}) "
            "ON CREATE SET f.created = datetime() "
            "ON MATCH SET f.last_updated = datetime()"
        )
        tx.run(query, file_path=file_path)

    @staticmethod
    def _create_method_node(tx, file_path, method_name, start_line, end_line, context):
        query = (
            "MATCH (f:File {path: $file_path}) "
            "MERGE (m:Method {name: $method_name, file_path: $file_path}) "
            "ON CREATE SET m.created = datetime(), "
            "m.start_line = $start_line, m.end_line = $end_line, m.context = $context "
            "ON MATCH SET m.last_updated = datetime(), "
            "m.start_line = $start_line, m.end_line = $end_line, m.context = $context "
            "MERGE (f)-[:CONTAINS]->(m)"
        )
        tx.run(query, file_path=file_path, method_name=method_name, start_line=start_line, end_line=end_line, context=context)

# Add more methods as needed for building and updating the graph