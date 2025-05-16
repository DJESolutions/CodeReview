import unittest
from unittest.mock import MagicMock, patch
import base64  # Moved import to the top

from github_api import GitHubRepo


class TestGitHubRepo(unittest.TestCase):
    """Test cases for the GitHubRepo class."""

    def setUp(self):
        """Set up test fixtures."""
        self.owner = "testuser"
        self.repo_name = "test-repo"
        self.access_token = "test_token"
        self.repo = GitHubRepo(self.owner, self.repo_name, self.access_token)
        self.base_url = "https://api.github.com"
        self.default_headers = {"Authorization": f"token {self.access_token}"}

    def test_initialization(self):
        """Test GitHubRepo initialization."""
        self.assertEqual(self.repo.owner, self.owner)
        self.assertEqual(self.repo.repo_name, self.repo_name)
        self.assertEqual(self.repo.base_url, self.base_url)
        self.assertEqual(self.repo.headers, self.default_headers)

    @patch("requests.get")
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"name": "test-repo"}
        mock_get.return_value = mock_response

        endpoint = "/test-endpoint"
        result = self.repo._make_request(endpoint)

        self.assertEqual(result, {"name": "test-repo"})
        mock_get.assert_called_once_with(
            f"{self.base_url}{endpoint}",
            headers=self.default_headers,
            params=None,
            timeout=(10, 30),
        )

    @patch("requests.get")
    @patch("github_api.handle_error")
    def test_make_request_error(self, mock_handle_error, mock_get):
        """Test API request with error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        endpoint = "/test-endpoint"
        with self.assertRaises(Exception):
            self.repo._make_request(endpoint)

        mock_handle_error.assert_called_once()

    @patch("github_api.GitHubRepo._make_request")
    def test_get_repo_info(self, mock_make_request):
        """Test getting repository information."""
        mock_repo_info = {
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "description": "Test repository",
            "stargazers_count": 10,
            "forks_count": 5,
            "watchers_count": 3,
            "language": "Python",
            "created_at": "2023-01-01",
            "updated_at": "2023-02-01",
            "default_branch": "main",
            "license": {"name": "MIT"},
            "html_url": "https://github.com/testuser/test-repo",
        }
        mock_make_request.return_value = mock_repo_info

        result = self.repo.get_repo_info()

        self.assertEqual(result["name"], "test-repo")
        self.assertEqual(result["stars"], 10)
        self.assertEqual(result["forks"], 5)
        self.assertEqual(result["language"], "Python")
        self.assertEqual(result["license"], "MIT")
        mock_make_request.assert_called_once_with(
            f"/repos/{self.owner}/{self.repo_name}"
        )

    @patch("github_api.GitHubRepo._make_request")
    def test_get_commit_history(self, mock_make_request):
        """Test getting commit history."""
        mock_commits = [
            {
                "sha": "abcd1234",
                "commit": {
                    "author": {
                        "name": "Test User",
                        "email": "test@example.com",
                        "date": "2023-02-01T12:00:00Z",
                    },
                    "message": "Test commit",
                },
                "html_url": "https://github.com/testuser/test-repo/commit/abcd1234",
            }
        ]
        mock_make_request.return_value = mock_commits

        result = self.repo.get_commit_history(limit=10)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["hash"], "abcd1234")
        self.assertEqual(result[0]["author"], "Test User")
        self.assertEqual(result[0]["message"], "Test commit")
        mock_make_request.assert_called_once_with(
            f"/repos/{self.owner}/{self.repo_name}/commits", {"per_page": 10}
        )

    @patch("github_api.GitHubRepo._make_request")
    def test_get_repository_files(self, mock_make_request):
        """Test getting repository files."""
        mock_make_request.side_effect = [
            {"default_branch": "main"},
            {
                "tree": [
                    {
                        "path": "test.py",
                        "type": "blob",
                        "size": 100,
                        "url": "https://api.github.com/repos/testuser/test-repo/git/blobs/abcd1234",
                    },
                    {
                        "path": "test.js",
                        "type": "blob",
                        "size": 200,
                        "url": "https://api.github.com/repos/testuser/test-repo/git/blobs/efgh5678",
                    },
                    {
                        "path": "test.md",
                        "type": "blob",
                        "size": 50,
                        "url": "https://api.github.com/repos/testuser/test-repo/git/blobs/ijkl9012",
                    },
                ]
            },
        ]

        result = self.repo.get_repository_files(
            max_files=2, file_extensions=["py", "js"]
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["path"], "test.py")
        self.assertEqual(result[1]["path"], "test.js")
        mock_make_request.assert_any_call(
            f"/repos/{self.owner}/{self.repo_name}"
        )
        mock_make_request.assert_any_call(
            f"/repos/{self.owner}/{self.repo_name}/git/trees/main", {"recursive": 1}
        )

    @patch("github_api.GitHubRepo._make_request")
    def test_get_file_content(self, mock_make_request):
        """Test getting file content."""
        content = "def test():\n    return True"
        encoded_content = base64.b64encode(content.encode()).decode()
        mock_make_request.return_value = {"type": "file", "content": encoded_content}

        result = self.repo.get_file_content("test.py")

        self.assertEqual(result, content)
        mock_make_request.assert_called_once_with(
            f"/repos/{self.owner}/{self.repo_name}/contents/test.py"
        )

    @patch("github_api.GitHubRepo._make_request")
    def test_get_file_content_not_a_file(self, mock_make_request):
        """Test getting content when path is not a file."""
        mock_make_request.return_value = {"type": "dir"}
        result = self.repo.get_file_content("test-dir")
        self.assertIsNone(result)

    @patch("github_api.GitHubRepo._make_request")
    def test_get_file_content_large_file(self, mock_make_request):
        """Test getting content for a large file."""
        mock_make_request.side_effect = [
            Exception("This API returns blobs up to 1 MB in size"),
            {"default_branch": "main"},
            {"sha": "abcd1234"},
            {"content": base64.b64encode(b"Large file content").decode()},
        ]

        with patch.object(
            self.repo, "_get_large_file_content"
        ) as mock_get_large:
            mock_get_large.return_value = "Large file content"
            result = self.repo.get_file_content("large-file.txt")
            self.assertEqual(result, "Large file content")
            mock_get_large.assert_called_once_with("large-file.txt")


if __name__ == "__main__":
    unittest.main()
