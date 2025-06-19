# Manual Tasks Implementation Plan

## File Structure
```
src/
└── features/
    └── manual-tasks/
        ├── manual-tasks.slice.ts       # Redux slice with API endpoints
        ├── ManualTasks.tsx             # Main component with search
        └── components/
            ├── ManualTasksTable.tsx    # Table component with status and request type tags
            └── ActionButtons.tsx       # Action buttons for tasks
```

## Implementation Status

### ✅ Completed
- [x] Create file structure
- [x] Create types in types/api/models/ManualTask.ts
- [x] Add type exports to types/api/index.ts
- [x] Create manual-tasks.slice.ts with RTK Query endpoints
- [x] Add the slice to the store configuration
- [x] Create ActionButtons component
- [x] Create ManualTasksTable component with filtering and server-side pagination
- [x] Create ManualTasks component with search
- [x] Integrate with ManualTaskTab in privacy requests
- [x] Style all components with Tailwind
- [x] Implement server-side pagination
- [x] Create Page_ManualTask_ type for pagination

### 🔄 In Progress
- [ ] Implement skip task functionality with comment modal
- [ ] Connect to real API endpoints
- [ ] Add error handling and notifications
- [ ] Add tests

## Future Tasks (When Real Endpoints Are Available)

### API Integration
- [ ] Update API endpoint paths in manual-tasks.slice.ts
- [ ] Add proper error handling for API responses
- [ ] Implement proper loading states
- [ ] Add toast notifications for success/error states

### Feature Enhancements
- [ ] Implement file upload for file input type tasks
- [ ] Add detailed task view/drawer
- [ ] Add task assignment functionality
- [ ] Implement task comments
- [ ] Add task history/audit log

### Testing
- [ ] Write unit tests for slice reducers
- [ ] Write component tests
- [ ] Write integration tests for filters and actions
- [ ] Add end-to-end tests

## API Design

### Manual Task Response Structure
```typescript
interface ManualTask {
  task_id: string;
  name: string;
  description: string;
  input_type: "string" | "file" | "checkbox";
  request_type: "access" | "erasure";
  status: "new" | "skipped" | "completed";
  assignedTo: string;
  privacy_request_id: string;
  created_at: string;
  updated_at: string;
  // Additional fields from linked privacy request
  days_left: number;
  due_date: string;
  // System information
  system_name: string;
  system_id: string;
}

// Pagination response type
interface Page_ManualTask_ {
  items: Array<ManualTask>;
  total: number | null;
  page: number | null;
  size: number | null;
  pages?: number | null;
}
```

### Endpoints
GET `/api/v1/plus/manual-tasks/`
- Returns a paginated list of manual tasks
- Supports query parameters:
  - page: Page number (default: 1)
  - size: Page size (default: 10)
  - search: Search term for name or description
  - status: Filter by status
  - requestType: Filter by request type
  - systemName: Filter by system name

GET `/api/v1/plus/manual-tasks/{task_id}`
- Returns a specific manual task by ID

POST `/api/v1/plus/manual-tasks/{task_id}/complete`
- Completes a manual task
- Payload varies based on input_type

POST `/api/v1/plus/manual-tasks/{task_id}/skip`
- Skips a manual task
- Requires a comment explaining why

## UI Components

### ManualTasks Component
- Search input for filtering tasks by name or description
- Table component for displaying tasks

### ManualTasksTable Component
- Small size variant of Ant Design Table
- Columns:
  - Task name
  - Status (with colored tags)
  - Days left
  - Source
  - Request type
  - Created date
  - Actions
- Built-in filtering
- Server-side pagination using PaginationBar
- Color-coded tags for task status:
  - New: Blue
  - Completed: Green
  - Skipped: Gray
- Color-coded tags for request type:
  - Access: Blue
  - Erasure: Red

### ActionButtons Component
- Complete button for new tasks
- Loading states for API calls
- Skip functionality to be implemented later

## Notes
- Uses Ant Design components imported from "fidesui"
- Layout uses Tailwind classes
- Uses RTK Query for API calls
- Uses TypeScript for type safety
- Table uses server-side pagination and filtering
- Currently visible when the `alphaNewManualDSR` feature flag is enabled
