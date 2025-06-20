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
  input_type: "string",
  status: "new",
  assigned_users: [mockUsers[0]],
  privacy_request: {
    id: "pri_5005c923-474c-4168-8c9e-2670fd40dc19",
    days_left: 25,
    request_type: "access",
    subject_identity: {
      email: {
        label: "Email",
        value: "customer@email.com",
      },
    },
  },
  system: {
    id: mockSystems[0].id,
    name: mockSystems[0].name,
  },
  ...overrides,
});
