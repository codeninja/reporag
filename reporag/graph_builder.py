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

    def convertAstToGraph(self, ast):
        logger.info(f"Converting AST to graph")
        with self.driver.session() as session:
            session.write_transaction(self._convert_ast_to_graph, ast)
        logger.info(f"AST converted to graph")

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

    @staticmethod
    def _convert_ast_to_graph(tx, ast):
        """
        Convert the AST to a graph representation.
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
            # iterate over ast, create nodes 

        pass
