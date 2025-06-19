import { ManualTask, RequestType, TaskInputType, TaskStatus } from "./types";

export const mockTaskStatus: TaskStatus[] = ["new", "skipped", "completed"];
export const mockRequestTypes: RequestType[] = ["access", "erasure"];
export const mockInputTypes: TaskInputType[] = ["string", "file", "checkbox"];

export const mockSystems = [
  { id: "sys_1", name: "Salesforce" },
  { id: "sys_2", name: "MySQL Database" },
  { id: "sys_3", name: "MongoDB Atlas" },
];

export const mockUsers = [
  {
    id: "usr_1",
    email_address: "john.doe@company.com",
    first_name: "John",
    last_name: "Doe",
  },
  {
    id: "usr_2",
    email_address: "jane.smith@company.com",
    first_name: "Jane",
    last_name: "Smith",
  },
  {
    id: "usr_3",
    email_address: "bob.wilson@company.com",
    first_name: "Bob",
    last_name: "Wilson",
  },
];

export const createMockTask = (
  overrides?: Partial<ManualTask>,
): ManualTask => ({
  task_id: `task_${Math.random().toString(36).substr(2, 9)}`,
  name: "Export Customer Data",
  description: "Export all customer data from the system",
  input_type: "file",
  request_type: "access",
  status: "new",
  assigned_users: [mockUsers[0]],
  privacy_request_id: "pri_5005c923-474c-4168-8c9e-2670fd40dc19",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  days_left: 25,
  due_date: new Date(Date.now() + 25 * 24 * 60 * 60 * 1000).toISOString(),
  system_name: mockSystems[0].name,
  system_id: mockSystems[0].id,
  ...overrides,
});
