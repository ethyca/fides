import {
  AttachmentResponse,
  CommentResponse,
  CommentType,
  ManualFieldListItem,
} from "~/types/api";

// Mock users for completion data
const MOCK_USERS = [
  {
    id: "user_001",
    first_name: "John",
    last_name: "Doe",
    email_address: "john.doe@example.com",
  },
  {
    id: "user_002",
    first_name: "Jane",
    last_name: "Smith",
    email_address: "jane.smith@example.com",
  },
  {
    id: "user_003",
    first_name: "Bob",
    last_name: "Johnson",
    email_address: "bob.johnson@example.com",
  },
];

// Mock comments
const MOCK_COMMENTS: CommentResponse[] = [
  {
    id: "comment_001",
    privacy_request_id: "", // Will be set dynamically
    user_id: "user_001",
    username: "John Doe",
    user_first_name: "John",
    user_last_name: "Doe",
    created_at: new Date().toISOString(),
    attachments: [],
    comment_text: "Task completed successfully with provided documentation",
    comment_type: CommentType.NOTE,
  },
  {
    id: "comment_002",
    privacy_request_id: "",
    user_id: "user_002",
    username: "Jane Smith",
    user_first_name: "Jane",
    user_last_name: "Smith",
    created_at: new Date().toISOString(),
    attachments: [],
    comment_text: "Manual verification completed, all data confirmed",
    comment_type: CommentType.NOTE,
  },
  {
    id: "comment_003",
    privacy_request_id: "",
    user_id: "user_003",
    username: "Bob Johnson",
    user_first_name: "Bob",
    user_last_name: "Johnson",
    created_at: new Date().toISOString(),
    attachments: [],
    comment_text: "Data export reviewed and validated",
    comment_type: CommentType.NOTE,
  },
];

// Mock attachments
const MOCK_ATTACHMENTS: AttachmentResponse[] = [
  {
    id: "att_001",
    user_id: "user_001",
    username: "John Doe",
    user_first_name: "John",
    user_last_name: "Doe",
    file_name: "verification_document.pdf",
    attachment_type: "document",
    retrieved_attachment_size: 245760,
    retrieved_attachment_url: null,
    created_at: new Date().toISOString(),
  },
  {
    id: "att_002",
    user_id: "user_002",
    username: "Jane Smith",
    user_first_name: "Jane",
    user_last_name: "Smith",
    file_name: "data_export.csv",
    attachment_type: "data",
    retrieved_attachment_size: 102400,
    retrieved_attachment_url: null,
    created_at: new Date().toISOString(),
  },
  {
    id: "att_003",
    user_id: "user_003",
    username: "Bob Johnson",
    user_first_name: "Bob",
    user_last_name: "Johnson",
    file_name: "access_report.xlsx",
    attachment_type: "spreadsheet",
    retrieved_attachment_size: 87654,
    retrieved_attachment_url: null,
    created_at: new Date().toISOString(),
  },
];

/**
 * Add mock completion data to manual field items that are completed or skipped
 */
export const addMockCompletionData = (
  items: ManualFieldListItem[],
  privacyRequestId: string,
): ManualFieldListItem[] => {
  return items.map((item, index) => {
    // Only add completion data for completed/skipped items
    if (item.status !== "completed" && item.status !== "skipped") {
      return item;
    }

    // Select mock data cyclically
    const userIndex = index % MOCK_USERS.length;
    const user = MOCK_USERS[userIndex];

    // Use deterministic randomness based on item ID for consistency
    const seed = item.manual_field_id.charCodeAt(
      item.manual_field_id.length - 1,
    );

    // 70% chance of having a comment (deterministic)
    const hasComment = seed % 10 >= 3;
    const comment = hasComment
      ? {
          ...MOCK_COMMENTS[index % MOCK_COMMENTS.length],
          privacy_request_id: privacyRequestId,
        }
      : null;

    // 80% chance of having an attachment (deterministic)
    const hasAttachment = seed % 10 >= 2;
    const attachment = hasAttachment
      ? MOCK_ATTACHMENTS[index % MOCK_ATTACHMENTS.length]
      : null;

    // Mock completion time (1-7 days ago, deterministic)
    const daysAgo = (seed % 7) + 1;
    const completedAt = new Date();
    completedAt.setDate(completedAt.getDate() - daysAgo);

    return {
      ...item,
      // Completion fields
      completed_by_user_id: user.id,
      completed_by_user_first_name: user.first_name,
      completed_by_user_last_name: user.last_name,
      completed_by_user_email_address: user.email_address,
      completion_comment: comment,
      completion_attachment: attachment,
      completed_at: completedAt.toISOString(),
      field_value:
        item.status === "completed" ? `Mock value for ${item.name}` : null,
    };
  });
};
