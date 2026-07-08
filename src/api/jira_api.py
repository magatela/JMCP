# jira_api.py
"""
Jira-API-Client.

Inherits from :class:`base_api.RestAPIClient` and implements only the
Jira-specific endpoints.
"""

from __future__ import annotations
from typing import Any, Dict
import json

from base_api import RestAPIClient


class JiraAPI(RestAPIClient):
    """
    Client for Jira Core.
    This class implements only the Jira-specific endpoints.
    Inherits from :class:`base_api.RestAPIClient`.
    """

    API_PATH = "rest/api/2/"

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
    # Util                                                            #
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

    # --------------------------------------------------------------- #
    # Endpoints                                                       #
    # --------------------------------------------------------------- #

    # GET
    def get_project_info(self):
        """         
        Retrieves detailed information for the configured project (based on prefix).
        :return: Response object of the GET request.
        """
        return self.get(f"{self.API_PATH}project/{self._prefix}")

    def get_issue_info(self, key: str):
        """
        Retrieves information for an issue.
        :param key: The key of the issue (with or without project prefix).
        :return: Response object of the GET request.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}")

    def get_changelogs(self, key: str):
        """     
        Retrieves the changelogs of an issue.
        :param key: The key of the issue (with or without project prefix).
        :return: Response object of the GET request.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/changelog")

    def check_issue_editable_fields(self, key: str):
        """
        Checks which fields of an issue can be edited.
        :param key: The key of the issue (with or without project prefix).
        :return: Response object of the GET request.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/editmeta")

    def get_all_fields(self):
        """
        Retrieves all available fields.
        :return: Response object of the GET request.
        """
        return self.get(f"{self.API_PATH}field")

    def get_field_reference_data(self):
        """
        Retrieves reference data for all fields.
        :return: Response object of the GET request.
        """
        return self.get(f"{self.API_PATH}jql/autocompletedata")

    def jql_requests(self, jql: str, max_results: int = 50):
        """
        Executes a JQL query and returns the results.
        :param jql: JQL query string.
        :param max_results: Maximum number of results (default: 50).
        :return: Response object of the GET request with the search results.
        """         
        return self.get(f"{self.API_PATH}search?jql={jql}&maxResults={max_results}")
    
    def get_bugs_linked_to_test(self, test_id: str):
        """
        Searches for bugs linked to a specific test case.
        :param test_id: The key of the test case.
        :return: Response object of the GET request with the found bugs.
        """
        jql = (
            f'issue in linkedIssues("{self.normalize_issue_key(test_id)}") '
            'AND issuetype = Bug'
        )
        return self.jql_requests(jql)

    def get_test_cases_in_project(self):
        """
        Retrieves all test cases (issues of type 'Test') in the currently configured project.
        :return: Response object of the GET request with the test cases.
        """
        jql = f'project = "{self._prefix}" AND issuetype = Test'
        return self.jql_requests(jql)

    def get_all_transitions(self, key: str):
        """
        Retrieves all possible transitions for a specific issue.
        :param key: The key of the issue (with or without project prefix).
        :return: Response object of the GET request with the transitions.
        """
        return self.get(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/transitions")
        
    # POST
    def create_issue(self, data: Dict[str, Any]):
        """
        Creates a new issue.
        :param data: The fields to be created in JSON format.
        :return: Response object of the POST request.
        """
        return self.post(f"{self.API_PATH}issue", data=data)

    def set_issue_transition(self, key: Any, data: Dict[str, Any]):
        """
        Performs a transition for an issue.
        :param key: The key of the issue.
        :param data: JSON payload with the transition ID.
                     Example: {'transition': {'id': '4'}}
                     (The ID depends on the configured workflow).
        :return: Response object of the POST request.
        """
        return self.post(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}/transitions", data=data)
    
    def set_issuelink(self, data):
        """
        Creates a link between two issues.
        :param data: JSON payload with link type and both issue keys (inward/outward).
                     Example:
                     {
                         "type": {"name": "Befund"},
                         "inwardIssue": {"key": "STORY-123"},
                         "outwardIssue": {"key": "TEST-456"}
                     }
        :return: Response object of the POST request.
        """
        return self.post(f"{self.API_PATH}issueLink", data=data)

    # PUT
    def update_issue(self, key: str, data: Dict[str, Any]):
        """
        Updates the fields of an existing issue.
        :param key: The key of the issue (with or without project prefix).
        :param data: The fields to be updated in JSON format.
        :return: Response object of the PUT request.
        """
        return self.put(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}", data=data)
    
    # DELETE
    def delete_issue(self, key: str):
        """
        Deletes an issue.
        :param key: The key of the issue (with or without project prefix).
        :return: Response object of the DELETE request.
        """
        return self.delete(f"{self.API_PATH}issue/{self.normalize_issue_key(key)}")
    
    # Miscellaneous
    def check_user_credentials(self):
        """
        Checks user credentials via a simple GET call to the API root.
        Returns the response object (status 200 → OK).
        """
        return self.get(self.API_PATH)


if __name__ == '__main__':
    pass
