import os
from github import Github
from github import Auth
from dotenv import load_dotenv
from .code_context import search_codebase
from .logger import logger

load_dotenv()

class RepoMonitor:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        # using an access token
        logger.info(f"Initializing RepoMonitor for {repo_path}")
        self.auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
        self.github = Github(auth=self.auth)
        self.repo = self.github.get_repo(repo_path)
        self.last_commit_sha = self.repo.get_commits()[0].sha
        logger.info("RepoMonitor initialized successfully")

    def check_for_updates(self):
        logger.info("Checking for updates in the repository")
        latest_commit = self.repo.get_commits()[0]
        if latest_commit.sha != self.last_commit_sha:
            self.last_commit_sha = latest_commit.sha
            logger.info("Updates detected in the repository")
            return True
        logger.info("No updates detected in the repository")
        return False

    def get_changed_files(self):
        logger.info("Getting list of changed files")
        compare = self.repo.compare(self.last_commit_sha, "HEAD")
        changed_files = [file.filename for file in compare.files]
        logger.info(f"Number of changed files: {len(changed_files)}")
        return changed_files

    def search_repo(self, pattern: str):
        """
        Search the repository for a specific pattern.
        
        :param pattern: The regex pattern to search for
        :return: A list of matches with context
        """
        logger.info(f"Searching repository for pattern: {pattern}")
        results = search_codebase(pattern, self.repo_path)
        logger.info(f"Number of search results: {len(results)}")
        return results

# Add more methods as needed for monitoring and updating the repo
