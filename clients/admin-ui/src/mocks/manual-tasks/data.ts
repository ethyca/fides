import type {
  ManualFieldListItem,
  ManualFieldSearchFilterOptions,
  ManualFieldSystem,
  ManualFieldUser,
} from "~/types/api";
import {
  CommentType,
  ManualFieldRequestType,
  ManualFieldStatus,
  ManualTaskFieldType,
} from "~/types/api";

const mockUsers: ManualFieldUser[] = [
  {
    id: "fidesadmin",
    email_address: "root_user@example.com",
    first_name: "Fides",
    last_name: "Admin",
  },
  {
    id: "fid_dcf26c27-b992-43e0-9178-2b577720e0c6",
    email_address: "john.doe@example.com",
    first_name: "John",
    last_name: "Doe",
  },
  {
    id: "fid_833b42df-ed8b-456b-a2f3-8f19322ec5a2",
    email_address: "jane.doe@example.com",
    first_name: "Jane",
    last_name: "Doe",
  },
  {
    id: "fid_970eee07-f621-48ac-aeea-8ac4ac7d4d3b",
    email_address: "michael.brown@example.com",
    first_name: "Michael",
    last_name: "Brown",
  },
  {
    id: "fid_73d47c3d-e94b-4497-8b51-e50f728283ea",
    email_address: "sarah.chen@example.com",
    first_name: "Sarah",
    last_name: "Chen",
  },
  {
    id: "fid_6eaa3315-49ac-4c61-a8f8-1743cbf32251",
    email_address: "crm@example.com",
    first_name: "CRM",
    last_name: "Admin",
  },
  {
    id: "fid_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    email_address: "alex.garcia@example.com",
    first_name: "Alex",
    last_name: "Garcia",
  },
  {
    id: "fid_b2c3d4e5-f6a7-8901-bcde-f12345678901",
    email_address: "priya.patel@example.com",
    first_name: "Priya",
    last_name: "Patel",
  },
  {
    id: "fid_c3d4e5f6-a7b8-9012-cdef-123456789012",
    email_address: "omar.hassan@example.com",
    first_name: "Omar",
    last_name: "Hassan",
  },
];

const mockSystems: ManualFieldSystem[] = [
  { id: "sys_001", name: "Salesforce" },
  { id: "sys_002", name: "MongoDB" },
  { id: "sys_003", name: "Stripe" },
  { id: "sys_004", name: "Google Analytics" },
  { id: "sys_005", name: "HubSpot CRM" },
  { id: "sys_006", name: "Data Warehouse" },
  { id: "sys_007", name: "Zendesk" },
  { id: "sys_008", name: "Snowflake" },
  { id: "sys_009", name: "AWS S3" },
  { id: "sys_010", name: "Mailchimp" },
];

const statuses = Object.values(ManualFieldStatus);
const requestTypes = Object.values(ManualFieldRequestType);
const inputTypes = Object.values(ManualTaskFieldType);

const taskTemplates = [
  "Export Customer Data from {system}",
  "Delete User Profile from {system}",
  "Confirm Data Deletion in {system}",
  "Extract Analytics Data from {system}",
  "Remove User Records from {system}",
  "Export User Data Package from {system}",
  "Verify Data Removal in {system}",
  "Manual Data Review in {system}",
  "Update Consent Records in {system}",
  "Audit Data Access Logs in {system}",
  "Retrieve Stored Preferences from {system}",
  "Clear Session Data in {system}",
  "Export Communication History from {system}",
  "Validate Identity Documents via {system}",
  "Archive User Records in {system}",
];

const subjectEmails = [
  "alice@example.com",
  "bob@customer.org",
  "charlie@test.net",
  "dana@mail.com",
  "eve@privacy.io",
  "frank@company.co",
  "grace@email.com",
  "henry@domain.org",
  "iris@test.com",
  "jack@example.net",
  "karen@mail.org",
  "leo@customer.com",
  "maya@test.io",
  "noah@example.com",
  "olivia@domain.net",
  "pete@mail.com",
];

const subjectPhones = [
  "+1-555-0101",
  "+1-555-0202",
  "+1-555-0303",
  "+1-555-0404",
  "+1-555-0505",
  "+1-555-0606",
  "+1-555-0707",
  "+1-555-0808",
];

function pick<T>(arr: T[], i: number): T {
  return arr[i % arr.length];
}

export const generateMockManualTasks = (): ManualFieldListItem[] => {
  const items: ManualFieldListItem[] = [];

  for (let i = 0; i < 75; i += 1) {
    const status = pick(statuses, i);
    const reqType = pick(requestTypes, i);
    const system = pick(mockSystems, i);
    const name = pick(taskTemplates, i).replace("{system}", system.name);
    const daysLeft = Math.max(-3, 30 - (i % 35));

    const assignedUsers: ManualFieldUser[] = [];
    // Assign fidesadmin (index 0) to ~80% of tasks so the default
    // "assigned to me" view has enough data for multiple pages.
    if (i % 5 !== 0) {
      assignedUsers.push(mockUsers[0]); // fidesadmin
    }
    // Add a second user to some tasks for variety
    if (i % 3 === 0) {
      assignedUsers.push(pick(mockUsers, i + 1));
    }

    const subjectIdentities: Record<string, string> = {};
    if (i % 3 !== 2) {
      subjectIdentities.email = pick(subjectEmails, i);
    }
    if (i % 3 !== 0) {
      subjectIdentities.phone_number = pick(subjectPhones, i);
    }

    const createdDate = new Date(
      2024,
      2,
      1 + (i % 28),
      8 + (i % 12),
      (i * 7) % 60,
    );
    const updatedDate = new Date(createdDate.getTime() + (i % 5) * 86400000);

    const item: ManualFieldListItem = {
      manual_field_id: `task_${String(i + 1).padStart(3, "0")}`,
      name,
      description: `${name} for privacy request processing`,
      input_type: pick(inputTypes, i),
      request_type: reqType,
      status,
      assigned_users: assignedUsers,
      privacy_request: {
        id: `pri_${String(i + 1).padStart(4, "0")}a1b2-c3d4-e5f6-a7b8-c9d0e1f2a3b4`,
        days_left: daysLeft,
        request_type: reqType,
        subject_identities: subjectIdentities,
        custom_fields: {},
      },
      system,
      created_at: createdDate.toISOString(),
      updated_at: updatedDate.toISOString(),
    };

    if (status !== ManualFieldStatus.NEW && assignedUsers.length > 0) {
      [item.submission_user] = assignedUsers;
    }

    if (i % 8 === 0) {
      item.comments = [
        {
          id: `comment_${String(i + 1).padStart(3, "0")}`,
          privacy_request_id: item.privacy_request.id,
          user_id: assignedUsers[0]?.id ?? "system",
          username: assignedUsers[0]
            ? `${assignedUsers[0].first_name} ${assignedUsers[0].last_name}`
            : "System",
          user_first_name: assignedUsers[0]?.first_name ?? "System",
          user_last_name: assignedUsers[0]?.last_name ?? "",
          created_at: updatedDate.toISOString(),
          attachments: [],
          comment_text:
            // eslint-disable-next-line no-nested-ternary
            status === ManualFieldStatus.COMPLETED
              ? "Task completed successfully"
              : status === ManualFieldStatus.SKIPPED
                ? "Skipped - data not found"
                : "In progress, awaiting review",
          comment_type: CommentType.NOTE,
        },
      ];
    }

    if (i % 11 === 0) {
      item.attachments = [
        {
          id: `att_${String(i + 1).padStart(3, "0")}`,
          file_name: `export_${i + 1}.csv`,
          file_size: String(1024 * ((i % 10) + 1)),
          created_at: updatedDate.toISOString(),
        },
      ];
    }

    items.push(item);
  }

  return items;
};

export const mockManualTasks = generateMockManualTasks();

export const mockManualTaskFilterOptions: ManualFieldSearchFilterOptions = {
  assigned_users: mockUsers,
  systems: mockSystems,
};
