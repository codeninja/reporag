import os
from github import Github
from github import Auth

from dotenv import load_dotenv
from .code_context import search_codebase

load_dotenv()

class RepoMonitor:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        # using an access token
        print(os.getenv("GITHUB_TOKEN"),os.getenv("REPO_PATH"))
        self.auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
        self.github = Github(auth=self.auth)
        self.repo = self.github.get_repo(repo_path)
        self.last_commit_sha = self.repo.get_commits()[0].sha

    def check_for_updates(self):
        latest_commit = self.repo.get_commits()[0]
        if latest_commit.sha != self.last_commit_sha:
            self.last_commit_sha = latest_commit.sha
            return True
        return False

    def get_changed_files(self):
        compare = self.repo.compare(self.last_commit_sha, "HEAD")
        return [file.filename for file in compare.files]

    def search_repo(self, pattern: str):
        """
        Search the repository for a specific pattern.
        
        :param pattern: The regex pattern to search for
        :return: A list of matches with context
        """
        return search_codebase(pattern, self.repo_path)

# Add more methods as needed for monitoring and updating the repo