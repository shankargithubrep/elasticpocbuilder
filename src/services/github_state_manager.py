"""
GitHub State Manager for Demo Persistence
Allows saving and loading demo state to/from GitHub
"""

import json
import base64
import logging
from typing import Optional, Dict, List
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class GitHubStateManager:
    """Manages demo state persistence using GitHub as storage"""

    def __init__(self, token: str, repo: str, branch: str = "main"):
        """
        Initialize GitHub state manager

        Args:
            token: GitHub personal access token
            repo: Repository in format "owner/repo"
            branch: Branch to use for storage
        """
        self.token = token
        self.repo = repo
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def save_file(self, file_path: str, content: str, message: str = None) -> bool:
        """
        Save a file to GitHub

        Args:
            file_path: Path in the repository
            content: File content as string
            message: Commit message

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if file exists to get SHA
            sha = None
            existing_file_url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(existing_file_url, headers=self.headers)

            if response.status_code == 200:
                sha = response.json()["sha"]

            # Prepare the request
            content_base64 = base64.b64encode(content.encode()).decode()

            data = {
                "message": message or f"Update {file_path}",
                "content": content_base64,
                "branch": self.branch
            }

            if sha:
                data["sha"] = sha

            # Create or update file
            response = requests.put(existing_file_url, headers=self.headers, json=data)

            if response.status_code in [200, 201]:
                logger.info(f"Successfully saved {file_path} to GitHub")
                return True
            else:
                logger.error(f"Failed to save {file_path}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error saving file to GitHub: {e}")
            return False

    def load_file(self, file_path: str) -> Optional[str]:
        """
        Load a file from GitHub

        Args:
            file_path: Path in the repository

        Returns:
            File content as string, or None if not found
        """
        try:
            url = f"{self.base_url}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                content_base64 = response.json()["content"]
                content = base64.b64decode(content_base64).decode()
                logger.info(f"Successfully loaded {file_path} from GitHub")
                return content
            else:
                logger.warning(f"File not found: {file_path}")
                return None

        except Exception as e:
            logger.error(f"Error loading file from GitHub: {e}")
            return None

    def list_demos(self) -> List[str]:
        """
        List all available demos

        Returns:
            List of demo IDs
        """
        try:
            url = f"{self.base_url}/contents/demos"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                demos = []
                for item in response.json():
                    if item["type"] == "dir":
                        demos.append(item["name"])
                return demos
            else:
                logger.warning("No demos found")
                return []

        except Exception as e:
            logger.error(f"Error listing demos: {e}")
            return []

    def save_demo_state(self, demo_id: str, state: Dict) -> bool:
        """
        Save complete demo state

        Args:
            demo_id: Unique demo identifier
            state: Complete state dictionary

        Returns:
            True if successful
        """
        try:
            # Add metadata
            state["updated_at"] = datetime.now().isoformat()
            state["demo_id"] = demo_id

            # Save main state file
            state_path = f"demos/{demo_id}/state.json"
            state_content = json.dumps(state, indent=2)

            if not self.save_file(state_path, state_content,
                                f"Update demo state for {demo_id}"):
                return False

            # Save individual artifacts if they exist
            if "datasets" in state:
                for name, content in state["datasets"].items():
                    dataset_path = f"demos/{demo_id}/data/{name}.csv"
                    self.save_file(dataset_path, content,
                                 f"Save dataset {name} for {demo_id}")

            if "queries" in state:
                queries_path = f"demos/{demo_id}/queries.json"
                queries_content = json.dumps(state["queries"], indent=2)
                self.save_file(queries_path, queries_content,
                             f"Save queries for {demo_id}")

            if "demo_guide" in state:
                guide_path = f"demos/{demo_id}/demo_guide.md"
                self.save_file(guide_path, state["demo_guide"],
                             f"Save demo guide for {demo_id}")

            logger.info(f"Successfully saved complete state for demo {demo_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving demo state: {e}")
            return False

    def load_demo_state(self, demo_id: str) -> Optional[Dict]:
        """
        Load complete demo state

        Args:
            demo_id: Unique demo identifier

        Returns:
            State dictionary or None if not found
        """
        try:
            # Load main state file
            state_path = f"demos/{demo_id}/state.json"
            state_content = self.load_file(state_path)

            if not state_content:
                return None

            state = json.loads(state_content)

            # Load additional artifacts
            queries_path = f"demos/{demo_id}/queries.json"
            queries_content = self.load_file(queries_path)
            if queries_content:
                state["queries"] = json.loads(queries_content)

            guide_path = f"demos/{demo_id}/demo_guide.md"
            guide_content = self.load_file(guide_path)
            if guide_content:
                state["demo_guide"] = guide_content

            logger.info(f"Successfully loaded state for demo {demo_id}")
            return state

        except Exception as e:
            logger.error(f"Error loading demo state: {e}")
            return None

    def delete_demo(self, demo_id: str) -> bool:
        """
        Delete a demo and all its artifacts

        Args:
            demo_id: Unique demo identifier

        Returns:
            True if successful
        """
        try:
            # Get all files in demo directory
            url = f"{self.base_url}/contents/demos/{demo_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                logger.warning(f"Demo not found: {demo_id}")
                return False

            # Delete all files recursively
            for item in response.json():
                self._delete_item(item)

            logger.info(f"Successfully deleted demo {demo_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting demo: {e}")
            return False

    def _delete_item(self, item: Dict):
        """Helper to delete a file or directory"""
        if item["type"] == "file":
            url = f"{self.base_url}/contents/{item['path']}"
            data = {
                "message": f"Delete {item['path']}",
                "sha": item["sha"],
                "branch": self.branch
            }
            requests.delete(url, headers=self.headers, json=data)
        elif item["type"] == "dir":
            # Recursively delete directory contents
            url = f"{self.base_url}/contents/{item['path']}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                for sub_item in response.json():
                    self._delete_item(sub_item)

    def create_demo_index(self) -> bool:
        """
        Create or update the demo index file

        Returns:
            True if successful
        """
        try:
            demos = self.list_demos()
            index = {
                "demos": [],
                "updated_at": datetime.now().isoformat()
            }

            for demo_id in demos:
                state = self.load_demo_state(demo_id)
                if state:
                    index["demos"].append({
                        "demo_id": demo_id,
                        "customer": state.get("config", {}).get("customer", "Unknown"),
                        "created_at": state.get("created_at"),
                        "updated_at": state.get("updated_at"),
                        "status": state.get("status", "unknown")
                    })

            index_content = json.dumps(index, indent=2)
            return self.save_file("demos/index.json", index_content,
                                "Update demo index")

        except Exception as e:
            logger.error(f"Error creating demo index: {e}")
            return False