import os
import shutil
from git import Repo, GitCommandError
import logging

logger = logging.getLogger(__name__)


class GitService:
    """Service for managing Git repository operations."""

    def __init__(self, repo_url, clone_path, branch='main', username=None, token=None):
        self.repo_url = repo_url
        self.clone_path = clone_path
        self.branch = branch
        self.username = username
        self.token = token
        self.repo = None

        # Build authenticated URL if credentials are provided
        self.auth_repo_url = self._build_auth_url() if username and token else repo_url

    def _build_auth_url(self):
        """Build authenticated Git URL with username and token."""
        if not self.username or not self.token:
            return self.repo_url

        # Handle different URL formats
        if self.repo_url.startswith('https://'):
            # Extract the part after https://
            url_part = self.repo_url.replace('https://', '')
            # Build authenticated URL: https://username:token@github.com/...
            auth_url = f'https://{self.username}:{self.token}@{url_part}'
            logger.info(f"Using authenticated URL for repository access")
            return auth_url
        elif self.repo_url.startswith('http://'):
            # Extract the part after http://
            url_part = self.repo_url.replace('http://', '')
            # Build authenticated URL: http://username:token@github.com/...
            auth_url = f'http://{self.username}:{self.token}@{url_part}'
            logger.info(f"Using authenticated URL for repository access")
            return auth_url
        else:
            # For SSH URLs or other formats, return as-is
            logger.warning(f"Cannot add authentication to URL format: {self.repo_url}")
            return self.repo_url

    def clone_or_update(self):
        """Clone the repository if it doesn't exist, otherwise pull latest changes."""
        try:
            if os.path.exists(self.clone_path):
                logger.info(f"Repository exists at {self.clone_path}, pulling latest changes...")
                self.repo = Repo(self.clone_path)

                # Update remote URL if using authentication
                if self.auth_repo_url != self.repo_url:
                    origin = self.repo.remotes.origin
                    origin.set_url(self.auth_repo_url)

                origin = self.repo.remotes.origin
                origin.pull(self.branch)
                logger.info(f"Successfully pulled latest changes from {self.branch}")
            else:
                logger.info(f"Cloning repository from {self.repo_url}...")
                os.makedirs(os.path.dirname(self.clone_path), exist_ok=True)
                self.repo = Repo.clone_from(self.auth_repo_url, self.clone_path, branch=self.branch)
                logger.info(f"Successfully cloned repository to {self.clone_path}")

            return True
        except GitCommandError as e:
            logger.error(f"Git command error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error cloning/updating repository: {e}")
            return False

    def get_current_commit_hash(self):
        """Get the current commit hash."""
        if self.repo:
            return self.repo.head.commit.hexsha
        return None

    def get_current_branch(self):
        """Get the current branch name."""
        if self.repo:
            return self.repo.active_branch.name
        return None

    def checkout_branch(self, branch):
        """Checkout a specific branch."""
        try:
            if self.repo:
                self.repo.git.checkout(branch)
                logger.info(f"Checked out branch: {branch}")
                return True
        except GitCommandError as e:
            logger.error(f"Error checking out branch {branch}: {e}")
        return False

    def get_file_content(self, file_path):
        """Get content of a specific file."""
        try:
            full_path = os.path.join(self.clone_path, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
        return None

    def find_test_files(self, pattern='test_*.py'):
        """Find all test files in the repository."""
        test_files = []
        try:
            for root, dirs, files in os.walk(self.clone_path):
                # Skip .git directory
                if '.git' in root:
                    continue

                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.clone_path)
                        test_files.append(rel_path)

            logger.info(f"Found {len(test_files)} test files")
        except Exception as e:
            logger.error(f"Error finding test files: {e}")

        return test_files

    def cleanup(self):
        """Remove the cloned repository."""
        try:
            if os.path.exists(self.clone_path):
                shutil.rmtree(self.clone_path)
                logger.info(f"Cleaned up repository at {self.clone_path}")
                return True
        except Exception as e:
            logger.error(f"Error cleaning up repository: {e}")
        return False

