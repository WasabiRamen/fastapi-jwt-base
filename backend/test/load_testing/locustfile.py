"""
Locust Load Testing for FastAPI-MSA-Ready-Template
Backend API Load Testing Script

This script tests:
1. auth/token - Login and token issuance
2. accounts/me - Get current user account information (requires authentication)
"""

import os
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthenticatedUser(HttpUser):
    """
    Simulates an authenticated user making requests to the API.
    
    This user class:
    - Logs in once at the start
    - Continuously makes requests to /accounts/me for load testing
    """
    
    # Wait between 0.1-0.5 seconds between tasks for higher load
    wait_time = between(0.1, 0.5)
    
    # Test credentials - these should match your test data
    TEST_USERNAME = os.getenv("TEST_USERNAME")
    TEST_PASSWORD = os.getenv("TEST_PASSWORD")
    
    def on_start(self):
        """
        Called when a simulated user starts.
        Performs login once to get authentication tokens.
        """
        self.access_token = None
        self.login()
    
    def login(self):
        """
        Login to get access and refresh tokens.
        The tokens are stored in cookies by the backend.
        This is only called once at the start.
        """
        login_data = {
            "username": self.TEST_USERNAME,
            "password": self.TEST_PASSWORD
        }
        
        with self.client.post(
            "/auth/token",
            data=login_data,  # OAuth2PasswordRequestForm expects form data
            catch_response=True,
            name="/auth/token [login]"
        ) as response:
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    self.access_token = json_response.get("access_token")
                    
                    # Cookies are automatically stored by the client
                    logger.info(f"Login successful for user: {self.TEST_USERNAME}")
                    response.success()
                except Exception as e:
                    logger.error(f"Login failed to parse response: {e}")
                    response.failure(f"Failed to parse login response: {e}")
                    raise RescheduleTask()
            else:
                logger.error(f"Login failed with status {response.status_code}: {response.text}")
                response.failure(f"Login failed: {response.status_code}")
                raise RescheduleTask()
    
    @task(1)
    def get_current_user(self):
        """
        GET /accounts/me
        Retrieves current user's account information.
        
        This is the main load testing target.
        This endpoint requires authentication via cookie (access_token).
        Locust's client automatically handles cookies from previous requests.
        """
        # No need to manually set headers - cookies are automatically sent
        with self.client.get(
            "/accounts/me",
            catch_response=True,
            name="/accounts/me"
        ) as response:
            if response.status_code == 200:
                try:
                    user_data = response.json()
                    logger.debug(f"User data retrieved: {user_data.get('user_id', 'unknown')}")
                    response.success()
                except Exception as e:
                    logger.error(f"Failed to parse user data: {e}")
                    response.failure(f"Failed to parse response: {e}")
            elif response.status_code == 401:
                # Token might be expired, try to re-login
                logger.warning("Token expired, attempting re-login")
                response.failure("Unauthorized - token expired")
                self.login()
            else:
                logger.error(f"Get user failed with status {response.status_code}: {response.text}")
                response.failure(f"Request failed: {response.status_code}")


class LoginOnlyUser(HttpUser):
    """
    Simulates users who only perform login operations.
    Useful for testing authentication endpoint under heavy load.
    
    Note: This is disabled by default. Use AuthenticatedUser for /accounts/me load testing.
    """
    
    # Set high weight to make this class rarely selected (or remove it from test)
    weight = 0  # This will not be used in the test
    
    wait_time = between(2, 5)
    
    TEST_USERNAME = os.getenv("TEST_USERNAME", "joonhee0318")
    TEST_PASSWORD = os.getenv("TEST_PASSWORD", "@Kfs980211")
    
    @task(1)
    def login(self):
        """
        Repeatedly test the login endpoint.
        Simulates high authentication load.
        """
        login_data = {
            "username": self.TEST_USERNAME,
            "password": self.TEST_PASSWORD
        }
        
        with self.client.post(
            "/auth/token",
            data=login_data,
            catch_response=True,
            name="/auth/token [login-only]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")


# Event handlers for custom reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts"""
    logger.info("=" * 80)
    logger.info("Load Test Starting")
    logger.info(f"Target Host: {environment.host}")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops"""
    logger.info("=" * 80)
    logger.info("Load Test Completed")
    logger.info("=" * 80)
