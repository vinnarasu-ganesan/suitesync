import requests
import base64
import logging

logger = logging.getLogger(__name__)


class TestRailService:
    """Service for interacting with TestRail API."""

    def __init__(self, url, email, api_key, suite_ids):
        self.url = url.rstrip('/')
        self.email = email
        self.api_key = api_key

        # Accept a single suite ID (str/int) or a list of suite IDs
        if isinstance(suite_ids, (list, tuple)):
            self.suite_ids = [str(sid).strip() for sid in suite_ids if sid]
        else:
            self.suite_ids = [str(suite_ids).strip()] if suite_ids else []

        # Primary suite ID – used for single-suite API calls and backward compatibility
        self.suite_id = self.suite_ids[0] if self.suite_ids else None

        self.project_id = None  # Will be fetched from suite
        self.headers = {
            'Content-Type': 'application/json'
        }

        # Create basic auth header
        auth_string = f"{email}:{api_key}"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = base64.b64encode(auth_bytes)
        base64_string = base64_bytes.decode('ascii')
        self.headers['Authorization'] = f'Basic {base64_string}'

        # Fetch project_id from the primary suite
        self._fetch_project_id_from_suite()

    def _make_request(self, method, endpoint, data=None):
        """Make a request to the TestRail API."""
        url = f"{self.url}/index.php?/api/v2/{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, verify=False)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, verify=False)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, verify=False)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"TestRail API error: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            return None

    def _fetch_project_id_from_suite(self):
        """Fetch project_id from the primary suite."""
        if not self.suite_id:
            return
        try:
            suite = self._make_request('GET', f'get_suite/{self.suite_id}')
            if suite and 'project_id' in suite:
                self.project_id = suite['project_id']
                logger.info(f"Fetched project_id {self.project_id} from suite {self.suite_id}")
        except Exception as e:
            logger.warning(f"Could not fetch project_id from suite: {e}")

    def get_case(self, case_id):
        """Get a specific test case by ID."""
        # Remove 'C' prefix if present
        case_id = case_id.replace('C', '').replace('c', '')
        return self._make_request('GET', f'get_case/{case_id}')

    def get_cases(self, suite_id=None):
        """Get all test cases for the suite (handles pagination via _links.next)."""
        suite_id = suite_id or self.suite_id
        if not self.project_id:
            logger.error("project_id not available, cannot fetch cases")
            return None

        all_cases = []
        offset = 0
        limit = 250  # TestRail API max limit per request

        while True:
            endpoint = f'get_cases/{self.project_id}&suite_id={suite_id}&limit={limit}&offset={offset}'
            response = self._make_request('GET', endpoint)

            if not response:
                logger.warning(f"No response from API at offset {offset}")
                break

            # Handle dict (paginated) response
            if isinstance(response, dict):
                cases = response.get('cases', [])
                has_next = response.get('_links', {}).get('next') is not None

                logger.info(f"Fetched {len(cases)} cases at offset {offset} (has_next: {has_next})")
            else:
                # Fallback for list response
                cases = response if isinstance(response, list) else []
                has_next = False
                logger.info(f"Fetched {len(cases)} cases (list response)")

            if not cases:
                logger.info(f"No more cases to fetch at offset {offset}")
                break

            all_cases.extend(cases)
            logger.info(f"Total cases fetched so far: {len(all_cases)}")

            # Check if there's a next page using _links
            if isinstance(response, dict) and not has_next:
                logger.info(f"No next link, all cases fetched")
                break

            # If we got fewer cases than requested and no next link, we've reached the end
            if len(cases) < limit and not has_next:
                logger.info(f"Received {len(cases)} cases (less than limit {limit}), reached end")
                break

            # Move to next page
            offset += len(cases)

        logger.info(f"✓ Total cases fetched: {len(all_cases)}")

        # Return in the same format as the API (dict with 'cases' key)
        return {'cases': all_cases, 'size': len(all_cases)}

    def create_case(self, section_id, title, **kwargs):
        """Create a new test case."""
        data = {
            'title': title,
            **kwargs
        }
        return self._make_request('POST', f'add_case/{section_id}', data)

    def update_case(self, case_id, **kwargs):
        """Update an existing test case."""
        # Remove 'C' prefix if present
        case_id = case_id.replace('C', '').replace('c', '')
        return self._make_request('POST', f'update_case/{case_id}', kwargs)

    def get_sections(self, suite_id=None):
        """Get all sections for the suite (handles pagination)."""
        suite_id = suite_id or self.suite_id
        if not self.project_id:
            logger.error("project_id not available, cannot fetch sections")
            return None

        all_sections = []
        offset = 0
        limit = 250  # TestRail API default/max limit

        while True:
            endpoint = f'get_sections/{self.project_id}&suite_id={suite_id}&limit={limit}&offset={offset}'
            response = self._make_request('GET', endpoint)

            if not response:
                break

            # Handle both dict (paginated) and list responses
            if isinstance(response, dict):
                sections = response.get('sections', [])
            else:
                sections = response if isinstance(response, list) else []

            if not sections:
                break

            all_sections.extend(sections)
            logger.info(f"Fetched {len(sections)} sections (total so far: {len(all_sections)})")

            # If we got fewer sections than the limit, we've reached the end
            if len(sections) < limit:
                break

            offset += limit

        logger.info(f"Total sections fetched: {len(all_sections)}")

        # Return in the same format as the API
        return all_sections if all_sections else response

    def get_suite(self, suite_id=None):
        """Get suite information. Defaults to the primary suite."""
        sid = suite_id or self.suite_id
        return self._make_request('GET', f'get_suite/{sid}')

    def get_suites_for_project(self, project_id):
        """Get all test suites for a project."""
        return self._make_request('GET', f'get_suites/{project_id}')

    def test_connection(self):
        """Test the connection to TestRail."""
        try:
            suite = self.get_suite()
            if suite:
                logger.info(f"Successfully connected to TestRail suite: {suite.get('name')} (ID: {self.suite_id})")
                return True
            else:
                logger.error("Failed to connect to TestRail")
                return False
        except Exception as e:
            logger.error(f"Error testing TestRail connection: {e}")
            return False

