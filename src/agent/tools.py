# tools.py
"""
Defines LangChain tools for interacting with Jira and Xray.
Uses a factory pattern to inject JiraAPI and XrayAPI instances.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool, BaseTool

# Ensure the src/api directory is in path to import base_api, jira_api, and xray_api
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
api_dir = os.path.join(parent_dir, "api")
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from jira_api import JiraAPI
from xray_api import XrayAPI
from jiraIssueBuilders import (
    get_builder_for_type,
    GenericIssueBuilder,
    CustomFields,
    DEFAULT_GET_FIELDS,
)

def get_jira_tools(jira: JiraAPI, xray: Optional[XrayAPI] = None) -> List[BaseTool]:
    """
    Returns the list of LangChain tools bound to the API clients.
    """

    @tool
    def get_project_info() -> str:
        """
        Retrieves general information and configuration of the current Jira project.
        """
        response = jira.get_project_info()
        if response.ok:
            return response.text
        return f"Error retrieving project information: {response.status_code} - {response.text}"

    @tool
    def get_issue_info(key: str, fields: Optional[List[str]] = None) -> str:
        """
        Retrieves all details, fields, and status of a specific issue in Jira by its key (e.g., 'PROJ-123' or just '123').
        Parameters:
        - key: The issue key.
        - fields: Optional list of fields to return (to save tokens). By default, returns the most
          common and important fields (summary, description, status, assignee, priority, issuetype, labels, etc., and custom fields).
          Pass ["*"] or ["all"] if you want to retrieve absolutely all available fields.
        """
        query_fields = fields
        if query_fields is None:
            query_fields = DEFAULT_GET_FIELDS
        elif len(query_fields) == 1 and query_fields[0].strip().lower() in ("*", "all"):
            query_fields = None

        response = jira.get_issue_info(key, fields=query_fields)
        if response.ok:
            return response.text
        return f"Error retrieving issue information for {key}: {response.status_code} - {response.text}"

    @tool
    def get_issue_changelogs(key: str) -> str:
        """
        Retrieves the change logs (changelogs) of a Jira issue by its key.
        """
        response = jira.get_changelogs(key)
        if response.ok:
            return response.text
        return f"Error retrieving changelogs for issue {key}: {response.status_code} - {response.text}"

    @tool
    def check_issue_editable_fields(key: str) -> str:
        """
        Checks which fields of a specific issue are editable in its current status.
        """
        response = jira.check_issue_editable_fields(key)
        if response.ok:
            return response.text
        return f"Error checking editable fields for {key}: {response.status_code} - {response.text}"

    @tool
    def get_all_fields() -> str:
        """
        Retrieves the list of all available fields in the Jira instance (both system and custom fields).
        """
        response = jira.get_all_fields()
        if response.ok:
            return response.text
        return f"Error retrieving all fields: {response.status_code} - {response.text}"

    @tool
    def jql_search(query: str, max_results: int = 50, fields: Optional[List[str]] = None) -> str:
        """
        Performs an issue search using JQL (Jira Query Language).
        Query example: 'project = "PROJ" AND status = "To Do" AND assignee = currentUser()'
        Parameters:
        - query: The JQL query string.
        - max_results: Maximum number of results to return (default is 50).
        - fields: Optional list of fields to return (to save tokens). By default, returns the most
          common and important fields. Pass ["*"] or ["all"] if you want to retrieve absolutely all fields.
        """
        query_fields = fields
        if query_fields is None:
            query_fields = DEFAULT_GET_FIELDS
        elif len(query_fields) == 1 and query_fields[0].strip().lower() in ("*", "all"):
            query_fields = None

        response = jira.jql_requests(query, max_results=max_results, fields=query_fields)
        if response.ok:
            return response.text
        return f"Error executing JQL search: {response.status_code} - {response.text}"

    @tool
    def get_bugs_linked_to_test(test_id: str) -> str:
        """
        Searches for bugs linked to a specific test case.
        """
        response = jira.get_bugs_linked_to_test(test_id)
        if response.ok:
            return response.text
        return f"Error searching for bugs associated with test {test_id}: {response.status_code} - {response.text}"

    @tool
    def get_test_cases_in_project() -> str:
        """
        Retrieves all test cases (issues of type 'Test') in the configured project.
        """
        response = jira.get_test_cases_in_project()
        if response.ok:
            return response.text
        return f"Error retrieving test cases: {response.status_code} - {response.text}"

    @tool
    def get_issue_transitions(key: str) -> str:
        """
        Retrieves the available destination statuses (transitions) for an issue.
        Returns the transition IDs and names.
        """
        response = jira.get_all_transitions(key)
        if response.ok:
            return response.text
        return f"Error retrieving transitions for {key}: {response.status_code} - {response.text}"

    @tool
    def create_jira_issue(
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Test",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        fix_versions: Optional[List[str]] = None,
        versions: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Creates a new issue in the configured Jira project in a highly flexible way using builders.
        Parameters:
        - summary: The title/summary of the issue.
        - description: The detailed description of the issue. Optional.
        - issue_type: The issue type (e.g., 'Test', 'Test Execution', 'Bug', 'Task', 'Story'). Default is 'Test'.
        - priority: The priority (e.g., 'High', 'Medium', 'Low', or a numeric ID). Optional.
        - assignee: Username of the assignee. Optional.
        - labels: List of labels (e.g., ['tag1', 'tag2']). Optional.
        - components: List of component names. Optional.
        - fix_versions: List of fix versions (fixVersions). Optional.
        - versions: List of affected versions (versions). Optional.
        - custom_fields: Optional dictionary of custom fields (e.g., {'epic_link': 'PROJ-12', 'test_plan': 'PROJ-34'}).
          Automatically maps common keys to CustomFields enum values (epic_link, test_plan, stage, revision, origin).
        """
        builder = get_builder_for_type(issue_type)
        builder.setProject(jira._prefix)
        builder.setSummary(summary)
        if description:
            builder.setDescription(description)
        if priority:
            builder.setPriority(priority)
        if assignee:
            builder.setAssignee(assignee)
        if labels:
            builder.setLabels(labels)
        if components:
            builder.setComponents(components)
        if fix_versions:
            builder.setFixVersions(fix_versions)
        if versions:
            builder.setVersions(versions)

        if custom_fields:
            for k, val in custom_fields.items():
                k_lower = k.lower().strip()
                if k_lower in ("epic_link", CustomFields.EPIC_LINK.value):
                    builder.setEpicLink(val)
                elif k_lower in ("test_plan", CustomFields.TEST_PLAN_KEY.value):
                    builder.setTestPlan(val)
                elif k_lower in ("stage", CustomFields.STAGE.value):
                    builder.setStage(val)
                elif k_lower in ("revision", CustomFields.REVISION.value):
                    builder.setRevision(val)
                elif k_lower in ("origin", CustomFields.ORIGIN.value):
                    builder.setOrigin(val)
                else:
                    builder.setField(k, val)

        data = builder.build()
        response = jira.create_issue(data)
        if response.ok:
            return f"Issue created successfully:\n{response.text}"
        return f"Error creating issue: {response.status_code} - {response.text}"

    @tool
    def transition_jira_issue(key: str, transition_id: str) -> str:
        """
        Changes the status of a Jira issue (transition).
        You should use get_issue_transitions beforehand to know the corresponding transition ID.
        """
        data = {"transition": {"id": transition_id}}
        response = jira.set_issue_transition(key, data)
        if response.ok:
            return f"Issue {key} successfully transitioned to transition ID {transition_id}."
        return f"Error transitioning issue {key}: {response.status_code} - {response.text}"

    @tool
    def link_jira_issues(inward_key: str, outward_key: str, link_type_name: str = "Befund") -> str:
        """
        Creates a link between two Jira issues.
        Example: Link a Story with a Test, or a Bug with a Story.
        Parameters:
        - inward_key: Destination issue key.
        - outward_key: Source issue key.
        - link_type_name: Link type name. Default is 'Befund'.
        """
        data = {
            "type": {"name": link_type_name},
            "inwardIssue": {"key": jira.normalize_issue_key(inward_key)},
            "outwardIssue": {"key": jira.normalize_issue_key(outward_key)}
        }
        response = jira.set_issuelink(data)
        if response.ok:
            return f"Link of type '{link_type_name}' created successfully between {inward_key} and {outward_key}."
        return f"Error creating link: {response.status_code} - {response.text}"

    @tool
    def update_jira_issue(
        key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        fix_versions: Optional[List[str]] = None,
        versions: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Updates the fields of a Jira issue in a highly flexible way using builders.
        Note: Use transition_jira_issue to change the issue status.
        Parameters:
        - key: The issue key.
        - summary: New title. Optional.
        - description: New description. Optional.
        - priority: New priority. Optional.
        - assignee: Assignee username. Pass an empty string or None to unassign. Optional.
        - labels: List of new labels. Optional.
        - components: List of components. Optional.
        - fix_versions: List of fix versions. Optional.
        - versions: List of affected versions. Optional.
        - custom_fields: Optional dictionary of custom fields to update.
        """
        builder = GenericIssueBuilder("")
        
        if summary is not None:
            builder.setSummary(summary)
        if description is not None:
            builder.setDescription(description)
        if priority is not None:
            builder.setPriority(priority)
        if assignee is not None:
            builder.setAssignee(assignee)
        if labels is not None:
            builder.setLabels(labels)
        if components is not None:
            builder.setComponents(components)
        if fix_versions is not None:
            builder.setFixVersions(fix_versions)
        if versions is not None:
            builder.setVersions(versions)

        if custom_fields:
            for k, val in custom_fields.items():
                k_lower = k.lower().strip()
                if k_lower in ("epic_link", CustomFields.EPIC_LINK.value):
                    builder.setEpicLink(val)
                elif k_lower in ("test_plan", CustomFields.TEST_PLAN_KEY.value):
                    builder.setTestPlan(val)
                elif k_lower in ("stage", CustomFields.STAGE.value):
                    builder.setStage(val)
                elif k_lower in ("revision", CustomFields.REVISION.value):
                    builder.setRevision(val)
                elif k_lower in ("origin", CustomFields.ORIGIN.value):
                    builder.setOrigin(val)
                else:
                    builder.setField(k, val)

        data = builder.build()
        if not data.get("fields"):
            return "No fields specified for update."

        response = jira.update_issue(key, data)
        if response.ok:
            return f"Issue {key} updated successfully."
        return f"Error updating issue {key}: {response.status_code} - {response.text}"

    @tool
    def delete_jira_issue(key: str) -> str:
        """
        Deletes a Jira issue by its key. Use with caution.
        """
        response = jira.delete_issue(key)
        if response.ok:
            return f"Issue {key} deleted successfully."
        return f"Error deleting issue {key}: {response.status_code} - {response.text}"

    # Basic Jira Core tools list
    tools_list = [
        get_project_info,
        get_issue_info,
        get_issue_changelogs,
        check_issue_editable_fields,
        get_all_fields,
        jql_search,
        get_bugs_linked_to_test,
        get_test_cases_in_project,
        get_issue_transitions,
        create_jira_issue,
        transition_jira_issue,
        link_jira_issues,


        
        update_jira_issue,
    ]

    # Add Xray tools if client is provided
    if xray is not None:
        @tool
        def xray_get_test_steps(test_id: str) -> str:
            """
            [XRAY] Retrieves detailed test steps of a specific test case (Test).
            """
            response = xray.get_test_steps(test_id)
            if response.ok:
                return response.text
            return f"Error retrieving test steps for {test_id}: {response.status_code} - {response.text}"

        @tool
        def xray_add_test_step(test_id: str, step: str, data: str, result: str) -> str:
            """
            [XRAY] Adds a test step to a Test.
            Parameters:
            - test_id: Key of the Test.
            - step: Step action description.
            - data: Input data for the step.
            - result: Expected result of the step.
            """
            payload = {
                "step": step,
                "data": data,
                "result": result
            }
            response = xray.add_test_step(test_id, payload)
            if response.ok:
                return f"Step successfully added to Test {test_id}."
            return f"Error adding step to Test {test_id}: {response.status_code} - {response.text}"

        @tool
        def xray_delete_test_step(test_id: str, step_id: str) -> str:
            """
            [XRAY] Deletes a specific test step from a Test.
            """
            response = xray.delete_step(test_id, step_id)
            if response.ok:
                return f"Step {step_id} of Test {test_id} successfully deleted."
            return f"Error deleting step {step_id}: {response.status_code} - {response.text}"

        @tool
        def xray_get_all_test_executions(test_id: str) -> str:
            """
            [XRAY] Retrieves the list of all test executions associated with a Test.
            """
            response = xray.get_all_test_executions(test_id)
            if response.ok:
                return response.text
            return f"Error retrieving test executions for {test_id}: {response.status_code} - {response.text}"

        @tool
        def xray_get_test_run_results(test_id: str) -> str:
            """
            [XRAY] Retrieves the test run results associated with a Test.
            """
            response = xray.get_test_run_results(test_id)
            if response.ok:
                return response.text
            return f"Error retrieving test run results for {test_id}: {response.status_code} - {response.text}"

        @tool
        def xray_add_test_to_execution(execution_id: str, test_keys: List[str]) -> str:
            """
            [XRAY] Adds a list of test keys (e.g., ['PROJ-101', 'PROJ-102']) to a test execution.
            """
            payload = {"add": test_keys}
            response = xray.add_test_to_test_execution(execution_id, payload)
            if response.ok:
                return f"Tests {test_keys} successfully added to execution {execution_id}."
            return f"Error adding tests to execution {execution_id}: {response.status_code} - {response.text}"

        @tool
        def xray_update_testrun_status(testrun_id: str, status: str) -> str:
            """
            [XRAY] Updates the status of a test run by its ID.
            The status must be one of the configured values (e.g., 'PASS', 'FAIL', 'TODO', 'EXECUTING').
            """
            payload = {"status": status}
            response = xray.update_testrun(testrun_id, payload)
            if response.ok:
                return f"Test Run {testrun_id} status updated to {status}."
            return f"Error updating Test Run {testrun_id} status: {response.status_code} - {response.text}"

        @tool
        def xray_get_testrun_data(execution_id: str, test_id: str) -> str:
            """
            [XRAY] Retrieves detailed data of a specific Test Run given the execution key and Test ID.
            """
            response = xray.get_test_run_data(execution_id, test_id)
            if response.ok:
                return response.text
            return f"Error retrieving Test Run data: {response.status_code} - {response.text}"

        @tool
        def xray_get_testrun_data_by_id(testrun_id: str) -> str:
            """
            [XRAY] Retrieves detailed data of a Test Run by its ID, including iterations and steps if applicable.
            """
            response = xray.get_test_run_data_by_id(testrun_id)
            if response.ok:
                return response.text
            return f"Error retrieving Test Run {testrun_id} data: {response.status_code} - {response.text}"

        @tool
        def xray_upload_results(payload: Dict[str, Any]) -> str:
            """
            [XRAY] Imports/uploads automated test results to Xray using Xray's execution JSON format.
            """
            success = xray.upload_results(payload)
            if success:
                return "Test results imported successfully to Xray."
            return "Error importing test results to Xray."

        # Add tools to the list
        tools_list.extend([
            xray_get_test_steps,
            xray_add_test_step,
            xray_delete_test_step,
            xray_get_all_test_executions,
            xray_get_test_run_results,
            xray_add_test_to_execution,
            xray_update_testrun_status,
            xray_get_testrun_data,
            xray_get_testrun_data_by_id,
            xray_upload_results
        ])

    return tools_list
