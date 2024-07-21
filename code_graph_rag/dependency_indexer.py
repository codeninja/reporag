import os
import json
import subprocess
from .graph_builder import GraphBuilder

class DependencyIndexer:
    def __init__(self, repo_path: str, graph_builder: GraphBuilder):
        self.repo_path = repo_path
        self.graph_builder = graph_builder

    def index_all_files(self):
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.index_python_dependencies(file_path)
                elif file == '.json':
                    file_path = os.path.join(root, file)
                    self.index_javascript_dependencies(file_path)

    def index_python_dependencies(self):
        requirements_path = os.path.join(self.repo_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            with open(requirements_path, 'r') as f:
                dependencies = f.readlines()
            for dep in dependencies:
                dep = dep.strip()
                if dep and not dep.startswith('#'):
                    self.graph_builder.add_dependency('python', dep)

    def index_javascript_dependencies(self):
        package_json_path = os.path.join(self.repo_path, 'package.json')
        if os.path.exists(package_json_path):
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            for dep, version in {**dependencies, **dev_dependencies}.items():
                self.graph_builder.add_dependency('javascript', f"{dep}@{version}")

    def index_all_dependencies(self):
        self.index_python_dependencies()
        self.index_javascript_dependencies()

# Add more methods as needed for indexing dependencies