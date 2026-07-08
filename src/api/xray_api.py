# xray_api.py
"""
Xray-API-Client (Test management plugin for Jira).

Here too: only Xray-specific endpoints, everything else
comes from :class:`base_api.RestAPIClient`.
"""

from __future__ import annotations
from typing import Any, Dict
from base_api import RestAPIClient


class XrayAPI(RestAPIClient):
    """Client for Xray (Raven)."""

    # Xray uses several different REST resources
    RAVEN = "rest/raven/1.0/"
    RAVEN_API = "rest/raven/1.0/api/"
    RAVEN_API_V2 = "rest/raven/2.0/api/"

    def __init__(
        self,
        base_url: str,
        prefix: str,
        user: str,
        password: str,
        *,
        proxies=None,
    ) -> None:
        super().__init__(base_url, user, password, proxies=proxies)
        self._prefix = prefix

    # --------------------------------------------------------------- #
    # Test Steps                                                      #
    # --------------------------------------------------------------- #
    def normalize_issue_key(self, key: str) -> str:
        """
        Normalizes the passed issue key.
        Adds the project prefix if it is not already present.
        
        :param key: The original issue key (with or without prefix).
        :return: The full issue key (e.g. "PROJ-123").
        """
        issueKey = f'{key}'
        if not issueKey.startswith(self._prefix):
            issueKey = f'{self._prefix}-{issueKey}'
        return issueKey

    def get_test_steps(self, test_id: str):
        """
        Retrieves all test steps of a test case.
        :param test_id: The key of the test case.
        :return: Response object of the GET request.
        """
        return self.get(f"{self.RAVEN_API_V2}test/{self.normalize_issue_key(test_id)}/steps")

    def delete_step(self, test_id: str, step_id: str):
        """
        Deletes a specific test step from a test case.
        :param test_id: The key of the test case.
        :param step_id: The ID of the step to delete.
        :return: Response object of the DELETE request.
        """
        return self.delete(
            f"{self.RAVEN_API_V2}test/{self.normalize_issue_key(test_id)}/steps/{step_id}"
        )

    def add_test_step(self, test_id: str, data: dict):
        """
        Adds a new test step to a test case.
        :param test_id: The key of the test case.
        :param data: JSON payload with the data of the new test step.
        :return: Response object of the PUT request.
        """
        return self.put(f"{self.RAVEN_API}test/{self.normalize_issue_key(test_id)}/step", data)
    
    # --------------------------------------------------------------- #
    # Test Executions                                                 #
    # --------------------------------------------------------------- #
    def get_all_test_executions(self, test_id: str):
        """
        Retrieves all test executions (Test Executions) linked to a test case.
        :param test_id: The key of the test case.
        :return: Response object of the GET request.
        """
        return self.get(
            f"{self.RAVEN_API}test/{self.normalize_issue_key(test_id)}/testexecutions"
        )
    
    def get_test_run_results(self, test_id: str):
        """
        Retrieves test run results for a specific test case.
        :param test_id: The key of the test case.
        :return: Response object of the GET request.
        """
        return self.get(
            f"{self.RAVEN_API}test/{self.normalize_issue_key(test_id)}/testexecutions"
        )

    def add_test_to_test_execution(self, execution_id: str, data: Dict[str, Any]):
        """
        Adds tests to a test execution (Test Execution).
        
        :param execution_id: The key of the test execution.
        :param data: JSON payload with the test keys to add.
                     Example: {"add": ["QTD-41", "QTD-40"]}
        :return: Response object of the POST request.
        """
        return self.post(f"{self.RAVEN_API}testexec/{self.normalize_issue_key(execution_id)}/test", data=data)

    # --------------------------------------------------------------- #
    # Test Sets & Plans                                               #
    # --------------------------------------------------------------- #
    def add_test_to_test_set(self, test_set_id: str, data: Dict[str, Any]):
        """
        Adds tests to a test set.
        :param test_set_id: The key of the test set.
        :param data: JSON payload with the test keys to add.
                     Example: {"add": ["QTD-41"]}
        :return: Response object of the POST request.
        """
        return self.post(
            f"{self.RAVEN_API}testset/{self.normalize_issue_key(test_set_id)}/test", data=data
        )

    def edit_tests_in_plan(self, test_plan_id: str, data: Dict[str, Any]):
        """
        Adds tests to or removes tests from a test plan.

        Example ``data``::

            {
                "add": ["PDNEU-14"],
                "remove": ["PDNEU-42"]
            }
            
        :param test_plan_id: The key of the test plan.
        :param data: JSON payload with the test keys to add/remove.
        :return: Response object of the POST request.
        """
        return self.post(
            f"{self.RAVEN_API}testplan/{self.normalize_issue_key(test_plan_id)}/test",
            data=data,
        )

    def get_testplan_tables(self):
        """
        Retrieves the folder structure (Test Repository) of a project.
        :return: Response object of the GET request.
        """
        return self.get(f"{self.RAVEN_API}testrepository/{self._prefix}/folders")

    def get_test_from_folder(self, folder_id):
        """
        Retrieves all tests from a specific folder in the Test Repository.
        :param folder_id: The ID of the folder.
        :return: Response object of the GET request.
        """
        return self.get(f"{self.RAVEN_API}testrepository/{self._prefix}/folders/{folder_id}/tests")
    
    def get_all_test_from_testplan(self, test_plan_id: str, limit=200, page=1):
        """
        Retrieves all tests assigned to a test plan (with pagination).
        :param test_plan_id: The key of the test plan.
        :param limit: Maximum number of tests per page (default: 200).
        :param page: The page to retrieve (default: 1).
        :return: Response object of the GET request.
        """
        params = {'limit': limit, 'page': page}
        return self.get(
            f"{self.RAVEN_API}testplan/{self.normalize_issue_key(test_plan_id)}/test", params=params)

    # --------------------------------------------------------------- #
    # Test Run                                                        #
    # --------------------------------------------------------------- #
    def update_testrun(self, testrun_id, data):
        """
        Updates the data of a specific test run (e.g. change status).
        :param testrun_id: The ID of the test run.
        :param data: JSON payload with the data to update.
        :return: Response object of the PUT request.
        """
        return self.put(
            f'{self.RAVEN_API_V2}testrun/{testrun_id}', data
        )
    
    def get_test_run_data(self, execution_id: str, test_id: str):
        """
        Retrieves the data of a test run belonging to a specific execution and a test.
        :param execution_id: The key of the test execution (Test Execution).
        :param test_id: The key of the test case.
        :return: Response object of the GET request.
        """
        return self.get(
            f"{self.RAVEN_API}testrun?"
            f"testExecIssueKey={self.normalize_issue_key(execution_id)}"
            f"&testIssueKey={self.normalize_issue_key(test_id)}"
        )
    
    def get_test_run_data_by_id(self, testrun_id: str):
        """
        Retrieves detailed data of a test run by its ID, including iterations.
        :param testrun_id: The ID of the test run.
        :return: Response object of the GET request.
        """
        return self.get(
            f"{self.RAVEN_API_V2}testrun/{testrun_id}?includeiterations=true"
        )
    
    def get_test_run_id(self, execution_id: str, test_id: str):
        """
        Helper method to retrieve the ID of a test run from execution and test.
        :param execution_id: The key of the test execution.
        :param test_id: The key of the test case.
        :return: The ID of the test run (int/str) or None if not found.
        """
        response = self.get_test_run_data(execution_id, test_id)
        if response.ok:
            return response.json().get('id')
        return None

    def read_test_run_comment(self, execution_id: str, test_id: str):
        """
        Helper method to read the comment of a specific test run.
        :param execution_id: The key of the test execution.
        :param test_id: The key of the test case.
        :return: The comment text or None if not found.
        """
        response = self.get_test_run_data(execution_id, test_id)
        if response.ok:
            return response.json().get('comment')
        return None
    
    def upload_results(self, data):
        """
        Uploads test results (e.g. from automated tests) to Xray.
        :param data: Payload with the execution results.
        :return: Boolean (True if the upload was successful, otherwise False).
        """
        response = self.post(f'{self.RAVEN}import/execution', data)
        return response.ok


if __name__ == '__main__':
    pass