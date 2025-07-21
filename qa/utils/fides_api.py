"""
Simple utilities for QA testing scripts.
"""

from typing import Any, Dict, List

import requests


class FidesAPI:
    """Helper class for interacting with the Fides API."""

    def __init__(self, base_url: str = "http://localhost:8080", username: str = "root_user", password: str = "Testpassword1!"):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.access_token = None

    def _authenticate(self) -> bool:
        """Authenticate with the Fides API and get access token."""
        if self.access_token:
            return True

        try:
            auth_url = f"{self.base_url}/api/v1/login"
            print("Authenticating with Fides API...")
            response = self.session.post(
                auth_url,
                json={"username": self.username, "password": self.password}
            )
            response.raise_for_status()

            token_data = response.json().get('token_data', {})
            self.access_token = token_data.get('access_token')

            if not self.access_token:
                print("No access token in response")
                return False

            # Set authorization header for future requests
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            print("Authentication successful")
            return True

        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request with error handling and automatic authentication."""
        if not self._authenticate():
            raise Exception("Failed to authenticate with Fides API")

        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)

            # Handle token expiration
            if response.status_code == 401:
                print("Token expired, re-authenticating...")
                self.access_token = None
                if self._authenticate():
                    response = self.session.request(method, url, **kwargs)

            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"API request failed: {method} {url} - {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise

    def create_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dataset."""
        response = self._request('POST', '/api/v1/dataset', json=dataset_data)
        return response.json()

    def create_system(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new system."""
        response = self._request('POST', '/api/v1/system', json=system_data)
        return response.json()

    def create_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new connection configuration."""
        response = self._request('PATCH', '/api/v1/connection/', json=[connection_data])
        return response.json()

    def update_connection(self, connection_key: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing connection configuration."""
        # First get the existing connection
        existing_connections = self.get_connections()
        existing_connection = next((c for c in existing_connections if c.get('key') == connection_key), None)

        if not existing_connection:
            raise Exception(f"Connection {connection_key} not found")

        # Merge the update data with existing connection data
        connection_data = {**existing_connection, **update_data}

        # Use PATCH to update the connection
        response = self._request('PATCH', '/api/v1/connection/', json=[connection_data])
        return response.json()

    def create_system_connection(self, system_key: str, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a connection configuration linked to a specific system."""
        response = self._request('PATCH', f'/api/v1/system/{system_key}/connection', json=[connection_data])
        return response.json()

    def get_datasets(self) -> List[Dict[str, Any]]:
        """Get all datasets."""
        response = self._request('GET', '/api/v1/dataset')
        result = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(result, list):
            return result
        else:
            # Handle paginated response - return the items list
            return result.get('items', [])

    def get_systems(self) -> List[Dict[str, Any]]:
        """Get all systems."""
        response = self._request('GET', '/api/v1/system')
        result = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(result, list):
            return result
        else:
            # Handle paginated response - return the items list
            return result.get('items', [])

    def get_connections(self) -> List[Dict[str, Any]]:
        """Get all connection configurations."""
        response = self._request('GET', '/api/v1/connection/')
        result = response.json()
        # Handle paginated response - return the items list
        return result.get('items', [])

    def get_system_connections(self, system_key: str) -> List[Dict[str, Any]]:
        """Get all connections for a specific system."""
        response = self._request('GET', f'/api/v1/system/{system_key}/connection')
        result = response.json()
        # Handle both paginated and non-paginated responses
        if isinstance(result, list):
            return result
        else:
            # Handle paginated response - return the items list
            return result.get('items', [])

    def get_system_by_key(self, system_key: str) -> Dict[str, Any]:
        """Get a system by its fides_key."""
        systems = self.get_systems()
        system = next((s for s in systems if s.get('fides_key') == system_key), None)
        if not system:
            raise Exception(f"System {system_key} not found")
        return system

    def delete_dataset(self, dataset_key: str) -> bool:
        """Delete a dataset by key."""
        try:
            self._request('DELETE', f'/api/v1/dataset/{dataset_key}')
            return True
        except requests.RequestException:
            return False

    def delete_system(self, system_key: str) -> bool:
        """Delete a system by key."""
        try:
            self._request('DELETE', f'/api/v1/system/{system_key}')
            return True
        except requests.RequestException:
            return False

    def delete_connection(self, connection_key: str) -> bool:
        """Delete a connection configuration by key."""
        try:
            self._request('DELETE', f'/api/v1/connection/{connection_key}')
            return True
        except requests.RequestException:
            return False

    def health_check(self) -> bool:
        """Check if the Fides API is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def link_datasets_to_connection(self, connection_key: str, dataset_keys: List[str]) -> Dict[str, Any]:
        """Link multiple datasets to a connection using DatasetConfig."""
        # Create dataset pairs - each dataset links to itself as the CTL dataset
        dataset_pairs = [
            {"fides_key": dataset_key, "ctl_dataset_fides_key": dataset_key}
            for dataset_key in dataset_keys
        ]

        response = self._request('PATCH', f'/api/v1/connection/{connection_key}/datasetconfig', json=dataset_pairs)
        return response.json()


def generate_dataset(index: int) -> Dict[str, Any]:
    """Generate a simple test dataset."""
    return {
        "fides_key": f"qa_test_dataset_{index}",
        "organization_fides_key": "default_organization",
        "name": f"QA Test Dataset {index}",
        "description": f"Test dataset {index} for pagination testing.",
        "meta": None,
        "data_categories": [],
        "collections": [
            {
                "name": "users",
                "description": "User data",
                "data_categories": [],
                "fields": [
                    {"name": "id", "description": "User ID", "data_categories": ["user.unique_id"]},
                    {"name": "email", "description": "Email", "data_categories": ["user.contact.email"]},
                    {"name": "name", "description": "Name", "data_categories": ["user.name"]}
                ]
            }
        ]
    }


def generate_system(system_name: str, dataset_count: int) -> Dict[str, Any]:
    """Generate a simple test system for integration testing."""
    return {
        "fides_key": system_name,
        "organization_fides_key": "default_organization",
        "name": "QA Integration Test System",
        "description": f"Test system with {dataset_count} datasets for integration testing.",
        "system_type": "Service",
        "privacy_declarations": [],
        "system_dependencies": []
    }


def generate_connection() -> Dict[str, Any]:
    """Generate a simple test PostgreSQL connection."""
    return {
        "name": "QA Test PostgreSQL Connection",
        "key": "qa_test_postgres_connection",
        "connection_type": "postgres",
        "access": "write",
        "description": "Test PostgreSQL connection for pagination testing",
        "secrets": {"host": "localhost"},
    }


def confirm_action(message: str) -> bool:
    """Ask user for confirmation. Returns True if confirmed."""
    try:
        response = input(f"{message} (y/N): ").strip().lower()
        return response in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled")
        return False
