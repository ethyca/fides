# Jira Integration Setup Requirements

This document outlines the complete setup requirements for implementing a production-ready Jira integration in Fides.

## 🎯 **Overview**

The Jira integration automatically creates and manages tickets for Data Subject Requests (DSRs) and other privacy compliance tasks, providing:

- **Automated ticket creation** for incoming DSRs
- **Templating system** with variable substitution and date math
- **Workflow integration** with Fides privacy request lifecycle
- **Custom field mapping** for Jira-specific requirements
- **Status synchronization** between Fides and Jira

## 🛠️ **Frontend Components (✅ Completed)**

### **1. Integration Tile**
- ✅ Jira tile in Settings > Integrations > Add Integration
- ✅ Logo, description, tags ("DSR", "Automated tasks")
- ✅ "Task Management" category

### **2. Configuration UI**
- ✅ `JiraConfigurationForm.tsx` - Complete form with all fields
- ✅ `templateEngine.ts` - Template processing with date math
- ✅ Template variable system with preview functionality

## 🔧 **Backend Implementation Requirements**

### **1. Database Schema Changes**

#### **Connection Configuration**
```sql
-- Add JIRA to connection_type enum
ALTER TYPE connectiontype ADD VALUE 'jira';

-- Jira-specific configuration fields in connection_config table
ALTER TABLE connectionconfig ADD COLUMN jira_config JSONB;
```

#### **Jira Configuration Schema**
```typescript
interface JiraConfig {
  instanceUrl: string;
  authType: 'api_token' | 'oauth2';
  projectKey: string;
  issueType: string;
  defaultPriority?: string;
  defaultAssignee?: string;
  defaultLabels?: string[];

  // Templates
  titleTemplate: string;
  descriptionTemplate: string;
  dueDateFormula: string;

  // Custom field mappings
  customFields?: {
    dataSubjectField?: string;
    requestTypeField?: string;
    fidesLinkField?: string;
    [key: string]: string;
  };
}
```

### **2. API Endpoints**

#### **Configuration Management**
```typescript
// POST /api/v1/connections (extended for Jira)
interface CreateJiraConnectionRequest {
  name: string;
  connection_type: 'jira';
  jira_config: JiraConfig;
  secrets: {
    username: string;
    api_token: string; // or OAuth tokens
  };
}

// Test connection endpoint
// POST /api/v1/connections/{id}/test
// Returns: { success: boolean, error?: string, project_info?: object }
```

#### **Template Processing**
```typescript
// POST /api/v1/integrations/jira/template/preview
interface TemplatePreviewRequest {
  template: string;
  context?: Partial<DSRContext>;
}

// POST /api/v1/integrations/jira/template/validate
interface TemplateValidateRequest {
  template: string;
}
```

### **3. Jira API Client**

#### **Authentication Handler**
```python
class JiraAuthHandler:
    def __init__(self, config: JiraConfig, secrets: dict):
        self.instance_url = config.instance_url
        self.auth_type = config.auth_type
        self.secrets = secrets

    def get_authenticated_client(self) -> JiraClient:
        if self.auth_type == 'api_token':
            return JiraClient(
                server=self.instance_url,
                basic_auth=(self.secrets['username'], self.secrets['api_token'])
            )
        # TODO: OAuth2 implementation
```

#### **Ticket Operations**
```python
class JiraTicketManager:
    def create_dsr_ticket(self, dsr_context: DSRContext, config: JiraConfig) -> str:
        """Create a Jira ticket for a DSR. Returns ticket ID."""

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update ticket status based on DSR progress."""

    def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add a comment to the ticket."""

    def get_ticket_info(self, ticket_id: str) -> dict:
        """Get current ticket information."""
```

### **4. Template Engine Backend**

#### **Template Processor**
```python
class JiraTemplateProcessor:
    def process_template(self, template: str, context: DSRContext) -> str:
        """Process template with variable substitution and date math."""

    def validate_template(self, template: str) -> List[str]:
        """Validate template syntax and return errors."""

    def get_available_variables(self) -> List[dict]:
        """Return list of available template variables."""
```

## 🔄 **Workflow Integration**

### **1. Privacy Request Lifecycle Hooks**

#### **Request Created**
```python
@privacy_request_created.connect
def create_jira_ticket(sender, privacy_request, **kwargs):
    """Create Jira ticket when DSR is submitted."""
    jira_connections = get_active_jira_connections()

    for connection in jira_connections:
        try:
            ticket_id = create_dsr_ticket(privacy_request, connection)
            store_ticket_reference(privacy_request.id, ticket_id, connection.id)
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
```

#### **Status Updates**
```python
@privacy_request_status_changed.connect
def update_jira_ticket_status(sender, privacy_request, old_status, new_status, **kwargs):
    """Update Jira ticket when DSR status changes."""
    tickets = get_jira_tickets_for_request(privacy_request.id)

    for ticket in tickets:
        update_ticket_status(ticket.jira_id, map_status_to_jira(new_status))

        if new_status == PrivacyRequestStatus.COMPLETE:
            add_completion_comment(ticket.jira_id, privacy_request)
```

### **2. Status Mapping**

```python
FIDES_TO_JIRA_STATUS_MAP = {
    PrivacyRequestStatus.PENDING: "To Do",
    PrivacyRequestStatus.IN_PROCESSING: "In Progress",
    PrivacyRequestStatus.PAUSED: "On Hold",
    PrivacyRequestStatus.COMPLETE: "Done",
    PrivacyRequestStatus.CANCELED: "Canceled",
    PrivacyRequestStatus.ERROR: "Failed",
}
```

### **3. Database Tracking**

```sql
-- Track Jira tickets associated with privacy requests
CREATE TABLE jira_ticket_references (
    id SERIAL PRIMARY KEY,
    privacy_request_id VARCHAR NOT NULL REFERENCES privacyrequest(id),
    jira_connection_id VARCHAR NOT NULL REFERENCES connectionconfig(key),
    jira_ticket_id VARCHAR NOT NULL,
    jira_ticket_url VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(privacy_request_id, jira_connection_id)
);
```

## 🧪 **Configuration Examples**

### **1. Basic DSR Template**
```typescript
// Title Template
"DSR Request: {{request-type}} for {{data-subject}}"

// Description Template
`# Data Subject Request

**Request Details:**
- **Type:** {{request-type}}
- **Subject:** {{data-subject}} ({{subject-name}})
- **Submitted:** {{request-date}}
- **Request ID:** {{request-id}}

**Fides Dashboard:** {{fides-dsr-link}}

**Due Date:** {{due-date}}

---

**Next Steps:**
1. Review request details
2. Verify data subject identity
3. Process request across systems
4. Provide response to data subject

**Contact:** {{privacy-team}} for questions`

// Due Date Formula
"{{today}}+45"  // 45 days from today
```

### **2. Advanced Template with Custom Fields**
```typescript
{
  titleTemplate: "GDPR {{request-type}} - {{data-subject}} - Due {{due-date}}",
  descriptionTemplate: "...", // Full template
  dueDateFormula: "{{due-date}}-7", // 7 days before legal deadline
  customFields: {
    "customfield_10001": "{{data-subject}}", // Data Subject Email
    "customfield_10002": "{{request-type}}", // Request Type
    "customfield_10003": "{{fides-dsr-link}}", // Fides Link
    "customfield_10004": "{{regulation}}", // Regulation
  }
}
```

## 🔒 **Security Requirements**

### **1. Credential Management**
- Store API tokens in encrypted secrets store
- Support for credential rotation
- Audit logging for all Jira API calls

### **2. Data Privacy**
- Ensure templates don't expose sensitive data unnecessarily
- Configurable data masking for ticket content
- Compliance with data retention policies

### **3. Access Control**
- Role-based access to Jira configuration
- Separate permissions for template management
- Audit trail for configuration changes

## 📋 **Testing Strategy**

### **1. Unit Tests**
- Template engine with various date math scenarios
- Jira API client error handling
- Configuration validation

### **2. Integration Tests**
- End-to-end DSR workflow with Jira ticket creation
- Status synchronization between Fides and Jira
- Template processing with real DSR data

### **3. Manual Testing Scenarios**
1. Configure Jira integration with test instance
2. Submit various types of DSRs
3. Verify ticket creation with correct templates
4. Test status updates and completion flow
5. Validate custom field mappings

## 🚀 **Implementation Phases**

### **Phase 1: Core Integration**
- [ ] Backend API endpoints
- [ ] Jira API client
- [ ] Basic ticket creation
- [ ] UI integration with existing form

### **Phase 2: Template System**
- [ ] Template engine backend
- [ ] Variable substitution
- [ ] Date math operations
- [ ] Preview functionality

### **Phase 3: Workflow Integration**
- [ ] Privacy request lifecycle hooks
- [ ] Status synchronization
- [ ] Custom field mapping
- [ ] Error handling and retries

### **Phase 4: Advanced Features**
- [ ] OAuth2 authentication
- [ ] Bulk operations
- [ ] Reporting and analytics
- [ ] Advanced template features

## 🔗 **Dependencies**

### **Python Packages**
```bash
pip install jira  # Official Atlassian JIRA Python library
pip install python-dateutil  # For date math operations
```

### **Environment Configuration**
```env
# Feature flag
ENABLE_JIRA_INTEGRATION=true

# Default settings
DEFAULT_JIRA_TICKET_PRIORITY=Medium
DEFAULT_JIRA_DUE_DAYS=45
```

This comprehensive setup would provide a robust, production-ready Jira integration that automatically manages tickets for privacy requests with full templating and workflow capabilities.
