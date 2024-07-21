import os
import json
import toml
from .graph_builder import GraphBuilder
from .logger import logger

class DependencyIndexer:
    def __init__(self, repo_path: str, graph_builder: GraphBuilder):
        self.repo_path = repo_path
        self.graph_builder = graph_builder
        self.index_dependencies = os.getenv('INDEX_DEPENDENCIES', 'True').lower() == 'true'
        self.dependency_depth = int(os.getenv('INDEX_DEPENDENCY_DEPTH', '1'))

    def index_python_dependencies(self):
        if not self.index_dependencies:
            logger.info("Skipping Python dependency indexing as INDEX_DEPENDENCIES is set to False")
            return

        poetry_lock_path = os.path.join(self.repo_path, 'poetry.lock')
        if os.path.exists(poetry_lock_path):
            with open(poetry_lock_path, 'r') as f:
                lock_data = toml.load(f)
            
            packages = lock_data.get('package', [])
            for package in packages:
                name = package.get('name')
                version = package.get('version')
                if name and version:
                    self.graph_builder.add_dependency('python', f"{name}@{version}", depth=0)
                    
                    if self.dependency_depth > 0:
                        dependencies = package.get('dependencies', {})
                        for dep, constraint in dependencies.items():
                            self.graph_builder.add_dependency('python', f"{dep}@{constraint}", depth=1)
                            self.graph_builder.add_dependency_relation(f"{name}@{version}", f"{dep}@{constraint}")
        else:
            logger.warning(f"poetry.lock not found in {self.repo_path}")

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
        self.index_python_dependencies()
        self.index_javascript_dependencies()

# Add more methods as needed for indexing dependencies
