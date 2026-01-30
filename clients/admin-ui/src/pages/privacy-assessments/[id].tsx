import {
  CheckCircleOutlined,
  DownloadOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import {
  Badge,
  Button,
  Card,
  Collapse,
  CUSTOM_TAG_COLOR,
  Descriptions,
  Divider,
  Drawer,
  Flex,
  Icons,
  Input,
  List,
  Modal,
  Result,
  Space,
  Tag,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useEffect, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  CPRAAssessmentAnswer,
  CPRAAssessmentQuestion,
  CPRAAssessmentResult,
  CPRADeclarationResult,
  FidesDataSource,
} from "~/features/plus/plus.slice";

import { EditableTextBlock } from "./components/EditableTextBlock";
import { SlackIcon } from "./components/SlackIcon";

// Storage key for API results
const ASSESSMENT_RESULTS_KEY = "privacy-assessments-api-results";

const { Title, Text } = Typography;
const { Panel } = Collapse;

// CSS for collapse styling with black left border on expanded items
const collapseStyles = `
  .privacy-assessment-collapse {
    max-width: 100%;
    overflow-x: hidden;
    border: 1px solid ${palette.FIDESUI_NEUTRAL_75};
    border-radius: 8px;
    overflow: visible;
  }
  .privacy-assessment-collapse .ant-collapse-item {
    border: none;
    border-left: 6px solid transparent;
    border-radius: 0;
    margin-bottom: 0;
    overflow: visible;
    position: relative;
    transition: border-left-color 0.2s ease;
    max-width: 100%;
  }
  .privacy-assessment-collapse .ant-collapse-item:not(:last-child) {
    border-bottom: 1px solid ${palette.FIDESUI_NEUTRAL_75};
  }
  .privacy-assessment-collapse .ant-collapse-item:first-child {
    border-top: none;
  }
  .privacy-assessment-collapse .ant-collapse-item:last-child {
    border-bottom: none;
  }
  .privacy-assessment-collapse .ant-collapse-item-active {
    border-left: 6px solid ${palette.FIDESUI_MINOS} !important;
  }
  .privacy-assessment-collapse .ant-collapse-header {
    display: flex;
    align-items: flex-start;
    min-height: 80px;
    padding: 16px 24px 20px 24px !important;
    padding-right: 140px !important;
    padding-left: 18px !important;
    position: relative;
    overflow: visible !important;
  }
  .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-header {
    min-height: 100px;
  }
  .privacy-assessment-collapse .ant-collapse-arrow {
    position: absolute;
    top: 20px;
    left: 18px;
    margin-top: 0 !important;
    display: flex;
    align-items: center;
    justify-content: center;
    height: auto;
    padding: 0 8px;
    z-index: 1;
  }
  .privacy-assessment-collapse .ant-collapse-header-text {
    margin-left: 40px;
    margin-right: 0;
    width: calc(100% - 40px);
    overflow: hidden;
  }
  .privacy-assessment-collapse .ant-collapse-header-text > div {
    max-width: 100%;
    overflow: hidden;
  }
  .privacy-assessment-collapse .ant-collapse-content-box {
    padding-top: 0;
  }
  .privacy-assessment-collapse .status-tag-container {
    position: absolute;
    right: 24px;
    top: 16px;
  }
`;

// Questions for the assessment - organized by groups
interface Question {
  id: string;
  question: string;
  answer: string;
  source: "system" | "derivable" | "slack";
  missingData?: string[]; // Fides field paths that could provide the answer if populated
}

interface QuestionGroup {
  id: string;
  title: string;
  questions: Question[];
}

// Evidence item types for the drawer
interface SystemEvidenceItem {
  id: string;
  groupId: string;
  type: "system";
  source: {
    system: string;
  };
  label?: string;
  content: string;
  timestamp: string;
  citationNumber?: number;
}

interface AnalysisEvidenceItem {
  id: string;
  groupId: string;
  type: "analysis";
  source: {
    model: string;
  };
  confidence: number;
  content: string;
  timestamp: string;
}

interface ThreadMessage {
  sender: string;
  message: string;
  timestamp: string;
}

interface HumanEvidenceItem {
  id: string;
  groupId: string;
  type: "human";
  subtype: "manual-entry" | "stakeholder-communication";
  source: {
    person: {
      name: string;
      role: string;
    };
  };
  content: string;
  timestamp: string;
  channel?: string;
  threadMessages?: ThreadMessage[];
  citationNumber?: number;
}

type EvidenceItem = SystemEvidenceItem | AnalysisEvidenceItem | HumanEvidenceItem;

// Mock evidence data
const mockEvidence: EvidenceItem[] = [
  // Group 1: Processing Scope and Purpose(s)
  {
    id: "ev-1",
    groupId: "1",
    type: "system",
    source: { system: "Demo Marketing System" },
    label: "Privacy declaration",
    content: "Data use: marketing.advertising - First and third party advertising purposes. System is configured for marketing data collection.",
    timestamp: "2025-01-28T10:30:00Z",
    citationNumber: 1,
  },
  {
    id: "ev-2",
    groupId: "1",
    type: "system",
    source: { system: "Fides Data Map" },
    label: "Data categories",
    content: "user.device.cookie_id mapped to Demo Marketing System. Data flow configured for advertising purposes.",
    timestamp: "2025-01-28T09:15:00Z",
    citationNumber: 2,
  },
  // Group 2: Significant Risk Determination
  {
    id: "ev-3",
    groupId: "2",
    type: "system",
    source: { system: "Fides Data Map" },
    label: "Data use classification",
    content: "marketing.advertising data use may involve third-party sharing. Cross-context behavioral advertising enabled.",
    timestamp: "2025-01-27T14:20:00Z",
    citationNumber: 3,
  },
  {
    id: "ev-4",
    groupId: "2",
    type: "system",
    source: { system: "Demo Marketing System" },
    label: "System configuration",
    content: "System uses marketing.advertising with cross-context behavioral advertising capabilities. No sensitive PI configured.",
    timestamp: "2025-01-27T11:00:00Z",
    citationNumber: 4,
  },
  {
    id: "ev-5",
    groupId: "2",
    type: "human",
    subtype: "manual-entry",
    source: { person: { name: "Jack Gale", role: "Privacy Officer" } },
    content:
      "Processing involves ML analysis of customer purchase history and browsing behavior for personalized recommendations.",
    timestamp: "2025-01-15T14:20:00Z",
    citationNumber: 5,
  },
  // Group 3: Categories of Personal/Sensitive Personal Information
  {
    id: "ev-6",
    groupId: "3",
    type: "system",
    source: { system: "Fides Data Map" },
    label: "Data categories",
    content: "user.device.cookie_id - Device cookie identifiers mapped. No sensitive PI categories detected in data map.",
    timestamp: "2025-01-28T08:00:00Z",
    citationNumber: 6,
  },
  {
    id: "ev-7",
    groupId: "3",
    type: "system",
    source: { system: "Demo Marketing System" },
    label: "System inventory",
    content: "N/A - No sensitive PI is involved. Only cookie identifiers processed for marketing purposes.",
    timestamp: "2025-01-28T07:30:00Z",
    citationNumber: 7,
  },
  {
    id: "ev-8",
    groupId: "3",
    type: "human",
    subtype: "manual-entry",
    source: { person: { name: "Sarah Chen", role: "Legal Counsel" } },
    content: "Reviewed and confirmed data category mappings are complete for this processing activity.",
    timestamp: "2025-01-25T16:30:00Z",
    citationNumber: 8,
  },
  {
    id: "ev-9",
    groupId: "2",
    type: "human",
    subtype: "stakeholder-communication",
    source: { person: { name: "Privacy Team", role: "Slack Thread" } },
    content: "Discussion: ADMT usage in marketing processing",
    channel: "#privacy-team",
    timestamp: "2025-01-14T10:30:00Z",
    citationNumber: 9,
    threadMessages: [
      {
        sender: "Jack Gale",
        message: "Does anyone know if we use any automated decision-making for the marketing personalization?",
        timestamp: "2025-01-14T10:30:00Z",
      },
      {
        sender: "Emily Rodriguez",
        message: "I checked with the engineering team - we use ML models for recommendations but no automated decisions that have legal effects on users.",
        timestamp: "2025-01-14T11:15:00Z",
      },
      {
        sender: "Jack Gale",
        message: "Thanks Emily! So we can confirm no ADMT is used for this processing activity.",
        timestamp: "2025-01-14T11:45:00Z",
      },
    ],
  },
];

// Helper function to render text with reference badges
// References are in the format [Label] e.g., [Demo Marketing System] or [Fides Data Map]
const renderTextWithReferences = (
  text: string,
  onReferenceClick?: (label: string) => void,
): React.ReactNode => {
  const referencePattern = /\[([^\]]+)\]/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match = referencePattern.exec(text);
  let refIndex = 0;

  while (match !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    const label = match[1];
    const currentRefIndex = refIndex;
    refIndex += 1;
    parts.push(
      <span
        key={`ref-${currentRefIndex}`}
        role="button"
        tabIndex={0}
        style={{
          display: "inline-flex",
          alignItems: "center",
          padding: "2px 8px",
          fontSize: 11,
          fontWeight: 500,
          color: "#4A6CF7",
          backgroundColor: "#F0F4FF",
          border: "1px solid #D6E4FF",
          borderRadius: 12,
          lineHeight: 1.2,
          transition: "all 0.2s ease",
          verticalAlign: "baseline",
          margin: "0 2px",
          cursor: "pointer",
        }}
        onMouseEnter={(e) => {
          const target = e.currentTarget;
          target.style.backgroundColor = "#E0E9FF";
          target.style.transform = "scale(1.05)";
          target.style.borderColor = "#B8D0FF";
        }}
        onMouseLeave={(e) => {
          const target = e.currentTarget;
          target.style.backgroundColor = "#F0F4FF";
          target.style.transform = "scale(1)";
          target.style.borderColor = "#D6E4FF";
        }}
        onClick={(e) => {
          e.stopPropagation();
          if (onReferenceClick) {
            onReferenceClick(label);
          }
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.stopPropagation();
            if (onReferenceClick) {
              onReferenceClick(label);
            }
          }
        }}
      >
        {label}
      </span>,
    );
    lastIndex = match.index + match[0].length;
    match = referencePattern.exec(text);
  }
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }
  // eslint-disable-next-line react/jsx-no-useless-fragment
  return <>{parts}</>;
};

// CPRA Risk Assessment questions with pre-filled answers from demo data
const initialQuestionGroups: QuestionGroup[] = [
  {
    id: "1",
    title: "Processing Scope and Purpose(s)",
    questions: [
      {
        id: "1.1",
        question: "What is the name and description of this processing activity?",
        answer:
          "Collect data for marketing - Collect data about our users for marketing. [1]",
        source: "system",
      },
      {
        id: "1.2",
        question:
          "What are the specific purposes for processing personal information?",
        answer:
          "marketing.advertising - First and third party advertising purposes. [2]",
        source: "system",
      },
      {
        id: "1.3",
        question:
          "Why is this processing necessary for the business? What business need does it address?",
        answer: "",
        source: "slack",
      },
      {
        id: "1.4",
        question:
          "What is the scale of processing (number of consumers, volume of data, geographic scope)?",
        answer: "",
        source: "slack",
      },
      {
        id: "1.5",
        question: "How frequently does this processing occur?",
        answer: "",
        source: "slack",
      },
    ],
  },
  {
    id: "2",
    title: "Significant Risk Determination",
    questions: [
      {
        id: "2.1",
        question: "Does this processing involve selling personal information?",
        answer:
          "Potential - The marketing.advertising data use may involve sharing with third parties for advertising purposes. [3]",
        source: "system",
      },
      {
        id: "2.2",
        question:
          "Does this processing involve sharing PI for cross-context behavioral advertising?",
        answer:
          "Yes - Processing uses marketing.advertising which typically involves cross-context behavioral advertising. [4]",
        source: "system",
      },
      {
        id: "2.3",
        question:
          "Does this processing involve sensitive personal information?",
        answer:
          "No - Only user.device.cookie_id is processed, which is not classified as sensitive PI. [3]",
        source: "system",
      },
      {
        id: "2.4",
        question:
          "Does this processing involve automated decision-making technology (ADMT)?",
        answer: "",
        source: "slack",
      },
      {
        id: "2.5",
        question:
          "What specific risks to consumers does this processing present?",
        answer: "",
        source: "slack",
      },
      {
        id: "2.6",
        question:
          'Why does this processing meet the threshold for "significant risk"?',
        answer: "",
        source: "slack",
      },
    ],
  },
  {
    id: "3",
    title: "Categories of Personal/Sensitive Personal Information",
    questions: [
      {
        id: "3.1",
        question:
          "What categories of personal information are collected and processed?",
        answer:
          "user.device.cookie_id - Device cookie identifiers used for tracking and advertising. [6]",
        source: "system",
      },
      {
        id: "3.2",
        question:
          "What categories of sensitive personal information (SPI) are involved?",
        answer:
          "None - No sensitive personal information categories are processed. [6]",
        source: "system",
      },
      {
        id: "3.3",
        question:
          "For each SPI category, what is the specific data collected?",
        answer:
          "N/A - No sensitive PI is involved in this processing activity. [7]",
        source: "system",
      },
      {
        id: "3.4",
        question:
          "Are there any data categories not yet mapped in your data inventory?",
        answer: "",
        source: "slack",
      },
    ],
  },
];

const ASSESSMENTS_STORAGE_KEY = "privacy-assessments-data";
const QUESTIONNAIRE_STATUS_KEY = "privacy-assessments-questionnaire-status";
const QUESTION_ANSWERS_KEY = "privacy-assessments-question-answers";

// Mock assessment data based on demo privacy declarations
const assessmentData: Record<
  string,
  {
    name: string;
    system: string;
    riskLevel: string;
    dataCategories: string[];
    dataUse: string;
  }
> = {
  analyze_customer_behaviour: {
    name: "Analyze customer behaviour for improvements",
    system: "Demo Analytics System",
    riskLevel: "Med",
    dataCategories: ["user.contact", "user.device.cookie_id"],
    dataUse: "functional.service.improve",
  },
  collect_data_for_marketing: {
    name: "Collect data for marketing",
    system: "Demo Marketing System",
    riskLevel: "High",
    dataCategories: ["user.device.cookie_id"],
    dataUse: "marketing.advertising",
  },
};

// Helper to extract group and question numbers from API question ID
// e.g., "cpra_1_1" -> { group: "1", question: "1.1" }
const parseQuestionId = (
  id: string
): { group: string; questionNum: string } => {
  // Match pattern like "cpra_1_1" or "cpra_2_3"
  const match = id.match(/cpra_(\d+)_(\d+)/);
  if (match) {
    return {
      group: match[1],
      questionNum: `${match[1]}.${match[2]}`,
    };
  }
  // Fallback: try to extract any numbers
  const nums = id.match(/\d+/g);
  if (nums && nums.length >= 2) {
    return {
      group: nums[0],
      questionNum: `${nums[0]}.${nums[1]}`,
    };
  }
  return { group: "1", questionNum: "1.1" };
};

// Map requirement_key to human-readable group titles
const requirementKeyToTitle: Record<string, string> = {
  processing_scope: "Processing Scope and Purpose(s)",
  significant_risk_determination: "Significant Risk Determination",
  data_categories: "Categories of Personal Information",
  sensitive_pi: "Sensitive Personal Information",
  consumer_notification: "Consumer Notification",
  consumer_rights: "Consumer Rights",
  retention: "Data Retention",
  third_party_sharing: "Third Party Sharing",
  security: "Data Security",
  safeguards: "Safeguards and Mitigation",
};

// Helper to map API questions to UI question groups
const mapApiQuestionsToGroups = (
  questions: CPRAAssessmentQuestion[],
  answers: CPRAAssessmentAnswer[],
): QuestionGroup[] => {
  // Create a map of answers by question_id for quick lookup
  const answerMap = new Map<string, CPRAAssessmentAnswer>();
  answers.forEach((a) => answerMap.set(a.question_id, a));

  // Group questions by their group number extracted from ID
  const groupMap = new Map<
    string,
    { title: string; requirementKey: string; questions: Question[] }
  >();

  questions.forEach((q) => {
    const { group: groupId, questionNum } = parseQuestionId(q.id);
    const answer = answerMap.get(q.id);

    if (!groupMap.has(groupId)) {
      // Get title from requirement_key mapping or format it nicely
      const title =
        requirementKeyToTitle[q.requirement_key] ||
        q.requirement_key
          .split("_")
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" ");

      groupMap.set(groupId, {
        title,
        requirementKey: q.requirement_key,
        questions: [],
      });
    }

    const group = groupMap.get(groupId)!;

    // Determine source based on answer status
    let source: "system" | "derivable" | "slack" = "slack";
    if (answer?.status === "complete") {
      source = "system";
    } else if (answer?.status === "partial") {
      source = "derivable";
    }

    group.questions.push({
      id: questionNum,
      question: q.question_text,
      answer: answer?.answer_text || "",
      source,
      missingData: answer?.missing_data,
    });
  });

  // Convert map to array and sort by group ID
  return Array.from(groupMap.entries())
    .sort(([a], [b]) => parseInt(a, 10) - parseInt(b, 10))
    .map(([groupId, group]) => ({
      id: groupId,
      title: group.title,
      questions: group.questions.sort((a, b) => {
        const aNum = parseFloat(a.id);
        const bNum = parseFloat(b.id);
        return aNum - bNum;
      }),
    }));
};

// Human-readable labels for field names
const fieldNameLabels: Record<string, string> = {
  name: "Name",
  description: "Description",
  data_use: "Data Use",
  data_categories: "Data Categories",
  data_subjects: "Data Subjects",
  fides_key: "Fides Key",
  legal_basis_for_processing: "Legal Basis",
  retention_period: "Retention Period",
  processes_special_category_data: "Processes Special Category Data",
  data_shared_with_third_parties: "Shared with Third Parties",
  third_parties: "Third Parties",
  system_type: "System Type",
};

// Human-readable labels for source types
const sourceTypeLabels: Record<string, string> = {
  system: "System",
  privacy_declaration: "Privacy Declaration",
  data_category: "Data Category",
  data_use: "Data Use",
  data_subject: "Data Subject",
};

// Format a value for display (remove quotes from strings, format arrays nicely)
const formatValue = (value: unknown): string => {
  if (value === null || value === undefined) return "N/A";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.length > 0 ? value.join(", ") : "None";
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return JSON.stringify(value);
};

// Helper to map FidesDataSource to evidence items
const mapFidesDataToEvidence = (
  answers: CPRAAssessmentAnswer[],
  questions: CPRAAssessmentQuestion[],
): EvidenceItem[] => {
  const evidence: EvidenceItem[] = [];
  let citationNum = 1;

  // Create a map of questions by ID for lookup
  const questionMap = new Map<string, CPRAAssessmentQuestion>();
  questions.forEach((q) => questionMap.set(q.id, q));

  answers.forEach((answer) => {
    const question = questionMap.get(answer.question_id);
    if (!question) return;

    // Extract group ID from question ID (e.g., "cpra_1_1" -> "1")
    const { group: groupId } = parseQuestionId(question.id);

    // Map fides_data_used to system evidence
    if (answer.fides_data_used && answer.fides_data_used.length > 0) {
      answer.fides_data_used.forEach((source) => {
        // Get human-readable source name
        const sourceTypeLabel =
          sourceTypeLabels[source.source_type] || source.source_type;
        const systemName = source.source_key
          ? `${sourceTypeLabel}: ${source.source_key}`
          : sourceTypeLabel;

        // Get human-readable field label
        const fieldLabel = source.field_name
          ? fieldNameLabels[source.field_name] ||
            source.field_name
              .split("_")
              .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
              .join(" ")
          : sourceTypeLabel;

        // Format content without duplicate prefixes
        const formattedValue = formatValue(source.value);
        const content = formattedValue;

        evidence.push({
          id: `ev-${citationNum}`,
          groupId,
          type: "system",
          source: { system: systemName },
          label: fieldLabel,
          content,
          timestamp: new Date().toISOString(),
          citationNumber: citationNum,
        });
        citationNum += 1;
      });
    }
  });

  return evidence;
};

const PrivacyAssessmentDetailPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const message = useMessage();
  const { id } = router.query;
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [questionGroups, setQuestionGroups] = useState<QuestionGroup[]>([]);
  const [evidenceItems, setEvidenceItems] = useState<EvidenceItem[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [apiResult, setApiResult] = useState<CPRAAssessmentResult | null>(null);
  const [declarationResult, setDeclarationResult] =
    useState<CPRADeclarationResult | null>(null);
  const [questionnaireSentAt, setQuestionnaireSentAt] = useState<Date | null>(
    null,
  );
  const [timeSinceSent, setTimeSinceSent] = useState<string>("");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [focusedGroupId, setFocusedGroupId] = useState<string | null>(null);
  const [evidenceSearchQuery, setEvidenceSearchQuery] = useState("");

  // Flatten all questions from groups for progress calculations
  const allQuestions = questionGroups.flatMap((g) => g.questions);

  // Calculate progress for slack questions
  const slackQuestions = allQuestions.filter((q) => q.source === "slack");
  const answeredSlackQuestions = slackQuestions.filter(
    (q) => q.answer.trim().length > 0,
  );
  const slackProgress = `${answeredSlackQuestions.length}/${slackQuestions.length}`;

  // Assessment is complete when all questions have answers
  const isComplete = allQuestions.every((q) => q.answer.trim().length > 0);

  // Load API results from localStorage and initialize question groups
  useEffect(() => {
    if (!id) return;

    const storedResults = localStorage.getItem(ASSESSMENT_RESULTS_KEY);
    if (storedResults) {
      try {
        const result = JSON.parse(storedResults) as CPRAAssessmentResult;
        setApiResult(result);

        // Find the declaration result for this assessment ID
        const declResult = result.declaration_results[id as string];
        if (declResult) {
          setDeclarationResult(declResult);

          // Map API data to UI format
          const groups = mapApiQuestionsToGroups(
            result.questions,
            declResult.answers,
          );
          setQuestionGroups(groups);

          // Map fides_data_used to evidence
          const evidence = mapFidesDataToEvidence(
            declResult.answers,
            result.questions,
          );
          setEvidenceItems(evidence);
        } else {
          // Fallback to initial questions if no declaration found
          setQuestionGroups(initialQuestionGroups);
          setEvidenceItems(mockEvidence);
        }
      } catch {
        // Invalid data, use fallback
        setQuestionGroups(initialQuestionGroups);
        setEvidenceItems(mockEvidence);
      }
    } else {
      // No API results, use initial values
      setQuestionGroups(initialQuestionGroups);
      setEvidenceItems(mockEvidence);
    }
  }, [id]);

  // Load any user-edited answers from localStorage (merges with API answers)
  useEffect(() => {
    if (!id || questionGroups.length === 0) return;

    const stored = localStorage.getItem(QUESTION_ANSWERS_KEY);
    if (stored) {
      try {
        const answersData = JSON.parse(stored);
        if (answersData[id as string]) {
          const savedAnswers = answersData[id as string] as Record<string, string>;
          setQuestionGroups((prev) =>
            prev.map((group) => ({
              ...group,
              questions: group.questions.map((q) => ({
                ...q,
                answer: savedAnswers[q.id] ?? q.answer,
              })),
            })),
          );
        }
      } catch {
        // Invalid data, ignore
      }
    }
  }, [id, questionGroups.length === 0]); // Only run when groups are first loaded

  // Save question answers to localStorage and update completeness when answers change
  useEffect(() => {
    if (!id) return;

    // Save answers to localStorage
    const answers: Record<string, string> = {};
    allQuestions.forEach((q) => {
      answers[q.id] = q.answer;
    });

    const stored = localStorage.getItem(QUESTION_ANSWERS_KEY);
    const answersData = stored ? JSON.parse(stored) : {};
    answersData[id as string] = answers;
    localStorage.setItem(QUESTION_ANSWERS_KEY, JSON.stringify(answersData));

    // Update completeness in assessments data
    const answeredCount = allQuestions.filter(
      (q) => q.answer.trim().length > 0,
    ).length;
    const completeness = Math.round((answeredCount / allQuestions.length) * 100);

    const assessmentsStored = localStorage.getItem(ASSESSMENTS_STORAGE_KEY);
    if (assessmentsStored) {
      try {
        const assessmentsData = JSON.parse(assessmentsStored);
        if (assessmentsData.cpra?.assessments) {
          assessmentsData.cpra.assessments = assessmentsData.cpra.assessments.map(
            (a: { id: string; completeness: number }) =>
              a.id === id ? { ...a, completeness } : a,
          );
          localStorage.setItem(
            ASSESSMENTS_STORAGE_KEY,
            JSON.stringify(assessmentsData),
          );
        }
      } catch {
        // Invalid data, ignore
      }
    }
  }, [id, allQuestions]);

  // Load questionnaire status from localStorage on mount
  useEffect(() => {
    if (!id) return;
    const stored = localStorage.getItem(QUESTIONNAIRE_STATUS_KEY);
    if (stored) {
      try {
        const statusData = JSON.parse(stored);
        if (statusData[id as string]) {
          setQuestionnaireSentAt(new Date(statusData[id as string]));
        }
      } catch {
        // Invalid data, ignore
      }
    }
  }, [id]);

  // Update time since sent
  useEffect(() => {
    if (!questionnaireSentAt) return undefined;

    const updateTime = () => {
      const now = new Date();
      const diffMs = now.getTime() - questionnaireSentAt.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffDays > 0) {
        setTimeSinceSent(`${diffDays}d ago`);
      } else if (diffHours > 0) {
        setTimeSinceSent(`${diffHours}h ago`);
      } else if (diffMins > 0) {
        setTimeSinceSent(`${diffMins}m ago`);
      } else {
        setTimeSinceSent("Just now");
      }
    };

    updateTime();
    const interval = setInterval(updateTime, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [questionnaireSentAt]);

  const handleAnswerChange = (questionId: string, newAnswer: string) => {
    setQuestionGroups((prev) =>
      prev.map((group) => ({
        ...group,
        questions: group.questions.map((q) =>
          q.id === questionId ? { ...q, answer: newAnswer } : q,
        ),
      })),
    );
  };

  const handleComment = (selection: {
    text: string;
    start: number;
    end: number;
  }) => {
    message.success(
      `Comment added on "${selection.text.substring(0, 30)}${selection.text.length > 30 ? "..." : ""}"`
    );
  };

  const handleRequestInput = () => {
    const sentAt = new Date();
    setQuestionnaireSentAt(sentAt);

    // Save to localStorage
    if (id) {
      const stored = localStorage.getItem(QUESTIONNAIRE_STATUS_KEY);
      const statusData = stored ? JSON.parse(stored) : {};
      statusData[id as string] = sentAt.toISOString();
      localStorage.setItem(QUESTIONNAIRE_STATUS_KEY, JSON.stringify(statusData));
    }

    message.success("Questionnaire sent to #privacy-team on Slack.");
  };

  const handleSendReminder = () => {
    message.success("Reminder sent to #privacy-team.");
  };

  const handleViewEvidence = (groupId: string) => {
    setFocusedGroupId(groupId);
    setIsDrawerOpen(true);
  };

  // Filter evidence based on search query
  const filteredEvidence = evidenceItems.filter((item) => {
    if (!evidenceSearchQuery) return true;
    const query = evidenceSearchQuery.toLowerCase();

    // Check content
    if (item.content.toLowerCase().includes(query)) return true;

    // Check source based on type
    if (item.type === "system") {
      return item.source.system.toLowerCase().includes(query);
    }
    if (item.type === "analysis") {
      return item.source.model.toLowerCase().includes(query);
    }
    if (item.type === "human") {
      return (
        item.source.person.name.toLowerCase().includes(query) ||
        item.source.person.role.toLowerCase().includes(query)
      );
    }
    return false;
  });

  // Group evidence by group ID
  const evidenceByGroup = filteredEvidence.reduce(
    (acc, item) => {
      if (!acc[item.groupId]) {
        acc[item.groupId] = [];
      }
      acc[item.groupId].push(item);
      return acc;
    },
    {} as Record<string, EvidenceItem[]>,
  );

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  // Convert confidence percentage to High/Medium/Low
  const getConfidenceLevel = (confidence: number): string => {
    if (confidence >= 80) return "High";
    if (confidence >= 50) return "Medium";
    return "Low";
  };

  const handleDelete = () => {
    // Get current assessments from localStorage
    const stored = localStorage.getItem(ASSESSMENTS_STORAGE_KEY);
    if (stored && id) {
      try {
        const data = JSON.parse(stored);
        const updatedAssessments = data.cpra.assessments.filter(
          (a: { id: string }) => a.id !== id,
        );
        if (updatedAssessments.length === 0) {
          localStorage.removeItem(ASSESSMENTS_STORAGE_KEY);
        } else {
          localStorage.setItem(
            ASSESSMENTS_STORAGE_KEY,
            JSON.stringify({
              ...data,
              cpra: {
                ...data.cpra,
                assessments: updatedAssessments,
              },
            }),
          );
        }
      } catch {
        // Invalid data, just remove it
        localStorage.removeItem(ASSESSMENTS_STORAGE_KEY);
      }
    }

    // Remove questionnaire status for this assessment
    if (id) {
      const statusStored = localStorage.getItem(QUESTIONNAIRE_STATUS_KEY);
      if (statusStored) {
        try {
          const statusData = JSON.parse(statusStored);
          delete statusData[id as string];
          if (Object.keys(statusData).length === 0) {
            localStorage.removeItem(QUESTIONNAIRE_STATUS_KEY);
          } else {
            localStorage.setItem(
              QUESTIONNAIRE_STATUS_KEY,
              JSON.stringify(statusData),
            );
          }
        } catch {
          // Invalid data, just remove it
          localStorage.removeItem(QUESTIONNAIRE_STATUS_KEY);
        }
      }

      // Remove question answers for this assessment
      const answersStored = localStorage.getItem(QUESTION_ANSWERS_KEY);
      if (answersStored) {
        try {
          const answersData = JSON.parse(answersStored);
          delete answersData[id as string];
          if (Object.keys(answersData).length === 0) {
            localStorage.removeItem(QUESTION_ANSWERS_KEY);
          } else {
            localStorage.setItem(
              QUESTION_ANSWERS_KEY,
              JSON.stringify(answersData),
            );
          }
        } catch {
          // Invalid data, just remove it
          localStorage.removeItem(QUESTION_ANSWERS_KEY);
        }
      }
    }
    message.success("Assessment deleted.");
    setIsDeleteModalOpen(false);
    router.push(PRIVACY_ASSESSMENTS_ROUTE);
  };

  if (!flags?.alphaDataProtectionAssessments) {
    return (
      <Layout title="Privacy Assessment">
        <Result
          status="error"
          title="Feature not available"
          subTitle="This feature is currently behind a feature flag and is not enabled."
        />
      </Layout>
    );
  }

  // Use declaration result from API if available, otherwise fallback to hardcoded data
  const assessment = useMemo(() => {
    if (declarationResult) {
      // Use new friendly name fields from API, with fallbacks
      const dataUse = declarationResult.data_use || "processing.general";
      const dataUseName = declarationResult.data_use_name || dataUse;
      const systemName =
        declarationResult.system_name ||
        declarationResult.system_fides_key ||
        "Unknown System";

      // Use declaration_name if set, otherwise fall back to data_use_name
      const declarationName =
        declarationResult.declaration_name ||
        dataUseName ||
        `Assessment ${id}`;

      // Get data categories from metadata (still needed for display)
      const dataCategories =
        (apiResult?.metadata?.data_categories as string[]) || [];

      return {
        name: declarationName,
        system: systemName,
        riskLevel: "Med" as const, // Could be computed from answers
        dataCategories,
        dataUse: dataUseName,
      };
    }
    // Fallback to hardcoded data
    return id ? assessmentData[id as string] : null;
  }, [declarationResult, apiResult, id]);

  const assessmentName = assessment?.name ?? "Assessment";

  return (
    <Layout title={`Privacy Assessment - ${assessmentName}`}>
      <PageHeader
        heading="Privacy assessments"
        breadcrumbItems={[
          { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
          {
            title: (
              <Flex align="center" gap="small" wrap="wrap">
                <span>{assessmentName}</span>
                <Tag
                  style={{
                    fontSize: 12,
                    margin: 0,
                    backgroundColor: palette.FIDESUI_NEUTRAL_300,
                    border: "none",
                    color: palette.FIDESUI_MINOS,
                  }}
                >
                  CPRA
                </Tag>
              </Flex>
            ),
          },
        ]}
        rightContent={
          <Space>
            <Tooltip title="Delete assessment">
              <Button
                type="text"
                danger
                onClick={() => setIsDeleteModalOpen(true)}
                aria-label="Delete assessment"
                style={{ padding: "4px 8px" }}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 32 32"
                  fill="currentColor"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M12 12H14V24H12V12Z" />
                  <path d="M18 12H20V24H18V12Z" />
                  <path d="M4 6V8H6V28C6 28.5304 6.21071 29.0391 6.58579 29.4142C6.96086 29.7893 7.46957 30 8 30H24C24.5304 30 25.0391 29.7893 25.4142 29.4142C25.7893 29.0391 26 28.5304 26 28V8H28V6H4ZM8 28V8H24V28H8Z" />
                  <path d="M12 2H20V4H12V2Z" />
                </svg>
              </Button>
            </Tooltip>
            <Tooltip
              title={
                !isComplete
                  ? "Assessment must be complete before generating a report"
                  : undefined
              }
            >
              <Button type="primary" disabled={!isComplete}>
                Generate report
              </Button>
            </Tooltip>
          </Space>
        }
      />
      <div style={{ padding: "0 24px 24px 24px" }}>
        <Space direction="vertical" size="small" style={{ width: "100%" }}>
          <div>
            <Flex align="center" gap="small" style={{ marginBottom: 4 }}>
              <Title level={4} style={{ margin: 0 }}>
                {assessmentName}
              </Title>
              <Tag
                color={
                  isComplete ? CUSTOM_TAG_COLOR.SUCCESS : CUSTOM_TAG_COLOR.DEFAULT
                }
              >
                {isComplete ? "Completed" : "In progress"}
              </Tag>
            </Flex>
            <Text type="secondary" style={{ display: "block", marginBottom: 8, fontSize: 12 }}>
              System: {assessment?.system}
            </Text>
            <Text
              type="secondary"
              style={{
                fontSize: 14,
                lineHeight: "28px",
                display: "block",
              }}
            >
              Processing{" "}
              {assessment?.dataCategories.map((category, idx) => (
                <span key={category}>
                  <Tag
                    color={CUSTOM_TAG_COLOR.DEFAULT}
                    style={{
                      margin: 0,
                      fontSize: 12,
                      verticalAlign: "middle",
                    }}
                  >
                    {category}
                  </Tag>
                  {idx < (assessment?.dataCategories.length ?? 0) - 1 && " "}
                </span>
              ))}{" "}
              for{" "}
              <Tag
                color={CUSTOM_TAG_COLOR.DEFAULT}
                style={{
                  margin: 0,
                  fontSize: 12,
                  verticalAlign: "middle",
                }}
              >
                {assessment?.dataUse}
              </Tag>
            </Text>
          </div>

          {!isComplete && (
            <>
              {!questionnaireSentAt ? (
                <Flex justify="flex-end">
                  <Button
                    icon={<SlackIcon size={14} />}
                    size="small"
                    onClick={handleRequestInput}
                  >
                    Request input from team
                  </Button>
                </Flex>
              ) : (
                <div
                  style={{
                    backgroundColor: palette.FIDESUI_BG_CORINTH,
                    borderRadius: 8,
                    padding: "16px",
                    width: "100%",
                  }}
                >
                  <Flex justify="space-between" align="center">
                    <Flex align="center" gap="middle">
                      <Flex align="center" gap="small">
                        <CheckCircleOutlined
                          style={{
                            color: palette.FIDESUI_SUCCESS,
                            fontSize: 16,
                          }}
                        />
                        <Text strong style={{ fontSize: 13 }}>
                          Questionnaire sent
                        </Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Sent {timeSinceSent} to #privacy-team
                      </Text>
                      <Flex align="center" gap="small">
                        <Text style={{ fontSize: 12 }}>Progress:</Text>
                        <Tag
                          color={
                            answeredSlackQuestions.length === slackQuestions.length
                              ? CUSTOM_TAG_COLOR.SUCCESS
                              : CUSTOM_TAG_COLOR.DEFAULT
                          }
                          style={{ margin: 0 }}
                        >
                          {slackProgress} answered
                        </Tag>
                      </Flex>
                    </Flex>
                    <Button
                      icon={<SlackIcon size={14} />}
                      size="small"
                      onClick={handleSendReminder}
                    >
                      Send reminder
                    </Button>
                  </Flex>
                </div>
              )}
            </>
          )}

          {/* eslint-disable-next-line react/no-danger */}
          <style dangerouslySetInnerHTML={{ __html: collapseStyles }} />

          <Collapse
            activeKey={expandedKeys}
            onChange={(keys) => setExpandedKeys(keys as string[])}
            className="privacy-assessment-collapse"
            style={{
              backgroundColor: "white",
              width: "100%",
              maxWidth: "100%",
            }}
          >
            {questionGroups.map((group) => {
              const answeredCount = group.questions.filter(
                (q) => q.answer.trim().length > 0,
              ).length;
              const totalCount = group.questions.length;
              const isGroupCompleted = answeredCount === totalCount;
              const isExpanded = expandedKeys.includes(group.id);
              return (
                <Panel
                  key={group.id}
                  header={
                    <>
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12 }}
                          >
                            <Text strong style={{ fontSize: 16 }}>
                              {group.id}. {group.title}
                            </Text>
                          </Flex>
                          <Flex
                            gap="middle"
                            align="center"
                            wrap="wrap"
                            style={{ marginBottom: 8 }}
                          >
                            <Text
                              type="secondary"
                              style={{
                                fontSize: 11,
                                lineHeight: "16px",
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                            >
                              Updated 2m ago by{" "}
                              <Tag
                                color={CUSTOM_TAG_COLOR.DEFAULT}
                                style={{ marginLeft: 4 }}
                              >
                                JG
                              </Tag>
                            </Text>
                            <Text
                              type="secondary"
                              style={{
                                fontSize: 11,
                                lineHeight: "16px",
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                            >
                              <Text strong style={{ fontSize: 11 }}>
                                Fields:
                              </Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {answeredCount}/{totalCount}
                              </span>
                            </Text>
                            <Flex
                              gap="small"
                              align="center"
                              style={{
                                fontSize: 11,
                                color: palette.FIDESUI_NEUTRAL_600,
                              }}
                            >
                              <div
                                style={{
                                  width: 6,
                                  height: 6,
                                  borderRadius: "50%",
                                  backgroundColor: palette.FIDESUI_SUCCESS,
                                }}
                              />
                              <Text style={{ fontSize: 11 }}>Risk: Low</Text>
                            </Flex>
                          </Flex>
                          {isExpanded && (
                            <Flex
                              align="center"
                              gap="small"
                              style={{ marginTop: 12 }}
                            >
                              <Button
                                type="default"
                                icon={<Icons.Document />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleViewEvidence(group.id);
                                }}
                                size="small"
                              >
                                View evidence
                              </Button>
                            </Flex>
                          )}
                        </div>
                      </Flex>
                      <div className="status-tag-container">
                        <Tag
                          color={
                            isGroupCompleted
                              ? CUSTOM_TAG_COLOR.SUCCESS
                              : CUSTOM_TAG_COLOR.DEFAULT
                          }
                        >
                          {isGroupCompleted ? "Completed" : "Pending"}
                        </Tag>
                      </div>
                    </>
                  }
                >
                  <Space
                    direction="vertical"
                    size="middle"
                    style={{ width: "100%" }}
                  >
                    {group.questions.map((q) => (
                      <div
                        key={q.id}
                        style={{
                          backgroundColor: palette.FIDESUI_BG_CORINTH,
                          padding: "16px 16px 8px 16px",
                          borderRadius: 8,
                        }}
                      >
                        <Flex
                          justify="space-between"
                          align="center"
                          style={{ marginBottom: 12 }}
                        >
                          <Text strong>
                            {q.id}. {q.question}
                          </Text>
                          {q.source === "derivable" ? (
                            <Tooltip
                              title={
                                q.missingData && q.missingData.length > 0
                                  ? `This answer can be automatically derived if you populate: ${q.missingData.join(", ")}`
                                  : "This answer can be derived from Fides data if the relevant field is populated"
                              }
                            >
                              <Tag color={CUSTOM_TAG_COLOR.WARNING}>
                                System derivable
                              </Tag>
                            </Tooltip>
                          ) : (
                            <Tag
                              color={
                                q.source === "system"
                                  ? CUSTOM_TAG_COLOR.SUCCESS
                                  : CUSTOM_TAG_COLOR.DEFAULT
                              }
                            >
                              {q.source === "system"
                                ? "System derived"
                                : "Team input"}
                            </Tag>
                          )}
                        </Flex>
                        <EditableTextBlock
                          value={q.answer}
                          onChange={(newValue) => handleAnswerChange(q.id, newValue)}
                          placeholder="Enter your answer..."
                          onComment={handleComment}
                          onRequestInput={
                            q.source === "slack" ? handleRequestInput : undefined
                          }
                          renderContent={(text) =>
                            renderTextWithReferences(text, () =>
                              handleViewEvidence(group.id),
                            )
                          }
                        />
                      </div>
                    ))}
                  </Space>
                </Panel>
              );
            })}
          </Collapse>
        </Space>
      </div>

      <Modal
        title="Delete assessment"
        open={isDeleteModalOpen}
        onCancel={() => setIsDeleteModalOpen(false)}
        onOk={handleDelete}
        okText="Delete"
        okButtonProps={{ danger: true }}
      >
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Text>Are you sure you want to delete this assessment?</Text>
          <Text type="secondary">
            This action cannot be undone. All assessment data, including any
            responses and documentation, will be permanently removed.
          </Text>
        </Space>
      </Modal>

      <Drawer
        title={
          <Flex
            justify="space-between"
            align="center"
            style={{ width: "100%" }}
          >
            <div>
              <Title
                level={5}
                style={{ margin: 0, color: "#1A1F36", fontWeight: 600 }}
              >
                Evidence
              </Title>
              <Text type="secondary" style={{ fontSize: 13, color: "#6B7280" }}>
                Complete evidence trail organized by question
              </Text>
            </div>
            <Button
              type="text"
              icon={<DownloadOutlined />}
              size="small"
              onClick={() => {
                message.success("Evidence report exported");
              }}
            >
              Export
            </Button>
          </Flex>
        }
        placement="right"
        onClose={() => {
          setIsDrawerOpen(false);
          setFocusedGroupId(null);
          setEvidenceSearchQuery("");
        }}
        open={isDrawerOpen}
        width={600}
        styles={{
          body: {
            padding: 0,
            display: "flex",
            flexDirection: "column",
            height: "100%",
            backgroundColor: "#FAFBFC",
          },
        }}
      >
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid #E8EBED",
            backgroundColor: "#FFFFFF",
          }}
        >
          <Input
            placeholder="Search evidence..."
            prefix={<SearchOutlined style={{ color: "#6B7280" }} />}
            value={evidenceSearchQuery}
            onChange={(e) => setEvidenceSearchQuery(e.target.value)}
            allowClear
            style={{
              borderRadius: 8,
              border: "1px solid #E8EBED",
            }}
          />
        </div>
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px",
            backgroundColor: "#FAFBFC",
          }}
        >
          <Space direction="vertical" size="large" style={{ width: "100%" }}>
            {questionGroups
              .filter((group) => focusedGroupId === group.id)
              .map((group) => {
                const groupEvidence = evidenceByGroup[group.id] || [];
                const systemEvidence = groupEvidence.filter(
                  (e) => e.type === "system",
                ) as SystemEvidenceItem[];
                const humanEvidence = groupEvidence.filter(
                  (e) => e.type === "human",
                ) as HumanEvidenceItem[];

                return (
                  <div key={group.id} data-group-id={group.id}>
                    {/* Question Title */}
                    <Text
                      strong
                      style={{
                        fontSize: 15,
                        fontWeight: 600,
                        color: "#1A1F36",
                        display: "block",
                        marginBottom: 20,
                      }}
                    >
                      {group.id}. {group.title}
                    </Text>

                  {/* System-Derived Data Section */}
                  {systemEvidence.length > 0 && (
                    <div style={{ marginBottom: 20 }}>
                      <Flex
                        align="center"
                        justify="space-between"
                        style={{ marginBottom: 12 }}
                      >
                        <Text
                          strong
                          style={{
                            fontSize: 14,
                            fontWeight: 600,
                            color: "#1A1F36",
                          }}
                        >
                          System-derived data
                        </Text>
                      </Flex>
                      <Text
                        type="secondary"
                        style={{
                          fontSize: 13,
                          display: "block",
                          marginBottom: 16,
                          color: "#6B7280",
                          lineHeight: 1.6,
                        }}
                      >
                        Automated data points extracted from system inventory,
                        classifications, and policies.
                      </Text>
                      <Space
                        direction="vertical"
                        size="small"
                        style={{ width: "100%" }}
                      >
                        {systemEvidence.map((item) => (
                          <div
                            key={item.id}
                            style={{
                              padding: "12px 16px",
                              backgroundColor: "#FFFFFF",
                              borderRadius: 8,
                              border: "1px solid #E8EBED",
                              transition: "all 0.15s ease",
                              cursor: "default",
                            }}
                            onMouseEnter={(e) => {
                              const target = e.currentTarget;
                              target.style.borderColor = "#D1D9E6";
                              target.style.boxShadow =
                                "0 1px 3px rgba(0, 0, 0, 0.04)";
                            }}
                            onMouseLeave={(e) => {
                              const target = e.currentTarget;
                              target.style.borderColor = "#E8EBED";
                              target.style.boxShadow = "none";
                            }}
                          >
                            <Flex
                              justify="space-between"
                              align="flex-start"
                              style={{ marginBottom: 8 }}
                            >
                              <Text
                                strong
                                style={{
                                  fontSize: 13,
                                  color: "#1A1F36",
                                }}
                              >
                                {item.source.system}
                              </Text>
                              {item.citationNumber && (
                                <span
                                  style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    minWidth: 22,
                                    height: 22,
                                    padding: "0 6px",
                                    fontSize: 11,
                                    fontWeight: 600,
                                    color: "#4A6CF7",
                                    backgroundColor: "#F0F4FF",
                                    border: "1px solid #D6E4FF",
                                    borderRadius: 11,
                                  }}
                                >
                                  {item.citationNumber}
                                </span>
                              )}
                            </Flex>
                            <Text
                              style={{
                                fontSize: 13,
                                color: "#4B5563",
                                display: "block",
                                lineHeight: 1.5,
                                marginBottom: 8,
                              }}
                            >
                              {item.label && (
                                <Text style={{ color: "#6B7280", marginRight: 4 }}>
                                  {item.label}:
                                </Text>
                              )}
                              {item.content}
                            </Text>
                            <Text
                              type="secondary"
                              style={{ fontSize: 12, display: "block" }}
                            >
                              Last updated: {formatTimestamp(item.timestamp)}
                            </Text>
                          </div>
                        ))}
                      </Space>
                    </div>
                  )}

                  {/* Human Input Section */}
                  {humanEvidence.length > 0 && (
                    <div>
                      <Flex
                        align="center"
                        justify="space-between"
                        style={{ marginBottom: 12 }}
                      >
                        <Text
                          strong
                          style={{
                            fontSize: 14,
                            fontWeight: 600,
                            color: "#1A1F36",
                          }}
                        >
                          Human input
                        </Text>
                      </Flex>
                      <Text
                        type="secondary"
                        style={{
                          fontSize: 13,
                          display: "block",
                          marginBottom: 16,
                          color: "#6B7280",
                          lineHeight: 1.6,
                        }}
                      >
                        Manual entries and stakeholder communications that inform
                        this assessment.
                      </Text>
                      <Space
                        direction="vertical"
                        size="small"
                        style={{ width: "100%" }}
                      >
                        {humanEvidence.map((item) => {
                          if (item.subtype === "stakeholder-communication") {
                            return (
                              <div
                                key={item.id}
                                style={{
                                  padding: "8px 16px 12px 16px",
                                  backgroundColor: "#FFFFFF",
                                  borderRadius: 8,
                                  border: "1px solid #E8EBED",
                                  transition: "all 0.15s ease",
                                  cursor: "default",
                                }}
                                onMouseEnter={(e) => {
                                  const target = e.currentTarget;
                                  target.style.borderColor = "#D1D9E6";
                                  target.style.boxShadow =
                                    "0 1px 3px rgba(0, 0, 0, 0.04)";
                                }}
                                onMouseLeave={(e) => {
                                  const target = e.currentTarget;
                                  target.style.borderColor = "#E8EBED";
                                  target.style.boxShadow = "none";
                                }}
                              >
                                <Flex
                                  justify="space-between"
                                  align="flex-start"
                                  style={{ marginBottom: 8 }}
                                >
                                  <Text
                                    strong
                                    style={{
                                      fontSize: 13,
                                      color: "#1A1F36",
                                    }}
                                  >
                                    Stakeholder communication
                                  </Text>
                                  {item.citationNumber && (
                                    <span
                                      style={{
                                        display: "inline-flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        minWidth: 22,
                                        height: 22,
                                        padding: "0 6px",
                                        fontSize: 11,
                                        fontWeight: 600,
                                        color: "#4A6CF7",
                                        backgroundColor: "#F0F4FF",
                                        border: "1px solid #D6E4FF",
                                        borderRadius: 11,
                                      }}
                                    >
                                      {item.citationNumber}
                                    </span>
                                  )}
                                </Flex>
                                <Text
                                  style={{
                                    fontSize: 13,
                                    color: "#4B5563",
                                    display: "block",
                                    lineHeight: 1.5,
                                    marginBottom: 8,
                                  }}
                                >
                                  {item.content}
                                </Text>
                                <Text
                                  type="secondary"
                                  style={{
                                    fontSize: 12,
                                    display: "block",
                                    marginBottom: 4,
                                  }}
                                >
                                  {item.channel} •{" "}
                                  {item.threadMessages?.length ?? 0} messages •{" "}
                                  {formatTimestamp(item.timestamp)}
                                </Text>
                                {item.threadMessages &&
                                  item.threadMessages.length > 0 && (
                                    <Collapse
                                      ghost
                                      style={{ marginTop: 8 }}
                                      items={[
                                        {
                                          key: "thread",
                                          label: `View ${item.threadMessages.length} message${item.threadMessages.length === 1 ? "" : "s"}`,
                                          children: (
                                            <List
                                              size="small"
                                              style={{ marginTop: -8 }}
                                              dataSource={item.threadMessages}
                                              renderItem={(msg, index) => (
                                                <List.Item
                                                  style={{
                                                    padding: "8px 0",
                                                    borderBottom:
                                                      index ===
                                                      (item.threadMessages?.length ?? 0) - 1
                                                        ? "none"
                                                        : `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
                                                  }}
                                                >
                                                  <List.Item.Meta
                                                    title={
                                                      <Flex
                                                        align="center"
                                                        gap="small"
                                                      >
                                                        <Text
                                                          strong
                                                          style={{ fontSize: 12 }}
                                                        >
                                                          {msg.sender}
                                                        </Text>
                                                        <Text
                                                          type="secondary"
                                                          style={{ fontSize: 11 }}
                                                        >
                                                          {new Date(
                                                            msg.timestamp,
                                                          ).toLocaleString("en-US", {
                                                            month: "short",
                                                            day: "numeric",
                                                            hour: "2-digit",
                                                            minute: "2-digit",
                                                          })}
                                                        </Text>
                                                      </Flex>
                                                    }
                                                    description={
                                                      <Text
                                                        style={{
                                                          fontSize: 13,
                                                          marginTop: 4,
                                                        }}
                                                      >
                                                        {msg.message}
                                                      </Text>
                                                    }
                                                  />
                                                </List.Item>
                                              )}
                                            />
                                          ),
                                        },
                                      ]}
                                    />
                                  )}
                              </div>
                            );
                          }

                          // Manual entry
                          return (
                            <div
                              key={item.id}
                              style={{
                                padding: "12px 16px",
                                backgroundColor: "#FFFFFF",
                                borderRadius: 8,
                                border: "1px solid #E8EBED",
                                transition: "all 0.15s ease",
                                cursor: "default",
                              }}
                              onMouseEnter={(e) => {
                                const target = e.currentTarget;
                                target.style.borderColor = "#D1D9E6";
                                target.style.boxShadow =
                                  "0 1px 3px rgba(0, 0, 0, 0.04)";
                              }}
                              onMouseLeave={(e) => {
                                const target = e.currentTarget;
                                target.style.borderColor = "#E8EBED";
                                target.style.boxShadow = "none";
                              }}
                            >
                              <Flex
                                justify="space-between"
                                align="flex-start"
                                style={{ marginBottom: 8 }}
                              >
                                <Text
                                  strong
                                  style={{
                                    fontSize: 13,
                                    color: "#1A1F36",
                                  }}
                                >
                                  Manual entry
                                </Text>
                                {item.citationNumber && (
                                  <span
                                    style={{
                                      display: "inline-flex",
                                      alignItems: "center",
                                      justifyContent: "center",
                                      minWidth: 22,
                                      height: 22,
                                      padding: "0 6px",
                                      fontSize: 11,
                                      fontWeight: 600,
                                      color: "#4A6CF7",
                                      backgroundColor: "#F0F4FF",
                                      border: "1px solid #D6E4FF",
                                      borderRadius: 11,
                                    }}
                                  >
                                    {item.citationNumber}
                                  </span>
                                )}
                              </Flex>
                              <Text
                                style={{
                                  fontSize: 13,
                                  color: "#4B5563",
                                  display: "block",
                                  lineHeight: 1.5,
                                  marginBottom: 8,
                                }}
                              >
                                {item.content}
                              </Text>
                              <Text
                                type="secondary"
                                style={{ fontSize: 12, display: "block" }}
                              >
                                {item.source.person.name},{" "}
                                {item.source.person.role} •{" "}
                                {formatTimestamp(item.timestamp)}
                              </Text>
                            </div>
                          );
                        })}
                      </Space>
                    </div>
                  )}

                  {/* No evidence message */}
                  {groupEvidence.length === 0 && (
                    <Text type="secondary" style={{ fontSize: 13 }}>
                      No evidence collected yet for this section.
                    </Text>
                  )}
                </div>
              );
            })}
          </Space>
        </div>
      </Drawer>
    </Layout>
  );
};

export default PrivacyAssessmentDetailPage;
