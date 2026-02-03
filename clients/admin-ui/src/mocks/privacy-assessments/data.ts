/**
 * Privacy Assessments Mock Data
 *
 * Factory functions and pre-built mock data for privacy assessments.
 * Used by MSW handlers for development and testing.
 */

import {
  AIAnalysisEvidenceItem,
  AnswerSource,
  AnswerStatus,
  AssessmentMetadata,
  AssessmentQuestion,
  AssessmentStatus,
  EvidenceItem,
  ManualEntryEvidenceItem,
  Page_PrivacyAssessmentResponse_,
  PrivacyAssessmentDetailResponse,
  PrivacyAssessmentResponse,
  QuestionGroup,
  QuestionnaireQuestion,
  QuestionnaireStatus,
  QuestionnaireStatusResponse,
  RiskLevel,
  SlackCommunicationEvidenceItem,
  SlackMessage,
  SystemEvidenceItem,
} from "~/features/privacy-assessments/types";

// =============================================================================
// Factory Functions
// =============================================================================

let assessmentIdCounter = 1;
let evidenceIdCounter = 1;

export const mockPrivacyAssessment = (
  partial?: Partial<PrivacyAssessmentResponse>
): PrivacyAssessmentResponse => {
  const id = partial?.id ?? `assessment-${assessmentIdCounter++}`;
  return {
    id,
    name: "Collect data for marketing",
    template_id: "CPRA-RA-2024",
    template_name: "CPRA Risk Assessment",
    status: "in_progress",
    status_updated_at: new Date().toISOString(),
    risk_level: "medium",
    completeness: 45,
    system_fides_key: "demo_marketing_system",
    system_name: "Demo Marketing System",
    declaration_id: "collect_data_for_marketing",
    declaration_name: "Collect data for marketing",
    data_use: "marketing.advertising",
    data_use_name: "Advertising",
    data_categories: ["user.device.cookie_id"],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...partial,
  };
};

export const mockSystemEvidence = (
  partial?: Partial<SystemEvidenceItem>
): SystemEvidenceItem => {
  const id = partial?.id ?? `ev-sys-${evidenceIdCounter++}`;
  return {
    id,
    type: "system",
    created_at: new Date().toISOString(),
    citation_number: 1,
    source: {
      source_type: "privacy_declaration",
      source_key: "demo_marketing_system.marketing_advertising",
      source_name: "Demo Marketing System - Advertising Declaration",
    },
    field: {
      field_name: "data_use",
      field_label: "Data Use",
    },
    value: "marketing.advertising",
    value_display: "Marketing / Advertising",
    ...partial,
  };
};

export const mockAIAnalysisEvidence = (
  partial?: Partial<AIAnalysisEvidenceItem>
): AIAnalysisEvidenceItem => {
  const id = partial?.id ?? `ev-ai-${evidenceIdCounter++}`;
  return {
    id,
    type: "ai_analysis",
    created_at: new Date().toISOString(),
    citation_number: null,
    model: {
      model_id: "gpt-4",
      model_version: "gpt-4-0125-preview",
    },
    analysis: {
      input_summary: "Analyzed privacy declaration and data category mappings",
      reasoning:
        "Based on the data_use of marketing.advertising and presence of cookie_id, this processing involves cross-context behavioral advertising.",
      confidence: 85,
      confidence_label: "high",
    },
    sources_used: ["ev-sys-001", "ev-sys-002"],
    ...partial,
  };
};

export const mockManualEntryEvidence = (
  partial?: Partial<ManualEntryEvidenceItem>
): ManualEntryEvidenceItem => {
  const id = partial?.id ?? `ev-manual-${evidenceIdCounter++}`;
  return {
    id,
    type: "manual_entry",
    created_at: new Date().toISOString(),
    citation_number: 5,
    author: {
      user_id: "user_abc123",
      user_name: "Jack Gale",
      user_email: "jack@example.com",
      role: "Privacy Officer",
    },
    entry: {
      previous_value: null,
      new_value:
        "Processing involves ML analysis of customer purchase history and browsing behavior for personalized recommendations.",
      edit_reason: "Added details from internal documentation",
    },
    ...partial,
  };
};

export const mockSlackMessage = (
  partial?: Partial<SlackMessage>
): SlackMessage => ({
  message_id: `msg-${Date.now()}`,
  timestamp: new Date().toISOString(),
  sender: {
    user_id: "U001",
    user_name: "jack.gale",
    display_name: "Jack Gale",
    avatar_url: null,
  },
  content: {
    text: "Sample message",
    is_bot_message: false,
    attachments: [],
  },
  reactions: [],
  reply_to_message_id: null,
  ...partial,
});

export const mockSlackCommunicationEvidence = (
  partial?: Partial<SlackCommunicationEvidenceItem>
): SlackCommunicationEvidenceItem => {
  const id = partial?.id ?? `ev-slack-${evidenceIdCounter++}`;
  return {
    id,
    type: "slack_communication",
    created_at: new Date().toISOString(),
    citation_number: 9,
    channel: {
      channel_id: "C123ABC",
      channel_name: "#privacy-team",
    },
    thread: {
      thread_id: "1705234200.123456",
      thread_url:
        "https://workspace.slack.com/archives/C123ABC/p1705234200123456",
      started_at: new Date().toISOString(),
      message_count: 3,
      participant_count: 2,
    },
    messages: [
      mockSlackMessage({
        message_id: "msg-001",
        timestamp: "2025-01-14T10:30:00Z",
        sender: {
          user_id: "U001",
          user_name: "jack.gale",
          display_name: "Jack Gale",
          avatar_url: null,
        },
        content: {
          text: "Does anyone know if we use any automated decision-making for the marketing personalization?",
          is_bot_message: false,
          attachments: [],
        },
      }),
      mockSlackMessage({
        message_id: "msg-002",
        timestamp: "2025-01-14T11:15:00Z",
        sender: {
          user_id: "U002",
          user_name: "emily.rodriguez",
          display_name: "Emily Rodriguez",
          avatar_url: null,
        },
        content: {
          text: "I checked with the engineering team - we use ML models for recommendations but no automated decisions that have legal effects on users.",
          is_bot_message: false,
          attachments: [],
        },
        reactions: [
          { emoji: "white_check_mark", count: 2, users: ["U001", "U003"] },
        ],
        reply_to_message_id: "msg-001",
      }),
      mockSlackMessage({
        message_id: "msg-003",
        timestamp: "2025-01-14T11:45:00Z",
        sender: {
          user_id: "U001",
          user_name: "jack.gale",
          display_name: "Jack Gale",
          avatar_url: null,
        },
        content: {
          text: "Thanks Emily! So we can confirm no ADMT is used for this processing activity.",
          is_bot_message: false,
          attachments: [],
        },
        reply_to_message_id: "msg-002",
      }),
    ],
    summary:
      "Confirmed that no automated decision-making technology (ADMT) is used for marketing personalization - only ML recommendations without legal effects.",
    ...partial,
  };
};

export const mockAssessmentQuestion = (
  partial?: Partial<AssessmentQuestion>
): AssessmentQuestion => ({
  id: "1.1",
  question_id: "cpra_1_1",
  question_text: "What is the name and description of this processing activity?",
  guidance: "Describe the processing activity in detail.",
  required: true,
  fides_sources: ["system", "privacy_declaration"],
  expected_coverage: "full",
  answer_text:
    "Collect data for marketing - Collect data about our users for marketing. [1]",
  answer_status: "complete",
  answer_source: "system",
  confidence: 95,
  evidence: [],
  missing_data: [],
  sme_prompt: null,
  ...partial,
});

export const mockQuestionGroup = (
  partial?: Partial<QuestionGroup>
): QuestionGroup => ({
  id: "1",
  title: "Processing Scope and Purpose(s)",
  requirement_key: "processing_scope",
  questions: [],
  answered_count: 2,
  total_count: 5,
  risk_level: "low",
  last_updated_at: new Date().toISOString(),
  last_updated_by: "Jack Gale",
  ...partial,
});

export const mockQuestionnaireStatus = (
  partial?: Partial<QuestionnaireStatus>
): QuestionnaireStatus => ({
  sent_at: new Date().toISOString(),
  channel: "#privacy-team",
  total_questions: 8,
  answered_questions: 3,
  last_reminder_at: null,
  reminder_count: 0,
  ...partial,
});

export const mockQuestionnaireStatusResponse = (
  partial?: Partial<QuestionnaireStatusResponse>
): QuestionnaireStatusResponse => ({
  assessment_id: "assessment-1",
  sent_at: new Date().toISOString(),
  channel: "#privacy-team",
  total_questions: 8,
  answered_questions: 3,
  pending_questions: 5,
  progress_percentage: 37.5,
  questions: [],
  last_reminder_at: null,
  reminder_count: 0,
  ...partial,
});

export const mockAssessmentMetadata = (
  partial?: Partial<AssessmentMetadata>
): AssessmentMetadata => ({
  generation_timestamp: new Date().toISOString(),
  model_used: "gpt-4",
  use_llm: true,
  ...partial,
});

export const mockPrivacyAssessmentDetail = (
  partial?: Partial<PrivacyAssessmentDetailResponse>
): PrivacyAssessmentDetailResponse => ({
  ...mockPrivacyAssessment(),
  assessment_type: "cpra",
  question_groups: MOCK_CPRA_QUESTION_GROUPS,
  questionnaire: null,
  metadata: mockAssessmentMetadata(),
  ...partial,
});

// =============================================================================
// Pre-built Mock Data - CPRA Question Groups
// =============================================================================

export const MOCK_CPRA_QUESTION_GROUPS: QuestionGroup[] = [
  {
    id: "1",
    title: "Processing Scope and Purpose(s)",
    requirement_key: "processing_scope",
    answered_count: 2,
    total_count: 5,
    risk_level: "low",
    last_updated_at: "2025-01-28T10:30:00Z",
    last_updated_by: "Jack Gale",
    questions: [
      {
        id: "1.1",
        question_id: "cpra_1_1",
        question_text:
          "What is the name and description of this processing activity?",
        guidance:
          "Provide the official name and a detailed description of what this processing activity involves.",
        required: true,
        fides_sources: ["system", "privacy_declaration"],
        expected_coverage: "full",
        answer_text:
          "Collect data for marketing - Collect data about our users for marketing. [1]",
        answer_status: "complete",
        answer_source: "system",
        confidence: 95,
        evidence: [],
        missing_data: [],
        sme_prompt: null,
      },
      {
        id: "1.2",
        question_id: "cpra_1_2",
        question_text:
          "What are the specific purposes for processing personal information?",
        guidance:
          "List all purposes for which personal information is collected and processed.",
        required: true,
        fides_sources: ["privacy_declaration", "data_use"],
        expected_coverage: "full",
        answer_text:
          "marketing.advertising - First and third party advertising purposes. [2]",
        answer_status: "complete",
        answer_source: "system",
        confidence: 90,
        evidence: [],
        missing_data: [],
        sme_prompt: null,
      },
      {
        id: "1.3",
        question_id: "cpra_1_3",
        question_text:
          "Why is this processing necessary for the business? What business need does it address?",
        guidance:
          "Explain the business justification for this processing activity.",
        required: true,
        fides_sources: [],
        expected_coverage: "full",
        answer_text: "",
        answer_status: "needs_input",
        answer_source: "slack",
        confidence: null,
        evidence: [],
        missing_data: ["system.description", "privacy_declaration.purpose"],
        sme_prompt:
          "Please explain why this processing is necessary for the business and what business need it addresses.",
      },
      {
        id: "1.4",
        question_id: "cpra_1_4",
        question_text:
          "What is the scale of processing (number of consumers, volume of data, geographic scope)?",
        guidance:
          "Describe the scope and scale of the processing activity, including the number of individuals affected.",
        required: true,
        fides_sources: [],
        expected_coverage: "full",
        answer_text: "",
        answer_status: "needs_input",
        answer_source: "slack",
        confidence: null,
        evidence: [],
        missing_data: [],
        sme_prompt:
          "Please provide information about the scale of this processing activity.",
      },
      {
        id: "1.5",
        question_id: "cpra_1_5",
        question_text: "How frequently does this processing occur?",
        guidance:
          "Indicate whether the processing is continuous, periodic, or triggered by specific events.",
        required: false,
        fides_sources: [],
        expected_coverage: "partial",
        answer_text: "",
        answer_status: "needs_input",
        answer_source: "slack",
        confidence: null,
        evidence: [],
        missing_data: [],
        sme_prompt:
          "Please describe how frequently this processing activity occurs.",
      },
    ],
  },
  {
    id: "2",
    title: "Significant Risk Determination",
    requirement_key: "significant_risk_determination",
    answered_count: 3,
    total_count: 6,
    risk_level: "medium",
    last_updated_at: "2025-01-27T14:20:00Z",
    last_updated_by: "System",
    questions: [
      {
        id: "2.1",
        question_id: "cpra_2_1",
        question_text:
          "Does this processing involve selling personal information?",
        guidance:
          "Indicate whether personal information is sold as defined under CPRA.",
        required: true,
        fides_sources: ["privacy_declaration", "data_use"],
        expected_coverage: "full",
        answer_text:
          "Potential - The marketing.advertising data use may involve sharing with third parties for advertising purposes. [3]",
        answer_status: "complete",
        answer_source: "system",
        confidence: 75,
        evidence: [],
        missing_data: [],
        sme_prompt: null,
      },
      {
        id: "2.2",
        question_id: "cpra_2_2",
        question_text:
          "Does this processing involve sharing PI for cross-context behavioral advertising?",
        guidance:
          "Indicate whether personal information is shared for behavioral advertising across different contexts.",
        required: true,
        fides_sources: ["privacy_declaration", "data_use"],
        expected_coverage: "full",
        answer_text:
          "Yes - Processing uses marketing.advertising which typically involves cross-context behavioral advertising. [4]",
        answer_status: "complete",
        answer_source: "system",
        confidence: 85,
        evidence: [],
        missing_data: [],
        sme_prompt: null,
      },
      {
        id: "2.3",
        question_id: "cpra_2_3",
        question_text:
          "Does this processing involve sensitive personal information?",
        guidance:
          "List any sensitive personal information categories that are processed.",
        required: true,
        fides_sources: ["data_category", "privacy_declaration"],
        expected_coverage: "full",
        answer_text:
          "No - Only user.device.cookie_id is processed, which is not classified as sensitive PI. [3]",
        answer_status: "complete",
        answer_source: "system",
        confidence: 90,
        evidence: [],
        missing_data: [],
        sme_prompt: null,
      },
      {
        id: "2.4",
        question_id: "cpra_2_4",
        question_text:
          "Does this processing involve automated decision-making technology (ADMT)?",
        guidance:
          "Indicate whether any automated decision-making technology is used that produces legal or similarly significant effects.",
        required: true,
        fides_sources: [],
        expected_coverage: "full",
        answer_text: "",
        answer_status: "needs_input",
        answer_source: "slack",
        confidence: null,
        evidence: [],
        missing_data: [],
        sme_prompt:
          "Does this processing activity use any automated decision-making technology (ADMT)?",
      },
      {
        id: "2.5",
        question_id: "cpra_2_5",
        question_text:
          "What specific risks to consumers does this processing present?",
        guidance:
          "Describe the potential risks to consumers from this processing activity.",
        required: true,
        fides_sources: [],
        expected_coverage: "full",
        answer_text: "",
        answer_status: "needs_input",
        answer_source: "slack",
        confidence: null,
        evidence: [],
        missing_data: [],
        sme_prompt:
          "Please describe the specific risks to consumers that this processing presents.",
      },
      {
        id: "2.6",
        question_id: "cpra_2_6",
        question_text:
          'Why does this processing meet the threshold for "significant risk"?',
        guidance:
          "Explain why this processing activity meets the CPRA threshold for significant risk.",
        required: true,
        fides_sources: [],
        expected_coverage: "full",
        answer_text: "",
        answer_status: "needs_input",
        answer_source: "slack",
        confidence: null,
        evidence: [],
        missing_data: [],
        sme_prompt:
          'Please explain why this processing meets the threshold for "significant risk" under CPRA.',
      },
    ],
  },
  {
    id: "3",
    title: "Categories of Personal/Sensitive Personal Information",
    requirement_key: "data_categories",
    answered_count: 3,
    total_count: 4,
    risk_level: "low",
    last_updated_at: "2025-01-28T08:00:00Z",
    last_updated_by: "System",
    questions: [
      {
        id: "3.1",
        question_id: "cpra_3_1",
        question_text:
          "What categories of personal information are collected and processed?",
        guidance: "List all categories of personal information that are processed.",
        required: true,
        fides_sources: ["data_category", "privacy_declaration"],
        expected_coverage: "full",
        answer_text:
          "user.device.cookie_id - Device cookie identifiers used for tracking and advertising. [6]",
        answer_status: "complete",
        answer_source: "system",
        confidence: 95,
        evidence: [],
        missing_data: [],
        sme_prompt: null,
      },
      {
        id: "3.2",
        question_id: "cpra_3_2",
        question_text:
          "What categories of sensitive personal information (SPI) are involved?",
        guidance:
          "List any sensitive personal information categories as defined under CPRA.",
        required: true,
        fides_sources: ["data_category", "privacy_declaration"],
        expected_coverage: "full",
        answer_text:
          "None - No sensitive personal information categories are processed. [6]",
        answer_status: "complete",
        answer_source: "system",
        confidence: 90,
        evidence: [],
        missing_data: [],
        sme_prompt: null,
      },
      {
        id: "3.3",
        question_id: "cpra_3_3",
        question_text:
          "For each SPI category, what is the specific data collected?",
        guidance:
          "For each sensitive PI category, describe the specific data elements collected.",
        required: false,
        fides_sources: ["data_category"],
        expected_coverage: "partial",
        answer_text:
          "N/A - No sensitive PI is involved in this processing activity. [7]",
        answer_status: "complete",
        answer_source: "system",
        confidence: 85,
        evidence: [],
        missing_data: [],
        sme_prompt: null,
      },
      {
        id: "3.4",
        question_id: "cpra_3_4",
        question_text:
          "Are there any data categories not yet mapped in your data inventory?",
        guidance:
          "Identify any data categories that may be processed but are not yet documented.",
        required: false,
        fides_sources: [],
        expected_coverage: "partial",
        answer_text: "",
        answer_status: "needs_input",
        answer_source: "slack",
        confidence: null,
        evidence: [],
        missing_data: [],
        sme_prompt:
          "Are there any data categories being processed that are not yet mapped in the data inventory?",
      },
    ],
  },
];

// =============================================================================
// Pre-built Mock Data - Evidence Items
// =============================================================================

export const MOCK_EVIDENCE_ITEMS: EvidenceItem[] = [
  // Group 1: Processing Scope and Purpose(s)
  mockSystemEvidence({
    id: "ev-sys-001",
    citation_number: 1,
    source: {
      source_type: "privacy_declaration",
      source_key: "demo_marketing_system.marketing_advertising",
      source_name: "Demo Marketing System - Advertising Declaration",
    },
    field: {
      field_name: "name",
      field_label: "Declaration Name",
    },
    value: "Collect data for marketing",
    value_display: "Collect data for marketing",
  }),
  mockSystemEvidence({
    id: "ev-sys-002",
    citation_number: 2,
    source: {
      source_type: "privacy_declaration",
      source_key: "demo_marketing_system.marketing_advertising",
      source_name: "Demo Marketing System - Advertising Declaration",
    },
    field: {
      field_name: "data_use",
      field_label: "Data Use",
    },
    value: "marketing.advertising",
    value_display: "Marketing / Advertising",
  }),

  // Group 2: Significant Risk Determination
  mockSystemEvidence({
    id: "ev-sys-003",
    citation_number: 3,
    source: {
      source_type: "data_use",
      source_key: "marketing.advertising",
      source_name: "Marketing - Advertising",
    },
    field: {
      field_name: "description",
      field_label: "Description",
    },
    value: "First and third party advertising purposes",
    value_display: "First and third party advertising purposes",
  }),
  mockSystemEvidence({
    id: "ev-sys-004",
    citation_number: 4,
    source: {
      source_type: "system",
      source_key: "demo_marketing_system",
      source_name: "Demo Marketing System",
    },
    field: {
      field_name: "system_type",
      field_label: "System Type",
    },
    value: "Marketing Platform",
    value_display: "Marketing Platform",
  }),
  mockManualEntryEvidence({
    id: "ev-manual-001",
    citation_number: 5,
    author: {
      user_id: "user_abc123",
      user_name: "Jack Gale",
      user_email: "jack@example.com",
      role: "Privacy Officer",
    },
    entry: {
      previous_value: null,
      new_value:
        "Processing involves ML analysis of customer purchase history and browsing behavior for personalized recommendations.",
      edit_reason: "Added details from internal documentation",
    },
  }),

  // Group 3: Categories of Personal Information
  mockSystemEvidence({
    id: "ev-sys-005",
    citation_number: 6,
    source: {
      source_type: "data_category",
      source_key: "user.device.cookie_id",
      source_name: "Cookie ID",
    },
    field: {
      field_name: "description",
      field_label: "Description",
    },
    value: "Device cookie identifiers",
    value_display: "Device cookie identifiers",
  }),
  mockSystemEvidence({
    id: "ev-sys-006",
    citation_number: 7,
    source: {
      source_type: "privacy_declaration",
      source_key: "demo_marketing_system.marketing_advertising",
      source_name: "Demo Marketing System - Advertising Declaration",
    },
    field: {
      field_name: "data_categories",
      field_label: "Data Categories",
    },
    value: ["user.device.cookie_id"],
    value_display: "user.device.cookie_id",
  }),
  mockManualEntryEvidence({
    id: "ev-manual-002",
    citation_number: 8,
    created_at: "2025-01-25T16:30:00Z",
    author: {
      user_id: "user_def456",
      user_name: "Sarah Chen",
      user_email: "sarah@example.com",
      role: "Legal Counsel",
    },
    entry: {
      previous_value: null,
      new_value:
        "Reviewed and confirmed data category mappings are complete for this processing activity.",
      edit_reason: null,
    },
  }),

  // Slack communication evidence
  mockSlackCommunicationEvidence({
    id: "ev-slack-001",
    citation_number: 9,
  }),
];

// =============================================================================
// Pre-built Mock Assessments
// =============================================================================

export const MOCK_ASSESSMENTS: PrivacyAssessmentResponse[] = [
  mockPrivacyAssessment({
    id: "collect_data_for_marketing",
    name: "Collect data for marketing",
    status: "in_progress",
    risk_level: "high",
    completeness: 53,
    system_fides_key: "demo_marketing_system",
    system_name: "Demo Marketing System",
    declaration_id: "collect_data_for_marketing",
    declaration_name: "Collect data for marketing",
    data_use: "marketing.advertising",
    data_use_name: "Advertising",
    data_categories: ["user.device.cookie_id"],
  }),
  mockPrivacyAssessment({
    id: "analyze_customer_behaviour",
    name: "Analyze customer behaviour for improvements",
    status: "in_progress",
    risk_level: "medium",
    completeness: 40,
    system_fides_key: "demo_analytics_system",
    system_name: "Demo Analytics System",
    declaration_id: "analyze_customer_behaviour",
    declaration_name: "Analyze customer behaviour for improvements",
    data_use: "functional.service.improve",
    data_use_name: "Service Improvement",
    data_categories: ["user.contact", "user.device.cookie_id"],
  }),
];

// =============================================================================
// Questionnaire Mock Data
// =============================================================================

export const MOCK_QUESTIONNAIRE_QUESTIONS: QuestionnaireQuestion[] = [
  {
    question_id: "cpra_1_3",
    question_text:
      "Why is this processing necessary for the business? What business need does it address?",
    status: "pending",
    answered_at: null,
    answered_by: null,
  },
  {
    question_id: "cpra_1_4",
    question_text:
      "What is the scale of processing (number of consumers, volume of data, geographic scope)?",
    status: "pending",
    answered_at: null,
    answered_by: null,
  },
  {
    question_id: "cpra_1_5",
    question_text: "How frequently does this processing occur?",
    status: "pending",
    answered_at: null,
    answered_by: null,
  },
  {
    question_id: "cpra_2_4",
    question_text:
      "Does this processing involve automated decision-making technology (ADMT)?",
    status: "answered",
    answered_at: "2025-01-14T11:45:00Z",
    answered_by: "Emily Rodriguez",
  },
  {
    question_id: "cpra_2_5",
    question_text:
      "What specific risks to consumers does this processing present?",
    status: "pending",
    answered_at: null,
    answered_by: null,
  },
  {
    question_id: "cpra_2_6",
    question_text:
      'Why does this processing meet the threshold for "significant risk"?',
    status: "pending",
    answered_at: null,
    answered_by: null,
  },
  {
    question_id: "cpra_3_4",
    question_text:
      "Are there any data categories not yet mapped in your data inventory?",
    status: "pending",
    answered_at: null,
    answered_by: null,
  },
];

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Calculate completeness percentage from question groups
 */
export const calculateCompleteness = (groups: QuestionGroup[]): number => {
  const allQuestions = groups.flatMap((g) => g.questions);
  if (allQuestions.length === 0) {
    return 0;
  }
  const answeredCount = allQuestions.filter(
    (q) => q.answer_text.trim().length > 0
  ).length;
  return Math.round((answeredCount / allQuestions.length) * 100);
};

/**
 * Determine assessment status based on completeness
 */
export const determineStatus = (completeness: number): AssessmentStatus => {
  if (completeness >= 100) {
    return "completed";
  }
  return "in_progress";
};

/**
 * Get evidence items for a specific question group
 */
export const getEvidenceForGroup = (
  groupId: string,
  evidence: EvidenceItem[]
): EvidenceItem[] => {
  // In a real implementation, evidence would be linked to specific questions
  // For mock purposes, we distribute evidence across groups
  const groupNum = parseInt(groupId, 10);
  return evidence.filter((e) => {
    const citationNum = e.citation_number ?? 0;
    if (groupNum === 1) {
      return citationNum <= 2;
    }
    if (groupNum === 2) {
      return citationNum >= 3 && citationNum <= 5;
    }
    if (groupNum === 3) {
      return citationNum >= 6;
    }
    return false;
  });
};
