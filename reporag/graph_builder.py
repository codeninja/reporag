
import neo4j
from neo4j import GraphDatabase, Transaction
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


    file_node = None

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

    def convertAstToGraph(self, ast_tree, filepath):
        logger.info(f"Converting AST to graph")
        with self.driver.session() as session:
            session.write_transaction(self._convert_ast_to_graph, ast_tree, filepath)

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
    def _convert_ast_to_graph(tx:Transaction, ast_tree, filepath):
        """
        Convert the AST to a graph representation in Neo4j.
        """


        def create_node(node_type, name, metadata: dict[str] = {}):
            newMetadata = f"""{{type: '{node_type}', {
                ', '.join([f"{k}: '{v}'" for k, v in metadata.items()])
            } name: '{name}', filepath: '{filepath}'}}"""

            query = f"""MERGE (n:{node_type} {newMetadata}) 
                ON CREATE SET n.created = datetime() 
                ON MATCH SET n.last_updated = datetime() 
                RETURN n as Node"""
            
            result = tx.run(query, type=node_type, name=name, filepath=filepath)
            node = result.single()['Node']
            return node
    
        def create_relationship(sourceNode: neo4j , targetNode, rel_type):
            print("SOURCE NODE", sourceNode)
            print("TARGET NODE", targetNode)

            if not sourceNode or not targetNode:
                logger.error(f"Missing nodes: Source: {sourceNode}, Target: {targetNode}")
                return None
            
            source_name = sourceNode._properties['name']
            target_name = targetNode._properties['name']
            source_labels = list(sourceNode.labels)
            target_labels = list(targetNode.labels)
            target_filepath = targetNode._properties['filepath']
            

            if not source_labels or not target_labels:
                logger.error(f"Missing labels: Source: {source_labels}, Target: {target_labels}")
                return None

            source_label = source_labels[0]
            target_label = target_labels[0]

            # TODO: Clean this up and pass results through transaction engine
            query = (
                f"MATCH (s:{source_label} {{name: '{source_name}'}}), (t:{target_label} {{name: '{target_name}'}}) "
                f"MERGE (s)-[r:{rel_type}]->(t) "
                "RETURN r"
            )
            result = tx.run(query, source_name=source_name, target_name=target_name, target_filepath=target_filepath, filepath=filepath)
            logger.info(f"RELATIONSHIP QUERY: {query}, RESULT: {result.data()} {result.values()}")
            logger.info(f"Relationship labels: {source_label} -> {target_label} ({rel_type})")
            logger.info(f"RELATIONSHIP args: sn:{source_name}, tn:{target_name}, tf:{target_filepath}, f:{filepath}, rt:{rel_type}")
            if result:
                logger.info(f"Relationship created: {source_label} -> {target_label} ({rel_type})")
            else:
                logger.error(f"Failed to create relationship: {source_label} -> {target_label} ({rel_type})")
            
            return result

        def getfilepathFromPath(filepath: str):
            return filepath.split("/")[-1]

        def process_file(filepath: str):
            file_name = getfilepathFromPath(filepath)
            file_node = create_node("File", file_name)
            logger.info(f"File node created: {file_name}: {file_node}")
            return file_node
        

        def process_module(node: ast.Module, parent_node):
            file_name = getfilepathFromPath(filepath)
            module_node = create_node("Module", file_name)
            
            logger.info(f"Module node created: {module_node}")
            if parent_node:
                create_relationship(parent_node, module_node, "CONTAINS")
            
            if GraphBuilder.file_node:
                create_relationship(GraphBuilder.file_node, module_node, "CONTAINS")

            return module_node


        def process_import(node: ast.Import, parent_node):
            print("IMPORT ast", ast.dump(node))
            import_name = node.names[0].name
            print('import name', import_name)
            import_node = create_node("Import", import_name)
            print('import node', import_node)
            create_relationship(import_node, parent_node, "IMPORTEDBY")
            create_relationship(parent_node, import_node, "IMPORTS")

        def process_class(node: ast.ClassDef, parent_node):
            class_name = node.__class__.__name__
            create_node("process_class", class_name)
            create_relationship(parent_node, class_name, "CONTAINS") 
            create_relationship(class_name, parent_node, "BELONGS_TO")         

        def process_function(node: ast.FunctionDef, parent_node):
            function_name = node.__class__.__name__
            function_node = create_node("process_function", function_name)
            create_relationship(parent_node, function_node, "CONTAINS")
            create_relationship(function_node, parent_node, "BELONGS_TO")
            create_relationship(GraphBuilder.file_node, function_node, "CONTAINS")

        def process_attribute(node: ast.Attribute, parent_node):
            attribute_name = node.__class__.__name__
            create_node("process_attribute", attribute_name)
            create_relationship(parent_node, attribute_name, "HAS_ATTRIBUTE")
            create_relationship(attribute_name, parent_node, "BELONGS_TO")

        def process_annotation(node: ast.AnnAssign, parent_node):
            annotation_name = node.__class__.__name__
            create_node("process_annotation", annotation_name)
            create_relationship(parent_node, annotation_name, "HAS_ANNOTATION")
            create_relationship(annotation_name, parent_node, "BELONGS_TO")
            
        def process_child(node, parent_node=None):
            node_name = node.__class__.__name__
            node_type = type(node).__name__
            self_node = None
            file_node = GraphBuilder.file_node

            # return if node is not in ast node map
            if node_type not in GraphBuilder.ast_node_map:
                logger.info(f"Node type not found: {node_type}")
                return

            logger.info(f"Processing node: {node_name} - {node_type}")
            # handle node type
            if node_type == "Module":
                self_node = process_module(node, parent_node)                

            elif node_type == "Import":
                self_node = process_import(node, parent_node)                

            # elif node_type == "ClassDef":
            #     self_node = process_class(node, parent_node)

            # elif node_type == "FunctionDef":
            #     self_node = process_function(node, parent_node)

            # elif node_type == "Attribute":
            #     self_node = process_attribute(node, parent_node)

            # elif node_type == "AnnAssign":
            #     self_node = process_annotation(node, parent_node)

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


            # if parent_node is not None:
            #     logger.info(f"Creating relationship: {parent_node} -> {self_node} (CONTAINS)")
            #     create_relationship(parent_node, self_node, "CONTAINS")
                
            #     logger.info(f"Creating relationship: {self_node} -> {parent_node} (BELONGS_TO)")
            #     create_relationship(GraphBuilder.file_node, self_node, "CONTAINS")  


            for child in ast.iter_child_nodes(node):
                print('---')
                print("CHILD", child, type(child).__name__)
                print('node', node)
                print('file_node', file_node)
                print('ast_node_map', GraphBuilder.ast_node_map.keys())
                child_type = child.__class__.__name__
                # if the child exists in the ast node map
                if child_type in GraphBuilder.ast_node_map.keys():
                    print('PROCESSING CHILD', child)
                    process_child(child, self_node)

        
        logger.info(f"** Parsing AST Tree for ${filepath}")
        # class names in ast module
        GraphBuilder.file_node = process_file(filepath)
        process_child(ast_tree, GraphBuilder.file_node)
