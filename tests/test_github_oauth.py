
import os
import unittest
from unittest.mock import MagicMock, patch

from github_oauth import GitHubOAuth


class TestGitHubOAuthPositive(unittest.TestCase):

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_initialization(self):
        """Test that GitHubOAuth initializes with correct environment variables."""
        oauth = GitHubOAuth()
        self.assertEqual(oauth.client_id, "test_client_id")
        self.assertEqual(oauth.client_secret, "test_client_secret")
        self.assertEqual(oauth.base_url, "https://github.com")
        self.assertEqual(oauth.api_url, "https://api.github.com")

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_get_authorization_url_without_state(self):
        """Test the authorization URL is generated correctly without state."""
        oauth = GitHubOAuth()
        expected_url = "https://github.com/login/oauth/authorize?client_id=test_client_id&scope=repo%2Cread%3Auser%2Cuser%3Aemail"
        self.assertEqual(oauth.get_authorization_url(), expected_url)

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_get_authorization_url_with_state(self):
        """Test the authorization URL is generated correctly with state."""
        oauth = GitHubOAuth()
        expected_url = "https://github.com/login/oauth/authorize?client_id=test_client_id&scope=repo%2Cread%3Auser%2Cuser%3Aemail&state=test_state"
        self.assertEqual(oauth.get_authorization_url(state="test_state"), expected_url)

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    @patch("requests.post")
    def test_exchange_code_for_token_success(self, mock_post):
        """Test exchanging code for token returns expected result on success."""
        oauth = GitHubOAuth()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_access_token"}
        mock_post.return_value = mock_response

        result = oauth.exchange_code_for_token("test_code")
        self.assertEqual(result, {"access_token": "test_access_token"})

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    @patch("requests.get")
    def test_get_user_info_success(self, mock_get):
        """Test getting user info returns expected result on success."""
        oauth = GitHubOAuth()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "test_user"}
        mock_get.return_value = mock_response

        result = oauth.get_user_info("test_access_token")
        self.assertEqual(result, {"login": "test_user"})

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_redirect_uri_initialization(self):
        """Test that redirect_uri is initialized correctly from environment variable."""
        with patch.dict(
            os.environ, {"GITHUB_REDIRECT_URI": "http://localhost/callback"}
        ):
            oauth = GitHubOAuth()
            self.assertEqual(oauth.redirect_uri, "http://localhost/callback")

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_clear_cache(self):
        """Test that clear_cache empties the cache dictionaries."""
        oauth = GitHubOAuth()
        # Fill caches with test data
        oauth._token_cache = {"code": "token"}
        oauth._user_info_cache = {"token": "user"}
        # Clear cache
        oauth.clear_cache()
        # Verify caches are empty
        self.assertEqual(oauth._token_cache, {})
        self.assertEqual(oauth._user_info_cache, {})


class TestGitHubOAuthNegative(unittest.TestCase):

    @patch("os.getenv")
    def test_initialization_without_client_secret(self, mock_getenv):
        """Test initialization when the client secret is not set."""
        mock_getenv.side_effect = lambda key, default=None: (
            None
            if key == "GH_CLIENT_SECRET"
            else "test_id" if key == "GITHUB_CLIENT_ID" else default
        )
        with patch("streamlit.warning") as mock_warning:
            oauth = GitHubOAuth()
            self.assertIsNone(oauth.client_secret)
            mock_warning.assert_called_with(
                "GitHub OAuth client secret not configured. Set GH_CLIENT_SECRET environment variable."
            )

    @patch("streamlit.error")
    @patch("requests.post")
    def test_exchange_code_for_token_with_none_code(self, mock_post, mock_error):
        """Test exchanging code for token with None code."""
        oauth = GitHubOAuth()
        token = oauth.exchange_code_for_token(None)
        self.assertIsNone(token)
        mock_error.assert_called_with("No authorization code provided")

    @patch("streamlit.error")
    @patch("requests.post")
    def test_exchange_code_for_token_with_request_exception(
        self, mock_post, mock_error
    ):
        """Test exchanging code for token with a request exception."""
        oauth = GitHubOAuth()
        mock_post.side_effect = requests.RequestException("Connection error")
        token = oauth.exchange_code_for_token("some_code")
        self.assertIsNone(token)
        mock_error.assert_called_with(
            "Error exchanging code for token: Connection error"
        )

    @patch("streamlit.error")
    @patch("requests.get")
    def test_get_user_info_with_none_access_token(self, mock_get, mock_error):
        """Test getting user info with None access token."""
        oauth = GitHubOAuth()
        user_info = oauth.get_user_info(None)
        self.assertIsNone(user_info)
        mock_error.assert_called_with("No access token provided")

    @patch("streamlit.error")
    @patch("requests.get")
    def test_get_user_info_with_request_exception(self, mock_get, mock_error):
        """Test getting user info with a request exception."""
        oauth = GitHubOAuth()
        mock_get.side_effect = requests.RequestException("Connection error")
        user_info = oauth.get_user_info("some_access_token")
        self.assertIsNone(user_info)
        mock_error.assert_called_with("Error fetching user info: Connection error")

    @patch("os.getenv")
    def test_initialization_with_missing_environment_variables(self, mock_getenv):
        """Test initialization with missing environment variables."""
        mock_getenv.side_effect = lambda key, default=None: None
        with patch("streamlit.warning") as mock_warning:
            oauth = GitHubOAuth()
            self.assertIsNone(oauth.client_id)
            self.assertIsNone(oauth.client_secret)
            mock_warning.assert_any_call(
                "GitHub OAuth client ID not configured. Set GITHUB_CLIENT_ID environment variable."
            )
            mock_warning.assert_any_call(
                "GitHub OAuth client secret not configured. Set GH_CLIENT_SECRET environment variable."
            )


if __name__ == "__main__":
    unittest.main()
import os
import unittest
from unittest.mock import MagicMock, patch

from github_oauth import GitHubOAuth


class TestGitHubOAuthPositive(unittest.TestCase):
    """Positive test cases for GitHubOAuth class."""

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_initialization(self):
        """Test that GitHubOAuth initializes with correct environment variables."""
        oauth = GitHubOAuth()
        self.assertEqual(oauth.client_id, "test_client_id")
        self.assertEqual(oauth.client_secret, "test_client_secret")
        self.assertEqual(oauth.base_url, "https://github.com")
        self.assertEqual(oauth.api_url, "https://api.github.com")

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_get_authorization_url_without_state(self):
        """Test the authorization URL is generated correctly without state."""
        oauth = GitHubOAuth()
        expected_url = "https://github.com/login/oauth/authorize?client_id=test_client_id&scope=repo%2Cread%3Auser%2Cuser%3Aemail"
        self.assertEqual(oauth.get_authorization_url(), expected_url)

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
        },
    )
    def test_get_authorization_url_with_state(self):
        """Test the authorization URL is generated correctly with state."""
        oauth = GitHubOAuth()
        state = "random_state_string"
        expected_url = f"https://github.com/login/oauth/authorize?client_id=test_client_id&scope=repo%2Cread%3Auser%2Cuser%3Aemail&state={state}"
        self.assertEqual(oauth.get_authorization_url(state), expected_url)

    @patch.dict(
        os.environ,
        {
            "GITHUB_CLIENT_ID": "test_client_id",
            "GH_CLIENT_SECRET": "test_client_secret",
            "GITHUB_REDIRECT_URI": "https://example.com/callback",
        },
    )
    def test_get_authorization_url_with_redirect_uri(self):
        """Test the authorization URL includes redirect_uri when configured."""
        oauth = GitHubOAuth()
        expected_url = "https://github.com/login/oauth/authorize?client_id=test_client_id&scope=repo%2Cread%3Auser%2Cuser%3Aemail&redirect_uri=https%3A%2F%2Fexample.com%2Fcallback"
        self.assertEqual(oauth.get_authorization_url(), expected_url)

    @patch("requests.post")
    def test_exchange_code_for_token_success(self, mock_post):
        """Test successful exchange of code for token."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "scope": "repo,read:user,user:email",
        }
        mock_post.return_value = mock_response

        oauth = GitHubOAuth()
        oauth.client_id = "test_client_id"
        oauth.client_secret = "test_client_secret"

        result = oauth.exchange_code_for_token("test_code")

        # Verify the result
        self.assertEqual(result["access_token"], "test_access_token")
        self.assertEqual(result["token_type"], "bearer")

        # Verify the request was made correctly
        mock_post.assert_called_once_with(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "code": "test_code",
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )

    @patch("requests.get")
    def test_get_user_info_success(self, mock_get):
        """Test successful retrieval of user information."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "login": "testuser",
            "id": 12345,
            "name": "Test User",
            "email": "test@example.com",
        }
        mock_get.return_value = mock_response

        oauth = GitHubOAuth()
        result = oauth.get_user_info("test_access_token")

        # Verify the result
        self.assertEqual(result["login"], "testuser")
        self.assertEqual(result["name"], "Test User")
        self.assertEqual(result["email"], "test@example.com")

        # Verify the request was made correctly
        mock_get.assert_called_once_with(
            "https://api.github.com/user",
            headers={
                "Authorization": "Bearer test_access_token",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=10,
        )

    def test_clear_cache(self):
        """Test clearing the token and user info caches."""
        oauth = GitHubOAuth()

        # Populate caches
        oauth._token_cache = {"code1": "token1"}
        oauth._user_info_cache = {"token1": {"name": "Test User"}}

        # Clear caches
        oauth.clear_cache()

        # Verify caches are empty
        self.assertEqual(oauth._token_cache, {})
        self.assertEqual(oauth._user_info_cache, {})


class TestGitHubOAuthNegative(unittest.TestCase):
    """Negative test cases for GitHubOAuth class."""

    @patch("os.getenv")
    def test_initialization_without_client_id(self, mock_getenv):
        """Test initialization when the client ID is not set."""
        mock_getenv.side_effect = lambda key, default=None: (
            None if key == "GITHUB_CLIENT_ID" else default
        )
        oauth = GitHubOAuth()
        self.assertIsNone(oauth.client_id)

    @patch("os.getenv")
    def test_initialization_without_client_secret(self, mock_getenv):
        """Test initialization when the client secret is not set."""
        mock_getenv.side_effect = lambda key, default=None: (
            None if key == "GH_CLIENT_SECRET" else default
        )
        oauth = GitHubOAuth()
        self.assertIsNone(oauth.client_secret)

    @patch("streamlit.warning")
    @patch("os.getenv")
    def test_validate_configuration_warnings(self, mock_getenv, mock_warning):
        """Test that warnings are displayed for missing configuration."""
        mock_getenv.return_value = None
        oauth = GitHubOAuth()
        oauth._validate_configuration()

        # Check that warnings were called twice (once for client_id, once for client_secret)
        self.assertEqual(mock_warning.call_count, 2)

    @patch("requests.post")
    def test_exchange_code_for_token_with_none_code(self, mock_post):
        """Test exchanging code for token with None code."""
        oauth = GitHubOAuth()
        token = oauth.exchange_code_for_token(None)
        self.assertIsNone(token)
        mock_post.assert_not_called()

    @patch("streamlit.error")
    @patch("requests.post")
    def test_exchange_code_for_token_with_error_response(self, mock_post, mock_error):
        """Test exchanging code for token with an error response."""
        # Setup mock response with an error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API error")
        mock_post.return_value = mock_response

        oauth = GitHubOAuth()
        oauth.client_id = "test_client_id"
        oauth.client_secret = "test_client_secret"

        result = oauth.exchange_code_for_token("test_code")

        # Verify the result is None and error was logged
        self.assertIsNone(result)
        mock_error.assert_called_once()

    @patch("streamlit.error")
    @patch("requests.get")
    def test_get_user_info_with_none_token(self, mock_get, mock_error):
        """Test getting user info with None token."""
        oauth = GitHubOAuth()
        user_info = oauth.get_user_info(None)

        self.assertIsNone(user_info)
        mock_get.assert_not_called()
        mock_error.assert_called_once()

    @patch("streamlit.error")
    @patch("requests.get")
    def test_get_user_info_with_error_response(self, mock_get, mock_error):
        """Test getting user info with an error response."""
        # Setup mock response with an error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API error")
        mock_get.return_value = mock_response

        oauth = GitHubOAuth()

        result = oauth.get_user_info("test_access_token")

        # Verify the result is None and error was logged
        self.assertIsNone(result)
        mock_error.assert_called_once()

    @patch("requests.post")
    def test_exchange_code_for_token_caching(self, mock_post):
        """Test that token responses are cached."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "bearer",
        }
        mock_post.return_value = mock_response

        oauth = GitHubOAuth()
        oauth.client_id = "test_client_id"
        oauth.client_secret = "test_client_secret"

        # First call should make the request
        first_result = oauth.exchange_code_for_token("test_code")

        # Reset the mock to verify second call
        mock_post.reset_mock()

        # Second call should use cache
        second_result = oauth.exchange_code_for_token("test_code")

        # Verify results are the same
        self.assertEqual(first_result, second_result)

        # Verify no additional request was made
        mock_post.assert_not_called()

    @patch("requests.get")
    def test_get_user_info_caching(self, mock_get):
        """Test that user info responses are cached."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser", "name": "Test User"}
        mock_get.return_value = mock_response

        oauth = GitHubOAuth()

        # First call should make the request
        first_result = oauth.get_user_info("test_access_token")

        # Reset the mock to verify second call
        mock_get.reset_mock()

        # Second call should use cache
        second_result = oauth.get_user_info("test_access_token")

        # Verify results are the same
        self.assertEqual(first_result, second_result)

        # Verify no additional request was made
        mock_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
