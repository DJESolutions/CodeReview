
import unittest
from unittest.mock import MagicMock, patch

from github_api import GitHubRepo


class TestGitHubRepoPositive(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.repo = GitHubRepo("owner", "repo", "access_token")

    @patch("github_api.GitHubRepo._make_request")
    def test_get_repo_info(self, mock_make_request):
        """Test get_repo_info returns expected repository information."""
        # Define mock API response
        mock_make_request.return_value = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "description": "Test repository",
            "stargazers_count": 10,
            "forks_count": 5,
            "watchers_count": 8,
            "language": "Python",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-02-01T12:00:00Z",
            "default_branch": "main",
            "license": {"name": "MIT License"},
            "html_url": "https://github.com/owner/test-repo",
        }

        # Call the method
        repo_info = self.repo.get_repo_info()

        # Verify request was made correctly
        mock_make_request.assert_called_once_with("/repos/owner/repo")

        # Verify result
        self.assertEqual(repo_info["name"], "test-repo")
        self.assertEqual(repo_info["full_name"], "owner/test-repo")
        self.assertEqual(repo_info["stars"], 10)
        self.assertEqual(repo_info["language"], "Python")
        self.assertEqual(repo_info["license"], "MIT License")

    @patch("github_api.GitHubRepo._make_request")
    def test_get_commit_history(self, mock_make_request):
        """Test get_commit_history returns correctly formatted commit data."""
        # Define mock API response
        mock_make_request.return_value = [
            {
                "sha": "abc123",
                "commit": {
                    "author": {
                        "name": "Test User",
                        "email": "test@example.com",
                        "date": "2023-03-01T12:00:00Z",
                    },
                    "message": "Initial commit",
                },
                "html_url": "https://github.com/owner/repo/commit/abc123",
            }
        ]

        # Call the method
        commits = self.repo.get_commit_history(limit=1)

        # Verify request was made correctly
        mock_make_request.assert_called_once_with(
            "/repos/owner/repo/commits", {"per_page": 1}
        )

        # Verify result
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]["hash"], "abc123")
        self.assertEqual(commits[0]["author"], "Test User")
        self.assertEqual(commits[0]["message"], "Initial commit")

    @patch("github_api.GitHubRepo._make_request")
    def test_get_repository_files(self, mock_make_request):
        """Test get_repository_files returns filtered file list."""
        # Mock get_repo_info to return default branch
        self.repo.get_repo_info = MagicMock(return_value={"default_branch": "main"})

        # Define mock API response
        mock_make_request.return_value = {
            "tree": [
                {
                    "path": "file1.py",
                    "type": "blob",
                    "size": 100,
                    "url": "https://api.github.com/repos/owner/repo/git/blobs/abc123",
                },
                {
                    "path": "file2.js",
                    "type": "blob",
                    "size": 200,
                    "url": "https://api.github.com/repos/owner/repo/git/blobs/def456",
                },
                {
                    "path": "dir",
                    "type": "tree",
                    "url": "https://api.github.com/repos/owner/repo/git/trees/ghi789",
                },
            ]
        }

        # Call the method with python files only
        files = self.repo.get_repository_files(max_files=1, file_extensions=["py"])

        # Verify request was made correctly
        mock_make_request.assert_called_with(
            "/repos/owner/repo/git/trees/main", {"recursive": 1}
        )

        # Verify result
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["path"], "file1.py")
        self.assertEqual(files[0]["size"], 100)

    @patch("github_api.GitHubRepo._make_request")
    def test_get_file_content(self, mock_make_request):
        """Test get_file_content returns decoded file content."""
        # Define mock API response
        import base64

        content = "print('Hello, World!')"
        encoded_content = base64.b64encode(content.encode()).decode()

        mock_make_request.return_value = {"type": "file", "content": encoded_content}

        # Call the method
        file_content = self.repo.get_file_content("file.py")

        # Verify request was made correctly
        mock_make_request.assert_called_once_with("/repos/owner/repo/contents/file.py")

        # Verify result
        self.assertEqual(file_content, content)

    @patch("github_api.logger")
    @patch("github_api.requests.get")
    def test_make_request_successful(self, mock_get, mock_logger):
        """Test _make_request handles successful API responses."""
        # Mock requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"success": True}
        mock_get.return_value = mock_response

        # Call the method
        result = self.repo._make_request("/test/endpoint")

        # Verify request was made correctly
        mock_get.assert_called_once()

        # Verify result
        self.assertEqual(result, {"success": True})
        mock_logger.debug.assert_called()


class TestGitHubRepoNegative(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.repo = GitHubRepo("owner", "repo", "access_token")

    @patch("github_api.GitHubRepo._make_request")
    def test_get_repo_info_with_error(self, mock_make_request):
        """Test get_repo_info handles API errors."""
        # Mock make_request to raise an exception
        mock_make_request.side_effect = Exception("API error")

        # Expect the method to raise the exception
        with self.assertRaises(Exception):
            self.repo.get_repo_info()

    @patch("github_api.GitHubRepo._make_request")
    def test_get_commit_history_empty(self, mock_make_request):
        """Test get_commit_history returns empty list when no commits exist."""
        # Mock make_request to return empty list
        mock_make_request.return_value = []

        # Call the method
        commits = self.repo.get_commit_history()

        # Verify result
        self.assertEqual(commits, [])

    @patch("github_api.GitHubRepo._make_request")
    @patch("github_api.logger")
    def test_get_file_content_not_file(self, mock_logger, mock_make_request):
        """Test get_file_content returns None if path is not a file."""
        # Mock make_request to return a directory
        mock_make_request.return_value = {"type": "dir"}

        # Call the method
        content = self.repo.get_file_content("dir")

        # Verify result
        self.assertIsNone(content)
        mock_logger.warning.assert_called()

    @patch("github_api.GitHubRepo._make_request")
    @patch("github_api.logger")
    def test_get_file_content_empty(self, mock_logger, mock_make_request):
        """Test get_file_content returns None if content is empty."""
        # Mock make_request to return empty content
        mock_make_request.return_value = {"type": "file", "content": ""}

        # Call the method
        content = self.repo.get_file_content("file.py")

        # Verify result
        self.assertIsNone(content)
        mock_logger.warning.assert_called()

    @patch("github_api.handle_error")
    @patch("github_api.logger")
    @patch("github_api.requests.get")
    def test_make_request_unauthorized(self, mock_get, mock_logger, mock_handle_error):
        """Test _make_request handles 401 unauthorized responses."""
        # Mock requests.get
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {"Content-Type": "application/json"}
        mock_get.return_value = mock_response

        # Call the method
        self.repo._make_request("/test/endpoint")

        # Verify error handling
        mock_logger.error.assert_called()
        mock_handle_error.assert_called()

    @patch("github_api.time.sleep", return_value=None)
    @patch("github_api.logger")
    @patch("github_api.requests.get")
    def test_make_request_rate_limit(self, mock_get, mock_logger, mock_sleep):
        """Test _make_request handles rate limit responses."""
        # Setup first response to be rate limited
        mock_response1 = MagicMock()
        mock_response1.status_code = 403
        mock_response1.headers = {
            "Content-Type": "application/json",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + 10),
        }

        # Setup second response (after retry) to be successful
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.headers = {"Content-Type": "application/json"}
        mock_response2.json.return_value = {"success": True}

        # Configure mock to return different responses on subsequent calls
        mock_get.side_effect = [mock_response1, mock_response2]

        # Call the method
        result = self.repo._make_request("/test/endpoint")

        # Verify request was retried
        self.assertEqual(mock_get.call_count, 2)

        # Verify sleep was called for rate limit
        mock_sleep.assert_called()

        # Verify result
        self.assertEqual(result, {"success": True})


if __name__ == "__main__":
    unittest.main()
import base64
import unittest
from unittest.mock import MagicMock, patch

from github_api import GitHubRepo


class TestGitHubRepo(unittest.TestCase):
    """Test cases for the GitHubRepo class."""

    def setUp(self):
        """Set up test fixtures."""
        self.owner = "testuser"
        self.repo_name = "test-repo"
        self.access_token = "test_token"
        self.repo = GitHubRepo(self.owner, self.repo_name, self.access_token)

    def test_initialization(self):
        """Test GitHubRepo initialization."""
        self.assertEqual(self.repo.owner, self.owner)
        self.assertEqual(self.repo.repo_name, self.repo_name)
        self.assertEqual(self.repo.base_url, "https://api.github.com")
        self.assertEqual(
            self.repo.headers["Authorization"], f"token {self.access_token}"
        )

    @patch("requests.get")
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"name": "test-repo"}
        mock_get.return_value = mock_response

        # Make the request
        endpoint = "/test-endpoint"
        result = self.repo._make_request(endpoint)

        # Verify the result
        self.assertEqual(result, {"name": "test-repo"})

        # Verify the request was made correctly
        mock_get.assert_called_once_with(
            "https://api.github.com/test-endpoint",
            headers=self.repo.headers,
            params=None,
            timeout=(10, 30),
        )

    @patch("requests.get")
    @patch("github_api.handle_error")
    def test_make_request_error(self, mock_handle_error, mock_get):
        """Test API request with error."""
        # Setup mock response with error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        # Make the request (should catch the exception)
        endpoint = "/test-endpoint"
        with self.assertRaises(
            Exception
        ):  # This is needed because handle_error will raise
            self.repo._make_request(endpoint)

        # Verify error was handled
        mock_handle_error.assert_called_once()

    @patch("github_api.GitHubRepo._make_request")
    def test_get_repo_info(self, mock_make_request):
        """Test getting repository information."""
        # Setup mock response
        mock_make_request.return_value = {
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

        # Get repository information
        result = self.repo.get_repo_info()

        # Verify the result
        self.assertEqual(result["name"], "test-repo")
        self.assertEqual(result["stars"], 10)
        self.assertEqual(result["forks"], 5)
        self.assertEqual(result["language"], "Python")
        self.assertEqual(result["license"], "MIT")

        # Verify the request was made correctly
        mock_make_request.assert_called_once_with(
            f"/repos/{self.owner}/{self.repo_name}"
        )

    @patch("github_api.GitHubRepo._make_request")
    def test_get_commit_history(self, mock_make_request):
        """Test getting commit history."""
        # Setup mock response
        mock_make_request.return_value = [
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

        # Get commit history
        result = self.repo.get_commit_history(limit=10)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["hash"], "abcd1234")
        self.assertEqual(result[0]["author"], "Test User")
        self.assertEqual(result[0]["message"], "Test commit")

        # Verify the request was made correctly
        mock_make_request.assert_called_once_with(
            f"/repos/{self.owner}/{self.repo_name}/commits", {"per_page": 10}
        )

    @patch("github_api.GitHubRepo._make_request")
    def test_get_repository_files(self, mock_make_request):
        """Test getting repository files."""
        # Setup mock responses
        mock_make_request.side_effect = [
            # First call - get repo info to get default branch
            {"default_branch": "main"},
            # Second call - get tree
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

        # Get repository files
        result = self.repo.get_repository_files(
            max_files=2, file_extensions=["py", "js"]
        )

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["path"], "test.py")
        self.assertEqual(result[1]["path"], "test.js")

        # Verify the requests were made correctly
        mock_make_request.assert_any_call(f"/repos/{self.owner}/{self.repo_name}")
        mock_make_request.assert_any_call(
            f"/repos/{self.owner}/{self.repo_name}/git/trees/main", {"recursive": 1}
        )

    @patch("github_api.GitHubRepo._make_request")
    def test_get_file_content(self, mock_make_request):
        """Test getting file content."""
        # Setup mock response with base64 encoded content
        content = "def test():\n    return True"
        encoded_content = base64.b64encode(content.encode()).decode()
        mock_make_request.return_value = {"type": "file", "content": encoded_content}

        # Get file content
        result = self.repo.get_file_content("test.py")

        # Verify the result
        self.assertEqual(result, content)

        # Verify the request was made correctly
        mock_make_request.assert_called_once_with(
            f"/repos/{self.owner}/{self.repo_name}/contents/test.py"
        )

    @patch("github_api.GitHubRepo._make_request")
    def test_get_file_content_not_a_file(self, mock_make_request):
        """Test getting content when path is not a file."""
        # Setup mock response for a directory
        mock_make_request.return_value = {"type": "dir"}

        # Get file content
        result = self.repo.get_file_content("test-dir")

        # Verify the result is None
        self.assertIsNone(result)

    @patch("github_api.GitHubRepo._make_request")
    def test_get_file_content_large_file(self, mock_make_request):
        """Test getting content for a large file."""
        # First call raises exception for large file
        mock_make_request.side_effect = [
            Exception("This API returns blobs up to 1 MB in size"),
            # Second call - get repo info
            {"default_branch": "main"},
            # Third call - get file sha
            {"sha": "abcd1234"},
            # Fourth call - get blob
            {"content": base64.b64encode(b"Large file content").decode()},
        ]

        # Mock _get_large_file_content to be called instead
        with patch.object(self.repo, "_get_large_file_content") as mock_get_large:
            mock_get_large.return_value = "Large file content"

            # Get file content
            result = self.repo.get_file_content("large-file.txt")

            # Verify the result
            self.assertEqual(result, "Large file content")

            # Verify _get_large_file_content was called
            mock_get_large.assert_called_once_with("large-file.txt")


if __name__ == "__main__":
    unittest.main()
