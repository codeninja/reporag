from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import ast
from .code_context import get_code_context
from .logger import logger

load_dotenv()

class GraphBuilder:

    ast_node_map = {
        'Module': "Module",
        'FunctionDef': "FunctionDef",
        'AsyncFunctionDef': "AsyncFunctionDef",
        'Lambda': "Lambda",
        'ClassDef': "ClassDef",
        'Import': "Import",
        'ImportFrom': "ImportFrom",
        'Assign': "Assign",
        'Raise': "Raise",
        'Try': "Try",
        'Import': "Import",
        'Global': "Global",
        'Return': "Return",
        'Attribute': "Attribute",
    }



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

    def convertAstToGraph(self, ast_tree, filename):
        logger.info(f"Converting AST to graph")
        with self.driver.session() as session:
            session.write_transaction(self._convert_ast_to_graph, ast_tree, filename)

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
    def _convert_ast_to_graph(tx, ast_tree, filename):
        """
        Convert the AST to a graph representation in Neo4j.
        """
        def create_node(node_type, name):
            query = (
                "MERGE (n:ASTNode {type: $type, name: $name}) "
                "RETURN n.name as node_id"
            )
            result = tx.run(query, type=node_type, name=name)
            return result.single()["node_id"]

        def create_relationship(source_name, target_name, rel_type):
            query = (
                "MATCH (s:ASTNode {name: $source_name}), (t:ASTNode {name: $target_name}) "
                "MERGE (s)-[r:" + rel_type + "]->(t)"
            )
            tx.run(query, source_name=source_name, target_name=target_name)

        def process_module(node):
            module_name = node.__class__.__name__
            create_node("Module", module_name)
            create_relationship(filename, module_name, "CONTAINS")

        def process_class(node, parent_name):
            class_name = node.__class__.__name__
            create_node("ClassDef", class_name)
            create_relationship(parent_name, class_name, "CONTAINS")
            # map all class variables
            for child in ast.iter_child_nodes(node):
                pass

            # map all functions
            for child in ast.iter_child_nodes(node):
                process_function(child, class_name)
            


        def process_function(node, parent_name):
            function_name = node.__class__.__name__
            create_node("FunctionDef", function_name)
            create_relationship(parent_name, function_name, "CONTAINS")

        def process_attribute(node, parent_name):
            attribute_name = node.__class__.__name__
            create_node("Attribute", attribute_name)
            create_relationship(parent_name, attribute_name, "HAS_ATTRIBUTE")
            create_relationship(attribute_name, parent_name, "BELONGS_TO")

        def process_annotation(node, parent_name):
            annotation_name = node.__class__.__name__
            create_node("Annotation", annotation_name)
            create_relationship(parent_name, annotation_name, "HAS_ANNOTATION")
            create_relationship(annotation_name, parent_name, "BELONGS_TO")
            

        

        def process_node(node, parent_name=None):
            node_name = node.__class__.__name__
            node_type = type(node).__name__
            
            # return if node is not in ast node map
            if node_type not in GraphBuilder.ast_node_map:
                logger.debug(f"Skipping node: {node_type} - {node_name}")
                return
            else:
                logger.info(f"Processing node: {node_type} - {node_name}")
                logger.info(f"Parent: {parent_name}")
                logger.info(f"Node: {ast.dump(node)}")


            if parent_name is not None:
                create_node(node_type, node_name)
                create_relationship(parent_name, node_name, "CONTAINS")
                create_relationship(filename, node_name, "CONTAINS")

            for child in ast.iter_child_nodes(node):
                process_node(child, node_name)

            # # Handle specific node types
            # if isinstance(node, ast.FunctionDef):
            #     for arg in node.args.args:
            #         arg_name = arg.arg
            #         create_node("Parameter", arg_name)
            #         create_relationship(node_name, arg_name, "PARAMETER")
            #         create_relationship(arg_name, node_name, "BELONGS_TO")

            # elif isinstance(node, ast.Import):
            #     for alias in node.names:
            #         import_name =   alias.name
            #         create_node("Import", import_name)
            #         create_relationship(node_name, import_name, "IMPORTS")

            # elif isinstance(node, ast.ImportFrom):
            #     module = node.module
            #     for alias in node.names:
            #         import_name = f"{module}.{alias.name}"
            #         create_node("ImportFrom", import_name)
            #         create_relationship(node_name, parent_name, "IMPORTS_FROM")
            #         create_relationship(node_name, import_name, "IMPORTS_FROM")

            # elif isinstance(node, ast.Attribute):
            #     attr_name = node.attr
            #     # print(f"Attribute: {attr_name}")
            #     create_node("Attribute", attr_name)
            #     create_relationship(node_name, attr_name, "HAS_ATTRIBUTE")
            #     create_relationship(attr_name, node_name, "BELONGS_TO")

        
        logger.info(f"** Processsing AST Tree for ${filename}")
        # class names in ast module
        process_node(ast_tree)
