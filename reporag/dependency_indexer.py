import os
import json
import toml
import fnmatch

from reporag.vector_store import VectorStore
from .code_context import get_file_context
from .graph_builder import GraphBuilder
from .logger import logger

class DependencyIndexer:
    def __init__(self, repo_path: str, graph_builder: GraphBuilder, vector_store: VectorStore):
        self.repo_path = repo_path
        self.graph_builder = graph_builder
        self.index_dependencies = os.getenv('INDEX_DEPENDENCIES').lower() == 'true'
        self.dependency_depth = int(os.getenv('INDEX_DEPENDENCY_DEPTH'))
        self.index_pattern = os.getenv('INDEX_PATTERN')
        self.ignore_pattern = os.getenv('IGNORE_PATTERN')
        self.vector_store = vector_store

    def index_all_files(self):
        logger.info('-index_all_files-')

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            for file in files:
                if self._should_index(file):
                    logger.info(f"-- Indexing file: {file}")
                    file_path = os.path.join(root, file)
                    context = get_file_context(file_path)
                    # self.graph_builder.add_file_to_graph(file_path)
                    self.graph_builder.convertAstToGraph(context.ast, file_path)
                    logger.info(f"File added to graph: {file_path}")

        logger.info('-/index_all_files-')
                

    def _should_index(self, file_name):
        return fnmatch.fnmatch(file_name, self.index_pattern) and not self._should_ignore(file_name)

    def _should_ignore(self, path):
        logger.debug(f"Checking if path should be ignored: {path}")
        logger.debug(f"Ignore path: {path}")
        logger.debug(f"Ignore pattern: {self.ignore_pattern}")

        isMatch = any(fnmatch.fnmatch(path, pattern) for pattern in self.ignore_pattern.split('|'))
        logger.debug(f"Is match: {isMatch}")
        return isMatch

    def index_python_dependencies(self):
        if not self.index_dependencies:
            logger.info("Skipping Python dependency indexing as INDEX_DEPENDENCIES is set to False")
            return

        poetry_lock_path = os.path.join(self.repo_path, 'poetry.lock')
        if os.path.exists(poetry_lock_path):
            with open(poetry_lock_path, 'r') as f:
                lock_data = toml.load(f)
            
            packages = lock_data.get('package', [])
            self.process_python_dependencies(packages, 0)

        else:
            logger.warning(f"poetry.lock not found in {self.repo_path}")

    def process_python_dependencies(self, packages, current_depth):
        for package in packages:
            name = package.get('name')
            version = package.get('version')
            if name and version:
                self.graph_builder.add_dependency('python', f"{name}@{version}", depth=current_depth)
                self.graph_builder.add_dependency_relation(f"{name}@{version}", f"{dep}@{constraint}")
                
                if current_depth < self.dependency_depth:
                    dependencies = package.get('dependencies', [])
                    self.process_python_dependencies(dependencies, current_depth+1)

    def index_javascript_dependencies(self):
        if not self.index_dependencies:
            logger.info("Skipping JavaScript dependency indexing as INDEX_DEPENDENCIES is set to False")
            return

        package_lock_path = os.path.join(self.repo_path, 'package-lock.json')
        if os.path.exists(package_lock_path):
            with open(package_lock_path, 'r') as f:
                lock_data = json.load(f)
            
            dependencies = lock_data.get('dependencies', {})
            self._process_js_dependencies(dependencies, 0)
        else:
            logger.warning(f"package-lock.json not found in {self.repo_path}")

    def _process_js_dependencies(self, dependencies, current_depth):
        for name, info in dependencies.items():
            version = info.get('version')
            if version:
                self.graph_builder.add_dependency('javascript', f"{name}@{version}", depth=current_depth)
                
                if current_depth < self.dependency_depth:
                    sub_dependencies = info.get('dependencies', {})
                    for sub_name, sub_info in sub_dependencies.items():
                        sub_version = sub_info.get('version')
                        if sub_version:
                            self.graph_builder.add_dependency('javascript', f"{sub_name}@{sub_version}", depth=current_depth+1)
                            self.graph_builder.add_dependency_relation(f"{name}@{version}", f"{sub_name}@{sub_version}")

    def index_all_dependencies(self):
        if not self.index_dependencies:
            logger.info("Skipping dependency indexing as INDEX_DEPENDENCIES is set to False")
            return

        self.index_all_files()
        self.index_python_dependencies()
        self.index_javascript_dependencies()

    def index_file_dependencies(self, file_path):
        if file_path.endswith('.py'):
            self.index_python_file_dependencies(file_path)
        elif file_path.endswith('.js'):
            self.index_javascript_file_dependencies(file_path)

    def index_python_file_dependencies(self, file_path):
        # Implement logic to index Python file dependencies
        pass

    def index_javascript_file_dependencies(self, file_path):
        # Implement logic to index JavaScript file dependencies
        pass

# Add more methods as needed for indexing dependencies
