from enum import Enum
from typing import Dict, List, Optional

from fidesops.schemas.base_class import BaseSchema


class OneTrustSubtaskStatus(Enum):
    """Onetrust subtask status"""

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    REJECTED = "REJECTED"


class OneTrustSubtask(BaseSchema):
    """Onetrust subtask schema"""

    assignedToGroup: Optional[bool]
    requestApprover: Optional[str]
    requestOrgName: Optional[str]
    requestQueueDateCreated: Optional[str]
    requestQueueDeadline: Optional[str]
    requestQueueId: Optional[str]
    requestQueueRefId: Optional[str]
    requestTypes: Optional[List[str]]
    subTaskAssignee: Optional[str]
    subTaskCreatedDate: Optional[str]
    subTaskDeadline: Optional[str]
    subTaskDescription: Optional[str]
    subTaskId: Optional[str]
    subTaskLastUpdatedDate: Optional[str]
    subTaskName: Optional[str]
    subTaskReminderDate: Optional[str]
    subTaskRequired: Optional[bool]
    subTaskStatus: Optional[str]
    subTaskType: Optional[str]
    subTaskResolution: Optional[str]
    subjectTypes: Optional[List[str]]


class OneTrustGetSubtasksResponse(BaseSchema):
    """Response from OneTrust Get Subtasks endpoint"""

    content: List[OneTrustSubtask]
    first: Optional[bool]
    last: Optional[bool]
    number: Optional[int]
    numberOfElements: Optional[int]
    size: Optional[int]
    sort: Optional[Dict[str, str]]
    totalElements: Optional[int]
    totalPages: Optional[int]


class OneTrustRequest(BaseSchema):
    """Onetrust request schema"""

    approver: Optional[str]
    countryCode: Optional[str]
    countryName: Optional[str]
    dateCompleted: Optional[str]
    dateCreated: Optional[str]
    dateUpdated: Optional[str]
    deadline: Optional[str]
    email: Optional[str]
    firstName: Optional[str]
    isExtended: Optional[bool]
    language: Optional[str]
    lastName: Optional[str]
    organization: Optional[str]
    requestQueueId: Optional[str]
    requestQueueRefId: Optional[str]
    requestTypes: Optional[List[str]]
    resolution: Optional[str]
    status: Optional[str]
    subjectTypes: Optional[List[str]]
    webform: Optional[str]
    workflow: Optional[str]


class OneTrustGetRequestsResponse(BaseSchema):
    """Response from OneTrust Get Requests endpoint"""

    content: List[OneTrustRequest]
    first: Optional[bool]
    last: Optional[bool]
    number: Optional[int]
    numberOfElements: Optional[int]
    size: Optional[int]
    sort: Optional[Dict[str, str]]
    totalElements: Optional[int]
    totalPages: Optional[int]


class OneTrustOAuthResponse(BaseSchema):
    """Response from OneTrust Oauth token endpoint"""

    access_token: str
    token_type: str
    expires_in: int
    scope: str
    role: str
    user_name: str
    orgGroupId: str
    orgGroupGuid: str
    ot_scopes: str
    languageId: int
    tenantId: int
    guid: str
    sessionId: str
    tenantGuid: str
    email: str
    jti: str
