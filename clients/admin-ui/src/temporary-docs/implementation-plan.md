# Manual Tasks Implementation Plan

## File Structure
```
src/
└── features/
    └── manual-tasks/
        ├── manual-tasks.slice.ts       # Redux slice with API endpoints
        ├── ManualTasks.tsx             # Main component with search
        └── components/
            ├── ManualTasksTable.tsx    # Table component
            ├── ActionButtons.tsx       # Action buttons for tasks
            └── StatusTag.tsx           # Status tag component
```

## Implementation Status

### ✅ Completed
- [x] Create file structure
- [x] Create types in types/api/models/ManualTask.ts
- [x] Add type exports to types/api/index.ts
- [x] Create manual-tasks.slice.ts with RTK Query endpoints
- [x] Add the slice to the store configuration
- [x] Create StatusTag component
- [x] Create ActionButtons component
- [x] Create ManualTasksTable component with filtering and sorting
- [x] Create ManualTasks component with search
- [x] Integrate with ManualTaskTab in privacy requests
- [x] Style all components with Tailwind

### 🔄 In Progress
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
```

### Endpoints
GET `/api/v1/plus/manual-tasks/`
- Returns a list of manual tasks

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
- Built-in filtering and sorting
- Pagination

### ActionButtons Component
- Complete button for new tasks
- Skip button with comment modal
- Loading states for API calls

### StatusTag Component
- Color-coded tags for task status:
  - New: Blue
  - Completed: Green
  - Skipped: Orange

## Notes
- Uses Ant Design components imported from "fidesui"
- Layout uses Tailwind classes
- Uses RTK Query for API calls
- Uses TypeScript for type safety
- Table uses built-in filtering and sorting
- Currently visible when the `alphaNewManualDSR` feature flag is enabled
