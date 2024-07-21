from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from .code_context import get_code_context
from .logger import logger

load_dotenv()

class GraphBuilder:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("GraphBuilder initialized")

    def close(self):
        self.driver.close()
        logger.info("GraphBuilder connection closed")

    def add_file_to_graph(self, file_path: str):
        logger.info(f"Adding file to graph: {file_path}")
        with self.driver.session() as session:
            session.write_transaction(self._create_file_node, file_path)
        logger.info(f"File added to graph: {file_path}")

    def add_method_to_graph(self, file_path: str, method_name: str, start_line: int, end_line: int):
        logger.info(f"Adding method to graph: {method_name} in {file_path}")
        context = get_code_context(file_path, start_line)
        with self.driver.session() as session:
            session.write_transaction(self._create_method_node, file_path, method_name, start_line, end_line, context)
        logger.info(f"Method added to graph: {method_name} in {file_path}")

    def add_dependency(self, language: str, dependency: str, depth: int):
        logger.info(f"Adding dependency to graph: {dependency} ({language})")
        with self.driver.session() as session:
            session.write_transaction(self._create_dependency_node, language, dependency, depth)
        logger.info(f"Dependency added to graph: {dependency} ({language})")

    def add_dependency_relation(self, parent: str, child: str):
        logger.info(f"Adding dependency relation: {parent} -> {child}")
        with self.driver.session() as session:
            session.write_transaction(self._create_dependency_relation, parent, child)
        logger.info(f"Dependency relation added: {parent} -> {child}")

    @staticmethod
    def _create_file_node(tx, file_path):
        query = (
            "MERGE (f:File {path: $file_path}) "
            "ON CREATE SET f.created = datetime() "
            "ON MATCH SET f.last_updated = datetime()"
        )
        tx.run(query, file_path=file_path)
        logger.debug(f"File node created or updated: {file_path}")

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
        logger.debug(f"Method node created or updated: {method_name} in {file_path}")

    @staticmethod
    def _create_dependency_node(tx, language, dependency, depth):
        query = (
            "MERGE (d:Dependency {name: $dependency, language: $language}) "
            "ON CREATE SET d.created = datetime(), d.depth = $depth "
            "ON MATCH SET d.last_updated = datetime(), d.depth = $depth"
        )
        tx.run(query, dependency=dependency, language=language, depth=depth)
        logger.debug(f"Dependency node created or updated: {dependency} ({language})")

    @staticmethod
    def _create_dependency_relation(tx, parent, child):
        query = (
            "MATCH (p:Dependency {name: $parent}), (c:Dependency {name: $child}) "
            "MERGE (p)-[:DEPENDS_ON]->(c)"
        )
        tx.run(query, parent=parent, child=child)
        logger.debug(f"Dependency relation created: {parent} -> {child}")

# Add more methods as needed for building and updating the graph
