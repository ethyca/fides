## Manual Tasks

### 1. GET `/api/v1/manual-tasks/`
**Description:** Get paginated list of manual tasks

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `size` (optional): Page size (default: 10)
- `search` (optional): Search term for filtering by name or description
- `status` (optional): Filter by status ("new", "skipped", "completed")
- `request_type` (optional): Filter by request type ("access", "erasure")
- `system_name` (optional): Filter by system name
- `assignee` (optional): Filter by assigned user ID

**Authorization Scoping:**
- Users with `manual-tasks:read-all` scope: Can retrieve all tasks or filter by any assignee
- Users with `manual-tasks:read-own` scope: Must include `assignee` parameter with their own user ID

**Response:**
```json
{
  "items": [
    {
      "task_id": "string",
      "name": "string",
      "description": "string",
      "input_type": "string" | "file" | "checkbox",
      "request_type": "access" | "erasure",
      "status": "new" | "skipped" | "completed",
      "assignedTo": "user_id",
      "privacy_request_id": "string",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "days_left": 30,
      "system_name": "string",
      "system_id": "string"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

### 2. GET `/api/v1/manual-tasks/{task_id}`
**Description:** Get individual manual task

**Parameters:**
- `task_id` (path parameter, required): The task identifier

**Response:**
```json
{
  "task_id": "string",
  "name": "string",
  "description": "string",
  "input_type": "string" | "file" | "checkbox",
  "request_type": "access" | "erasure",
  "status": "new" | "skipped" | "completed",
  "assignedTo": "user_id",
  "privacy_request_id": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "days_left": 30,
  "system_name": "string",
  "system_id": "string"
}
```

### 3. POST `/api/v1/manual-tasks/{task_id}/complete`
**Description:** Complete a manual task with response data

**Parameters:**
- `task_id` (path parameter, required): The task identifier

**Request Body:** multipart/form-data
- `text_value` (optional): Text input response
- `checkbox_value` (optional): Boolean checkbox response
- `attachment_type` (optional): Type of attachment file
- `attachment_file` (optional): File attachment
- `comment` (optional): Additional comment about the completion

**Response:**
```json
{
  "task_id": "string",
  "status": "completed"
}
```

### 4. POST `/api/v1/manual-tasks/{task_id}/skip`
**Description:** Skip a manual task

**Parameters:**
- `task_id` (path parameter, required): The task identifier

**Request Body:**
```json
{
  "comment": "string"
}
```

**Response:**
```json
{
  "task_id": "string",
  "status": "skipped"
}
```

## Notes
- All API endpoints are prefixed with `/api/v1/plus` in production
- Pagination follows the standard Page_T_ pattern used across the application
- Server-side filtering is preferred over client-side filtering for better performance
- The API supports both camelCase (frontend) and snake_case (backend) parameter naming
