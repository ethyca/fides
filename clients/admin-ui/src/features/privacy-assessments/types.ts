/**
 * Privacy Assessments API Types
 *
 * TypeScript interfaces for privacy assessment request/response payloads.
 * These types define the contract between the frontend and backend API.
 */

// =============================================================================
// Pagination
// =============================================================================

export interface Page_PrivacyAssessmentResponse_ {
  items: PrivacyAssessmentResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// =============================================================================
// Assessment Response Types
// =============================================================================

export interface PrivacyAssessmentResponse {
  id: string; // UUID
  name: string; // e.g., "Collect data for marketing"
  template_id: string; // e.g., "CPRA-RA-2024"
  template_name: string; // e.g., "CPRA Risk Assessment"
  status: AssessmentStatus;
  status_updated_at: string; // ISO datetime
  risk_level: RiskLevel;
  completeness: number; // 0-100 percentage

  // System/Declaration context
  system_fides_key: string;
  system_name: string;
  declaration_id: string;
  declaration_name: string | null;
  data_use: string; // fides key, e.g., "marketing.advertising"
  data_use_name: string; // friendly name, e.g., "Advertising"
  data_categories: string[]; // e.g., ["user.device.cookie_id"]

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface PrivacyAssessmentDetailResponse
  extends PrivacyAssessmentResponse {
  // Assessment type info (from original CPRAAssessmentResult)
  assessment_type: string; // e.g., "cpra"

  // Question groups with answers
  question_groups: QuestionGroup[];

  // Questionnaire status (if sent)
  questionnaire: QuestionnaireStatus | null;

  // Additional metadata from generation
  metadata: AssessmentMetadata | null;
}

export type AssessmentStatus = "in_progress" | "completed" | "outdated";
export type RiskLevel = "high" | "medium" | "low";

// =============================================================================
// Assessment Metadata
// =============================================================================

export interface AssessmentMetadata {
  generation_timestamp: string; // When assessment was generated
  model_used: string | null; // LLM model if use_llm was true
  use_llm: boolean; // Whether LLM was used

  // Any additional data from the backend
  [key: string]: unknown;
}

// =============================================================================
// Question Groups and Questions
// =============================================================================

export interface QuestionGroup {
  id: string; // e.g., "1", "2", "3"
  title: string; // e.g., "Processing Scope and Purpose(s)"
  requirement_key: string; // e.g., "processing_scope"
  questions: AssessmentQuestion[];

  // Group-level stats
  answered_count: number;
  total_count: number;
  risk_level: RiskLevel | null;
  last_updated_at: string | null;
  last_updated_by: string | null; // User ID or name
}

export interface AssessmentQuestion {
  id: string; // e.g., "1.1", "1.2"
  question_id: string; // Original question ID, e.g., "cpra_1_1"
  question_text: string;
  guidance: string | null; // Help text for answering
  required: boolean;

  // Question metadata (from CPRAAssessmentQuestion)
  fides_sources: string[]; // Fides resource types that can answer this
  // e.g., ["system", "privacy_declaration", "data_category"]
  expected_coverage: string; // Expected coverage level, e.g., "full", "partial"

  // Answer data
  answer_text: string; // Current answer (user-edited or system-derived)
  answer_status: AnswerStatus;
  answer_source: AnswerSource;
  confidence: number | null; // 0-100 if AI-generated

  // Evidence trail
  evidence: EvidenceItem[]; // All evidence supporting this answer
  missing_data: string[]; // Fides fields that could provide answer if populated
  sme_prompt: string | null; // Prompt to send to SME for this question
}

export type AnswerStatus = "complete" | "partial" | "needs_input";
export type AnswerSource = "system" | "ai_analysis" | "user_input" | "slack";

// =============================================================================
// Evidence Types
// =============================================================================

// Discriminated union for different evidence types
export type EvidenceItem =
  | SystemEvidenceItem
  | AIAnalysisEvidenceItem
  | ManualEntryEvidenceItem
  | SlackCommunicationEvidenceItem;

// Base fields shared by all evidence types
export interface BaseEvidenceItem {
  id: string; // Unique evidence ID
  created_at: string; // When this evidence was captured
  citation_number: number | null; // For reference in answer text, e.g., [1], [2]
}

// System-Derived Evidence
export interface SystemEvidenceItem extends BaseEvidenceItem {
  type: "system";

  source: {
    source_type: SystemSourceType; // What kind of Fides resource
    source_key: string; // Fides key of the resource
    source_name: string; // Human-readable name
  };

  field: {
    field_name: string; // Specific field extracted
    field_label: string; // Human-readable label
  };

  value: unknown; // The actual value
  value_display: string; // Formatted for display
}

export type SystemSourceType =
  | "system" // From System resource
  | "privacy_declaration" // From PrivacyDeclaration
  | "data_category" // From DataCategory taxonomy
  | "data_use" // From DataUse taxonomy
  | "data_subject" // From DataSubject taxonomy
  | "dataset" // From Dataset resource
  | "data_flow"; // From data flow configuration

// AI Analysis Evidence
export interface AIAnalysisEvidenceItem extends BaseEvidenceItem {
  type: "ai_analysis";

  model: {
    model_id: string; // e.g., "gpt-4", "claude-3"
    model_version: string | null;
  };

  analysis: {
    input_summary: string; // What data was analyzed
    reasoning: string | null; // LLM's reasoning (if available)
    confidence: number; // 0-100 confidence score
    confidence_label: "high" | "medium" | "low";
  };

  sources_used: string[]; // IDs of other evidence items used as input
}

// Manual Entry Evidence
export interface ManualEntryEvidenceItem extends BaseEvidenceItem {
  type: "manual_entry";

  author: {
    user_id: string;
    user_name: string;
    user_email: string | null;
    role: string | null; // e.g., "Privacy Officer", "Legal Counsel"
  };

  entry: {
    previous_value: string | null; // What the answer was before (for edits)
    new_value: string; // The new answer text
    edit_reason: string | null; // Optional reason for the change
  };
}

// Slack Communication Evidence
export interface SlackCommunicationEvidenceItem extends BaseEvidenceItem {
  type: "slack_communication";

  channel: {
    channel_id: string;
    channel_name: string; // e.g., "#privacy-team"
  };

  thread: {
    thread_id: string; // Slack thread timestamp
    thread_url: string | null; // Direct link to thread
    started_at: string; // When thread was created
    message_count: number;
    participant_count: number;
  };

  // The messages in the thread
  messages: SlackMessage[];

  // Summary of the discussion (for quick reference)
  summary: string | null; // AI-generated or manual summary
}

export interface SlackMessage {
  message_id: string;
  timestamp: string;

  sender: {
    user_id: string;
    user_name: string;
    display_name: string; // Slack display name
    avatar_url: string | null;
  };

  content: {
    text: string; // Message text
    is_bot_message: boolean; // Was this from our questionnaire bot?
    attachments: SlackAttachment[];
  };

  reactions: SlackReaction[]; // Emoji reactions (useful for approvals)

  // If this message is a reply to another
  reply_to_message_id: string | null;
}

export interface SlackAttachment {
  type: "file" | "image" | "link";
  name: string;
  url: string | null;
}

export interface SlackReaction {
  emoji: string; // e.g., "white_check_mark", "+1"
  count: number;
  users: string[]; // User IDs who reacted
}

// =============================================================================
// Questionnaire Types
// =============================================================================

export interface QuestionnaireStatus {
  sent_at: string; // ISO datetime when questionnaire was sent
  channel: string; // e.g., "#privacy-team"
  total_questions: number; // Questions requiring user input
  answered_questions: number; // Questions that have been answered
  last_reminder_at: string | null; // ISO datetime of last reminder
  reminder_count: number; // Number of reminders sent
}

export interface QuestionnaireStatusResponse {
  assessment_id: string;
  sent_at: string;
  channel: string;

  // Progress
  total_questions: number;
  answered_questions: number;
  pending_questions: number;
  progress_percentage: number; // 0-100

  // Questions breakdown
  questions: QuestionnaireQuestion[];

  // Reminders
  last_reminder_at: string | null;
  reminder_count: number;
}

export interface QuestionnaireQuestion {
  question_id: string;
  question_text: string;
  status: "answered" | "pending";
  answered_at: string | null;
  answered_by: string | null;
}

export interface QuestionnaireResponse {
  sent_at: string;
  channel: string;
  questions_sent: number;
  message_id: string | null; // Slack message ID if applicable
}

export interface ReminderResponse {
  sent_at: string;
  channel: string;
  pending_questions: number;
  message_id: string | null;
}

// =============================================================================
// Request Types
// =============================================================================

export interface CreatePrivacyAssessmentRequest {
  assessment_type: "cpra"; // Extensible for future types (GDPR DPIA, etc.)
  system_fides_key?: string; // Optional: generate for specific system
  declaration_id?: string; // Optional: generate for specific declaration
  use_llm?: boolean; // Whether to use LLM for AI-assisted answers
  model?: string; // Optional: specific LLM model to use
}

export interface CreatePrivacyAssessmentResponse {
  assessments: PrivacyAssessmentResponse[]; // List of created assessments
  assessment_type: string;
  assessment_name: string; // e.g., "CPRA Risk Assessment"
  total_created: number;
}

export interface UpdatePrivacyAssessmentRequest {
  name?: string;
  status?: AssessmentStatus;
  risk_level?: RiskLevel;
}

export interface UpdateAnswerRequest {
  answer_text: string;
}

export interface UpdateAnswerResponse {
  question: AssessmentQuestion; // Updated question
  completeness: number; // Updated assessment completeness percentage
  status: AssessmentStatus; // Assessment status (may change to completed)
}

export interface BulkUpdateAnswersRequest {
  answers: AnswerUpdate[];
}

export interface AnswerUpdate {
  question_id: string; // e.g., "cpra_1_1" or "1.1"
  answer_text: string;
}

export interface BulkUpdateAnswersResponse {
  updated_count: number;
  completeness: number; // Updated completeness percentage
  status: AssessmentStatus; // May change to completed if 100%
  questions: AssessmentQuestion[]; // All updated questions
}

export interface CreateQuestionnaireRequest {
  channel: string; // e.g., "#privacy-team"
  message?: string; // Optional custom message
  include_question_ids?: string[]; // Optional: specific questions, default all needs_input
}

export interface CreateReminderRequest {
  message?: string; // Optional custom reminder message
}

// =============================================================================
// Evidence Endpoint Types
// =============================================================================

export interface AssessmentEvidenceResponse {
  assessment_id: string;
  total_count: number;

  // Evidence grouped by question (if group_by=question or default)
  by_question?: Record<string, QuestionEvidence>;

  // Evidence grouped by type (if group_by=type)
  by_type?: {
    system: SystemEvidenceItem[];
    ai_analysis: AIAnalysisEvidenceItem[];
    manual_entry: ManualEntryEvidenceItem[];
    slack_communication: SlackCommunicationEvidenceItem[];
  };

  // Flat list (if no grouping)
  items?: EvidenceItem[];
}

export interface QuestionEvidence {
  question_id: string;
  question_text: string;
  evidence: EvidenceItem[];
}

// =============================================================================
// Query Parameter Types
// =============================================================================

export interface GetPrivacyAssessmentsParams {
  page?: number;
  size?: number;
  status?: AssessmentStatus;
}

export interface GetAssessmentEvidenceParams {
  id: string;
  question_id?: string;
  type?: EvidenceItem["type"];
  group_by?: "question" | "type";
}
