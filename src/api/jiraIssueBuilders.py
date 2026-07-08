from enum import Enum
from typing import Dict, List, Any, Optional
import json
from abc import ABC, abstractmethod

class JiraIssueTypes(Enum):
    TEST = 'Test'
    TEST_EXECUTION = 'Test Execution'
    BUG = 'Bug'
    TEST_PLAN = 'Test Plan'
    NOT_A_TEST = 'NaT'

class CustomFields(Enum):
    EPIC_LINK = 'customfield_10101'
    TEST_PLAN_KEY = 'customfield_10231' 
    STAGE = 'customfield_10229'
    REVISION = 'customfield_10223'
    ORIGIN = 'customfield_20003' # Herkunft  {"value": "Entwicklung", "id": "520539",} {"value": "RZF", "id": "520538"}

class TransitionsIDTestExecution(Enum):
    IN_PROGRESS = 4
    SUCCESS = 5
    CLOSE = 2

class BugStatsuValues(Enum):
    ASSIGNED = 'Projekt zugewiesen' 
    DONE = 'Erledigt'
    REJECTED = 'Abgelehnt'
    ABORTED = 'Abgebrochen'

class JiraIssue:
    def __init__(self):
        self.fields = {}

    def toJson(self) -> Dict[str, Any]:
        return {"fields":self.fields}

    def toJsonString(self) -> str:
        return json.dumps(self.toJson(), indent=4, ensure_ascii=False)

class JiraIssueBuilder(ABC):
    def __init__(self):
        self.reset()
    
    def reset(self):
        self._jiraIssue = JiraIssue()
        return self

    def setProject(self, project:str) -> 'JiraIssueBuilder':
        self._jiraIssue.fields['project'] = {'key':project.strip()}
        return self
    
    def setSummary(self, summary:str) -> 'JiraIssueBuilder':
        self._jiraIssue.fields['summary'] = summary.strip()
        return self

    def setDescription(self, description:str) -> 'JiraIssueBuilder':
        self._jiraIssue.fields['description'] = description
        return self
    
    @abstractmethod
    def setIssuetype(self) -> 'JiraIssueBuilder':
        pass
       
    def setPriority(self, priority:str) -> 'JiraIssueBuilder':
        p = priority.strip()
        if p.isdigit():
            self._jiraIssue.fields['priority'] = {'id': p}
        else:
            self._jiraIssue.fields['priority'] = {'name': p}
        return self

    def setField(self, field_name: str, value: Any) -> 'JiraIssueBuilder':
        self._jiraIssue.fields[field_name] = value
        return self

    def setFixVersions(self, fixVersions:List[str]) -> 'JiraIssueBuilder':
        items = []
        for version in fixVersions:
            items.append({'name':version.strip()})
        self._jiraIssue.fields['fixVersions'] = items
        return self

    def setVersions(self, versions:List[str]) -> 'JiraIssueBuilder':
        items = []
        for version in versions:
            items.append({'name':version.strip()})
        self._jiraIssue.fields['versions'] = items
        return self
    
    def setAssignee(self, assignee:Optional[str]) -> 'JiraIssueBuilder':
        if assignee is None or assignee.strip() == "":
            self._jiraIssue.fields['assignee'] = None
        else:
            self._jiraIssue.fields['assignee'] = {'name': assignee.strip()}
        return self
    
    def setLabels(self, labels:List[str]) -> 'JiraIssueBuilder':
        self._jiraIssue.fields['labels'] = labels
        return self
    
    def setComponents(self, components:List[str]) -> 'JiraIssueBuilder':
        items = []
        for component in components:
            items.append({'name':component.strip()})
        self._jiraIssue.fields['components'] = items
        return self
    
    def setEpicLink(self, epiclink:str) -> 'JiraIssueBuilder':
        self._jiraIssue.fields[CustomFields.EPIC_LINK.value] = epiclink
        return self
    
    def setTestPlan(self, testplan:str) -> 'JiraIssueBuilder':
        self._jiraIssue.fields[CustomFields.TEST_PLAN_KEY.value] = testplan
        return self
    
    def setStage(self, stage:str) -> 'JiraIssueBuilder':
        self._jiraIssue.fields[CustomFields.STAGE.value] = stage
        return self
    
    def setRevision(self, revision:str) -> 'JiraIssueBuilder':
        self._jiraIssue.fields[CustomFields.REVISION.value] = revision
        return self
    
    def setOrigin(self, origin:str) -> 'JiraIssueBuilder':
        self._jiraIssue.fields[CustomFields.ORIGIN.value] = {'id':origin}
        return self
    
    def build(self) -> Dict[str, Any]:
        return self._jiraIssue.toJson()
    
    def toString(self) -> str:
        return self._jiraIssue.toJsonString()
    
class TestExecutionBuilder(JiraIssueBuilder):
    def __init__(self):
        super().__init__()
    
    def setIssuetype(self) -> 'TestExecutionBuilder':
        self._jiraIssue.fields['issuetype'] = {'name': JiraIssueTypes.TEST_EXECUTION.value }
        return self

class TestCaseBuilder(JiraIssueBuilder):
    def __init__(self):
        super().__init__()
    
    def setIssuetype(self) -> 'TestCaseBuilder':
        self._jiraIssue.fields['issuetype'] = {'name': JiraIssueTypes.TEST.value }
        return self

class BugBuilder(JiraIssueBuilder):
    def __init__(self):
        super().__init__()
    
    def setIssuetype(self) -> 'BugBuilder':
        self._jiraIssue.fields['issuetype'] = {'name': JiraIssueTypes.BUG.value }
        return self

class GenericIssueBuilder(JiraIssueBuilder):
    def __init__(self, issuetype: str):
        self._issuetype = issuetype
        super().__init__()
    
    def setIssuetype(self) -> 'GenericIssueBuilder':
        if self._issuetype:
            self._jiraIssue.fields['issuetype'] = {'name': self._issuetype.strip()}
        return self

def get_builder_for_type(issuetype: str) -> JiraIssueBuilder:
    issuetype_lower = issuetype.lower().strip()
    if issuetype_lower == 'test':
        return TestCaseBuilder().setIssuetype()
    elif issuetype_lower == 'test execution':
        return TestExecutionBuilder().setIssuetype()
    elif issuetype_lower == 'bug':
        return BugBuilder().setIssuetype()
    else:
        return GenericIssueBuilder(issuetype).setIssuetype()

DEFAULT_GET_FIELDS = [
    "project",
    "summary",
    "description",
    "issuetype",
    "priority",
    "status",
    "assignee",
    "labels",
    "components",
    "fixVersions",
    "versions",
    "created",
    "updated",
    CustomFields.EPIC_LINK.value,
    CustomFields.TEST_PLAN_KEY.value,
    CustomFields.STAGE.value,
    CustomFields.REVISION.value,
    CustomFields.ORIGIN.value
]

class TestExecutionTransitionBuilder:
    def __init__(self):
        self.transitionID = {'id':None}
    
    def setClose(self):
        self.transitionID['id'] = TransitionsIDTestExecution.CLOSE.value
        return self
    
    def setSuccess(self):
        self.transitionID['id'] = TransitionsIDTestExecution.SUCCESS.value
        return self
    
    def setInProgress(self):
        self.transitionID['id'] = TransitionsIDTestExecution.IN_PROGRESS.value
        return self
    
    def build(self):
        return {'transition':self.transitionID}