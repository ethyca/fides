import {
  CheckCircleOutlined,
  CloseOutlined,
  DownloadOutlined,
  DownOutlined,
  EditOutlined,
  FilePdfOutlined,
  GlobalOutlined,
  RightOutlined,
  SafetyOutlined,
  SearchOutlined,
  SlackOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import {
  Avatar,
  Badge,
  Button,
  Card,
  CheckOutlined,
  Collapse,
  CUSTOM_TAG_COLOR,
  Descriptions,
  Divider,
  Drawer,
  Flex,
  Form,
  Icons,
  Input,
  List,
  LocationSelect,
  Modal,
  Result,
  Space,
  Steps,
  Tag,
  Tooltip,
  Typography,
} from "fidesui";
import {
  formatIsoLocation,
  isoStringToEntry,
} from "fidesui/src/components/data-display/location.utils";
// TODO: fix this export to be better encapsulated in fidesui
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import Head from "next/head";
import { useRouter } from "next/router";
import React, { useEffect, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import SearchInput from "~/features/common/SearchInput";

import { EditableTextBlock } from "./components/EditableTextBlock";

const { Title, Text } = Typography;
const { Panel } = Collapse;

interface EvidenceItem {
  id: string;
  questionId: string; // Which question/section this evidence relates to
  type: "system" | "human" | "analysis";
  subtype: string;
  content: string;
  source: {
    system?: string;
    person?: { name: string; role: string };
    model?: string;
  };
  timestamp: string;
  confidence?: number;
  references?: string[];
  metadata?: Record<string, unknown>;
  links?: { label: string; url: string }[];
}

interface SystemEvidenceItem extends EvidenceItem {
  type: "system";
  subtype:
    | "data-classification"
    | "system-inventory"
    | "policy-document"
    | "compliance-monitor";
  source: {
    system: string;
  };
  confidence?: number;
}

interface HumanEvidenceItem extends EvidenceItem {
  type: "human";
  subtype: "manual-entry" | "stakeholder-communication";
  source: {
    person: { name: string; role: string };
  };
  status?: "verified" | "pending-review" | "draft";
  threadMessages?: Array<{
    sender: string;
    timestamp: string;
    message: string;
  }>;
  channel?: string;
  participants?: string[];
}

interface AnalysisEvidenceItem extends EvidenceItem {
  type: "analysis";
  subtype: "summary" | "inference" | "risk-assessment" | "compliance-check";
  source: {
    model: string;
  };
  confidence: number;
  references: string[];
}

/**
 * Generates a lawyer-perspective summary of assessment section answers.
 * This is a mock implementation that can be replaced with a real API call.
 */
const generateSectionSummary = async (
  sectionKey: string,
  sectionTitle: string,
  formValues: Record<string, unknown>,
): Promise<string> => {
  // Mock delay to simulate API call
  await new Promise<void>((resolve) => {
    setTimeout(resolve, 500);
  });

  // Extract answers from form values
  const answers = Object.entries(formValues)
    .filter(
      ([, value]) =>
        value && typeof value === "string" && value.trim().length > 0,
    )
    .map(([, value]) => value as string)
    .join(" ");

  // Mock summaries based on section - in production, this would call an LLM API
  const mockSummaries: Record<string, string> = {
    "1": "DPIA required due to systematic automated processing using AI/ML for personalized recommendations at scale, triggering GDPR Article 35.",
    "2": "ML analysis of purchase history and browsing behavior for recommendations. Data ingested via API, processed in isolated environment. Scope: PII and behavioral data for opted-in customers.",
    "3": "Consultation with DPO, InfoSec, Legal/Compliance teams. Customer feedback via opt-in surveys. Processor consultation for compliance measures.",
    "4": "Legitimate interests basis (Art. 6(1)(f)). Data minimization via selective fields and 24-month retention. Self-service portal for data subject rights. SCCs for international transfers.",
    "5": "Medium-level risks from automated decision-making and large-scale processing. Assessment evaluates likelihood and severity of harm.",
    "6": "Measures pending risk assessment completion. Additional measures will be proposed to eliminate or reduce medium/high-risk items.",
    "7": "Final approval required from stakeholders including DPO advice, residual risk acceptance, and ongoing compliance review.",
  };

  return (
    mockSummaries[sectionKey] ??
    `Summary for ${sectionTitle}: ${answers.substring(0, 200)}...`
  );
};

const PrivacyAssessmentDetailPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();

  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRegionModalOpen, setIsRegionModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [form] = Form.useForm();
  const [evidenceSearchQuery, setEvidenceSearchQuery] = useState("");
  const [evidenceExpandedSections, setEvidenceExpandedSections] = useState<
    string[]
  >([]);
  const [focusedQuestionId, setFocusedQuestionId] = useState<string | null>(
    null,
  );
  // Track expanded items per section (for "Show X more" functionality)
  const [expandedSystemItems, setExpandedSystemItems] = useState<
    Record<string, boolean>
  >({});
  const [expandedHumanItems, setExpandedHumanItems] = useState<
    Record<string, boolean>
  >({});
  // Track collapsed/expanded state for section cards
  const [collapsedSystemSections, setCollapsedSystemSections] = useState<
    Record<string, boolean>
  >({});
  const [collapsedHumanSections, setCollapsedHumanSections] = useState<
    Record<string, boolean>
  >({});
  const [questionsModalOpen, setQuestionsModalOpen] = useState(false);
  const [selectedSectionKey, setSelectedSectionKey] = useState<string | null>(
    null,
  );

  // Inline editing state for controller details
  const [isEditingControllerDetails, setIsEditingControllerDetails] =
    useState(false);
  const [editControllerDetails, setEditControllerDetails] = useState({
    nameOfController: "",
    subjectTitleOfDPO: "",
    nameOfControllerContactDPO: "",
  });

  // Controller details state
  const [controllerDetails, setControllerDetails] = useState({
    nameOfController: "Example Corporation",
    subjectTitleOfDPO:
      "Data Protection Impact Assessment - Customer Insight AI Module",
    nameOfControllerContactDPO: "Jane Doe, DPO",
  });

  // Document content state (replaces form values for editable text blocks)
  const [documentContent, setDocumentContent] = useState<
    Record<string, string>
  >({
    // Section 1
    dpiaNeed:
      "A DPIA is required because this project involves systematic and extensive evaluation of personal aspects relating to natural persons based on automated processing, including profiling [1]. The processing uses new technologies (AI/ML algorithms) [2] and involves processing of personal data on a large scale, including special category data. The automated decision-making aspects and the scale of data processing present potential high risks to individuals' rights and freedoms.",
    // Section 2
    framework: "GDPR-DPIA",
    nature:
      "The system uses machine learning algorithms to analyze customer purchase history and browsing behavior to generate personalized product recommendations. Data is ingested via API from the core commerce engine and processed in a secure isolated environment.",
    scope:
      "Names, email addresses, IP addresses, purchase history, and clickstream data.",
    context:
      "Data subjects are existing customers who have opted-in to marketing communications. The relationship is direct B2C. There are no known vulnerable groups in the standard customer base.",
    purposes: "",
    // Section 3
    stakeholderConsultation:
      "We will consult with the Data Protection Officer (DPO) and the Information Security team before implementation. Customer feedback will be gathered through opt-in surveys during the initial rollout phase. We will also consult with our data processors (cloud infrastructure provider) to ensure compliance measures are in place. The Legal and Compliance teams will review the processing activities and provide guidance on lawful basis and data subject rights.",
    // Section 4
    complianceMeasures:
      "Lawful basis: Legitimate interests (Article 6(1)(f)) for personalized recommendations to enhance customer experience [1]. The processing achieves the purpose of providing relevant product suggestions, and there is no less intrusive alternative that would achieve the same outcome. Function creep is prevented through strict access controls and regular audits. Data quality is ensured through validation at ingestion points and automated data cleansing processes. Data minimisation is achieved by only processing necessary data fields (purchase history, browsing behavior) [2] and implementing data retention policies (24 months) [3]. Individuals are informed through privacy notices and cookie banners. Data subject rights are supported through a self-service portal for access, rectification, erasure, and objection requests. Processors are contractually bound through Data Processing Agreements (DPAs) with specific security and compliance requirements. International transfers are safeguarded through Standard Contractual Clauses (SCCs) and adequacy decisions where applicable.",
    // Section 5
    risks: "",
    // Section 6
    measures: "",
    // Section 7
    measuresApprovedBy: "",
    residualRisksApprovedBy: "",
    dpoAdviceProvided: "",
    dpoAdviceSummary: "",
    dpoAdviceAccepted: "",
    consultationReviewedBy: "",
    dpiaReviewBy: "",
  });

  // Format region code to display name
  const formatRegionDisplay = (regionCode: string): string => {
    const entry = isoStringToEntry(regionCode);
    if (entry) {
      return formatIsoLocation({ isoEntry: entry, showFlag: true });
    }
    return regionCode;
  };

  // Mock evidence data grouped by question
  // In a real implementation, this would come from an API and be organized by question
  const allEvidence: EvidenceItem[] = [
    // Question 2: Describe the processing
    {
      id: "sys-1",
      questionId: "2",
      type: "system",
      subtype: "data-classification",
      content: "PII, Behavioral Data",
      source: { system: "Fides Data Map" },
      timestamp: "2024-01-15T14:23:00Z",
      confidence: 98,
      links: [{ label: "View in Data Map", url: "#" }],
    },
    {
      id: "sys-2",
      questionId: "2",
      type: "system",
      subtype: "system-inventory",
      content: "Customer Insight AI Module",
      source: { system: "System Inventory" },
      timestamp: "2024-01-15T14:20:00Z",
      links: [{ label: "View system details", url: "#" }],
    },
    {
      id: "sys-3",
      questionId: "2",
      type: "system",
      subtype: "policy-document",
      content: "Retention: 24 months (Section 4.2)",
      source: { system: "Data Retention Policy v3.1" },
      timestamp: "2024-01-15T13:45:00Z",
      links: [{ label: "View policy document", url: "#" }],
    },
    {
      id: "human-1",
      questionId: "2",
      type: "human",
      subtype: "manual-entry",
      content:
        "Processing involves ML analysis of customer purchase history and browsing behavior for personalized recommendations.",
      source: { person: { name: "Jack Gale", role: "Privacy Officer" } },
      timestamp: "2024-01-15T14:20:00Z",
      status: "verified",
    },
    {
      id: "human-2",
      questionId: "2",
      type: "human",
      subtype: "stakeholder-communication",
      content: "Data flow discussion with team",
      source: { person: { name: "Jack Gale", role: "Privacy Officer" } },
      timestamp: "2024-01-15T14:15:00Z",
      channel: "Slack #privacy-assessments",
      participants: ["Jack Gale", "Sarah Johnson", "Data Steward Team"],
      threadMessages: [
        {
          sender: "Jack Gale",
          timestamp: "2024-01-15T14:15:00Z",
          message:
            "Thanks! Can you help me understand the data flow? How is the data ingested?",
        },
        {
          sender: "Sarah Johnson",
          timestamp: "2024-01-15T14:18:00Z",
          message:
            "Based on the system architecture, data is ingested via API from the core commerce engine. It's processed in a secure isolated environment.",
        },
        {
          sender: "Jack Gale",
          timestamp: "2024-01-15T14:22:00Z",
          message:
            "What about the retention period? Do we have that information?",
        },
        {
          sender: "Sarah Johnson",
          timestamp: "2024-01-15T14:23:00Z",
          message:
            "The retention period is 24 months based on the legitimate interest lawful basis.",
        },
      ],
    },
    {
      id: "analysis-1",
      questionId: "2",
      type: "analysis",
      subtype: "summary",
      content:
        "Processing involves ML analysis of customer purchase history and browsing behavior for personalized recommendations. Data from commerce engine, processed in isolated environment. Scope: PII and behavioral data for opted-in customers.",
      source: { model: "GPT-4-turbo (v2024.01)" },
      timestamp: "2024-01-15T15:30:00Z",
      confidence: 87,
      references: ["sys-1", "sys-2", "human-1", "human-2"],
    },
  ];

  // Group evidence by question - merge analysis into system
  const evidenceByQuestion = useMemo(() => {
    const grouped: Record<
      string,
      {
        system: (SystemEvidenceItem | AnalysisEvidenceItem)[];
        human: HumanEvidenceItem[];
      }
    > = {};

    allEvidence.forEach((item) => {
      if (!grouped[item.questionId]) {
        grouped[item.questionId] = { system: [], human: [] };
      }

      if (item.type === "system") {
        grouped[item.questionId].system.push(item as SystemEvidenceItem);
      } else if (item.type === "human") {
        grouped[item.questionId].human.push(item as HumanEvidenceItem);
      } else if (item.type === "analysis") {
        // Merge analysis items into system-derived data
        grouped[item.questionId].system.push(item as AnalysisEvidenceItem);
      }
    });

    return grouped;
  }, [allEvidence]);

  // Get question titles
  const getQuestionTitle = (questionId: string): string => {
    const questionMap: Record<string, string> = {
      "1": "Identify the need for a DPIA",
      "2": "Describe the processing",
      "3": "Consultation process",
      "4": "Assess necessity and proportionality",
      "5": "Identify and assess risks",
      "6": "Identify measures to reduce risk",
      "7": "Sign off and record outcomes",
    };
    return questionMap[questionId] ?? `Question ${questionId}`;
  };

  // Helper function to render text with source links
  const renderTextWithSourceLinks = (text: string, questionId: string) => {
    const sourcePattern = /\[(\d+)\]/g;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match = sourcePattern.exec(text);
    let sourceIndex = 0;

    while (match !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      const sourceNum = match[1];
      const currentSourceIndex = sourceIndex;
      sourceIndex += 1;
      parts.push(
        <Button
          key={`source-${currentSourceIndex}`}
          type="text"
          style={{
            padding: "2px 8px",
            height: "auto",
            minHeight: "auto",
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
            setFocusedQuestionId(questionId);
            setIsDrawerOpen(true);
            if (!evidenceExpandedSections.includes(questionId)) {
              setEvidenceExpandedSections([
                ...evidenceExpandedSections,
                questionId,
              ]);
            }
          }}
        >
          {sourceNum}
        </Button>,
      );
      lastIndex = match.index + match[0].length;
      match = sourcePattern.exec(text);
    }
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }
    // eslint-disable-next-line react/jsx-no-useless-fragment
    return <>{parts}</>;
  };

  const handleExpandAll = () => {
    setExpandedKeys(["1", "2", "3", "4", "5", "6", "7"]);
  };

  const handleCollapseAll = () => {
    setExpandedKeys([]);
  };

  const handleConfirmDelete = () => {
    // In a real implementation, this would call an API to delete the assessment
    // For now, we just navigate back to the assessments list
    setIsDeleteModalOpen(false);
    router.push(PRIVACY_ASSESSMENTS_ROUTE);
  };

  // Questions for each section based on GDPR DPIA template
  const sectionQuestions: Record<string, string[]> = {
    "1": ["Why is a DPIA needed for this processing?"],
    "2": [
      "What assessment framework are you using?",
      "What is the nature of the processing? How will you collect, use, store and delete data? What is the source of the data? Will you be sharing data with anyone? What types of processing identified as likely high risk are involved?",
      "What is the scope of the processing? What is the nature of the data, and does it include special category or criminal offence data? How much data will you be collecting and using? How often? How long will you keep it? How many individuals are affected? What geographical area does it cover?",
      "What is the context of the processing? What is the nature of your relationship with the individuals? How much control will they have? Would they expect you to use their data in this way? Do they include children or other vulnerable groups? Are there prior concerns over this type of processing or security flaws?",
      "What are the purposes of the processing? What do you want to achieve? What is the intended effect on individuals? What are the benefits of the processing – for you, and more broadly?",
    ],
    "3": [
      "How will you consult with relevant stakeholders? When and how will you seek individuals' views – or justify why it's not appropriate to do so? Who else do you need to involve within your organisation? Do you need to ask your processors to assist? Do you plan to consult information security experts, or any other experts?",
    ],
    "4": [
      "What is your lawful basis for processing? Does the processing actually achieve your purpose? Is there another way to achieve the same outcome? How will you prevent function creep? How will you ensure data quality and data minimisation? What information will you give individuals? How will you help to support their rights? What measures do you take to ensure processors comply? How do you safeguard any international transfers?",
    ],
    "5": [
      "What is the source of risk? What is the nature of potential impact on individuals? What are the associated compliance and corporate risks? For each risk, what is the likelihood of harm (Remote, possible or probable)? For each risk, what is the severity of harm (Minimal, significant or severe)? What is the overall risk level (Low, medium or high) for each identified risk?",
    ],
    "6": [
      "What additional measures could you take to reduce or eliminate risks identified as medium or high risk? For each risk, what are the options to reduce or eliminate risk? What is the effect on risk (Eliminated, reduced, accepted) for each measure? What is the residual risk (Low, medium, high) after implementing measures? Is the measure approved (Yes/no)?",
    ],
    "7": [
      "Who approved the measures? (Name/date)",
      "Who approved the residual risks? (Name/date) - If accepting any residual high risk, consult the ICO before going ahead",
      "Was DPO advice provided? (Name/date) - DPO should advise on compliance, step 6 measures and whether processing can proceed",
      "What is the summary of DPO advice?",
      "Was DPO advice accepted or overruled? (Name/date) - If overruled, you must explain your reasons",
      "Who reviewed consultation responses? (Name/date) - If your decision departs from individuals' views, you must explain your reasons",
      "Who will keep this DPIA under review? (Name/date) - The DPO should also review ongoing compliance with DPIA",
    ],
  };

  const handleOpenQuestions = (sectionKey: string) => {
    setSelectedSectionKey(sectionKey);
    setQuestionsModalOpen(true);
  };

  const handleOpenEvidence = (sectionKey: string) => {
    setFocusedQuestionId(sectionKey);
    if (!evidenceExpandedSections.includes(sectionKey)) {
      setEvidenceExpandedSections([
        ...evidenceExpandedSections,
        sectionKey,
      ]);
    }
    setIsDrawerOpen(true);
  };

  // Helper to render section title with info icon
  const renderSectionTitle = (
    sectionKey: string,
    title: string,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _isExpanded: boolean,
  ) => {
    const sectionNumber = sectionKey;
    return (
      <Flex align="center" gap="small" style={{ flexShrink: 0 }}>
        <Text strong style={{ fontSize: 16, whiteSpace: "nowrap" }}>
          {sectionNumber}. {title}
        </Text>
        <Tooltip title="View questions for this section">
          <Button
            type="text"
            size="small"
            icon={<Icons.Information size={16} />}
            aria-label="View questions for this section"
            onClick={(e) => {
              e.stopPropagation();
              handleOpenQuestions(sectionKey);
            }}
            style={{
              padding: "2px 4px",
              height: "auto",
              minHeight: "auto",
              color: palette.FIDESUI_NEUTRAL_500,
              transition: "color 0.2s ease",
              flexShrink: 0,
            }}
            onMouseEnter={(e) => {
              const target = e.currentTarget;
              target.style.color = palette.FIDESUI_MINOS;
            }}
            onMouseLeave={(e) => {
              const target = e.currentTarget;
              target.style.color = palette.FIDESUI_NEUTRAL_500;
            }}
          />
        </Tooltip>
      </Flex>
    );
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    });
  };

  // Filter evidence based on search query
  const filteredEvidenceByQuestion = useMemo(() => {
    if (!evidenceSearchQuery) {
      return evidenceByQuestion;
    }

    const query = evidenceSearchQuery.toLowerCase();
    const filtered: typeof evidenceByQuestion = {};

    Object.entries(evidenceByQuestion).forEach(([questionId, evidence]) => {
      const filteredSystem = evidence.system.filter(
        (item) =>
          item.content.toLowerCase().includes(query) ||
          (item.type === "system" &&
            item.source.system?.toLowerCase().includes(query)) ||
          (item.type === "analysis" &&
            item.source.model?.toLowerCase().includes(query)) ||
          item.subtype.toLowerCase().includes(query),
      );

      const filteredHuman = evidence.human.filter(
        (item) =>
          item.content.toLowerCase().includes(query) ||
          item.source.person.name.toLowerCase().includes(query) ||
          item.source.person.role.toLowerCase().includes(query) ||
          (item.channel && item.channel.toLowerCase().includes(query)) ||
          (item.participants &&
            item.participants.some((p) => p.toLowerCase().includes(query))),
      );

      // Only include question if it has filtered results
      if (filteredSystem.length > 0 || filteredHuman.length > 0) {
        filtered[questionId] = {
          system: filteredSystem,
          human: filteredHuman,
        };
      }
    });

    return filtered;
  }, [evidenceSearchQuery, evidenceByQuestion]);

  const sections = [
    { key: "1", title: "Identify the need for a DPIA", fields: ["dpiaNeed"] },
    {
      key: "2",
      title: "Describe the processing",
      fields: ["framework", "nature", "scope", "context", "purposes"],
    },
    {
      key: "3",
      title: "Consultation process",
      fields: ["stakeholderConsultation"],
    },
    {
      key: "4",
      title: "Assess necessity and proportionality",
      fields: ["complianceMeasures"],
    },
    { key: "5", title: "Identify and assess risks", fields: ["risks"] },
    {
      key: "6",
      title: "Identify measures to reduce risk",
      fields: ["measures"],
    },
    {
      key: "7",
      title: "Sign off and record outcomes",
      fields: [
        "measuresApprovedBy",
        "residualRisksApprovedBy",
        "dpoAdviceProvided",
        "dpoAdviceSummary",
        "dpoAdviceAccepted",
        "consultationReviewedBy",
        "dpiaReviewBy",
      ],
    },
  ];

  // Generate summary for a specific section
  const generateSummaryForSection = async (
    sectionKey: string,
    allValues: Record<string, unknown>,
  ) => {
    const section = sections.find((s) => s.key === sectionKey);
    if (!section) {
      return;
    }

    const sectionValues: Record<string, unknown> = {};
    section.fields.forEach((field) => {
      if (allValues[field]) {
        sectionValues[field] = allValues[field];
      }
    });

    // Only generate if we have values
    if (Object.keys(sectionValues).length > 0) {
      // Summary generation would happen here via API call
      await generateSectionSummary(sectionKey, section.title, sectionValues);
    }
  };

  // Generate summaries for sections when form values change
  const handleFormValuesChange = async (
    changedValues: Record<string, unknown>,
    allValues: Record<string, unknown>,
  ) => {
    // Find which section was changed
    const changedFields = Object.keys(changedValues);
    const affectedSection = sections.find((section) =>
      section.fields.some((field) => changedFields.includes(field)),
    );

    if (affectedSection) {
      await generateSummaryForSection(affectedSection.key, allValues);
    }
  };

  // Initialize summaries from initial form values
  useEffect(() => {
    // Wait for form to be ready, then generate summaries for all sections with values
    const timer = setTimeout(() => {
      // Get all form values including initial values
      const formValues = form.getFieldsValue(true);

      // Generate summaries for all completed sections (1, 2, 4) that have initial values
      // Section 1: dpiaNeed
      const section1Values = {
        dpiaNeed:
          formValues.dpiaNeed ??
          "A DPIA is required because this project involves systematic and extensive evaluation of personal aspects relating to natural persons based on automated processing, including profiling. The processing uses new technologies (AI/ML algorithms) and involves processing of personal data on a large scale, including special category data. The automated decision-making aspects and the scale of data processing present potential high risks to individuals' rights and freedoms.",
      };
      if (section1Values.dpiaNeed) {
        generateSummaryForSection("1", section1Values);
      }

      // Section 2: framework, nature, scope, context, purposes
      const section2Values = {
        framework: formValues.framework ?? "GDPR-DPIA",
        nature:
          formValues.nature ??
          "The system uses machine learning algorithms to analyze customer purchase history and browsing behavior to generate personalized product recommendations. Data is ingested via API from the core commerce engine and processed in a secure isolated environment.",
        scope:
          formValues.scope ??
          "Names, email addresses, IP addresses, purchase history, and clickstream data.",
        context:
          formValues.context ??
          "Data subjects are existing customers who have opted-in to marketing communications. The relationship is direct B2C. There are no known vulnerable groups in the standard customer base.",
        purposes: formValues.purposes ?? "",
      };
      if (
        section2Values.framework ||
        section2Values.nature ||
        section2Values.scope ||
        section2Values.context
      ) {
        generateSummaryForSection("2", section2Values);
      }

      // Section 4: complianceMeasures
      const section4Values = {
        complianceMeasures:
          formValues.complianceMeasures ??
          "Lawful basis: Legitimate interests (Article 6(1)(f)) for personalized recommendations to enhance customer experience. The processing achieves the purpose of providing relevant product suggestions, and there is no less intrusive alternative that would achieve the same outcome. Function creep is prevented through strict access controls and regular audits. Data quality is ensured through validation at ingestion points and automated data cleansing processes. Data minimisation is achieved by only processing necessary data fields (purchase history, browsing behavior) and implementing data retention policies (24 months). Individuals are informed through privacy notices and cookie banners. Data subject rights are supported through a self-service portal for access, rectification, erasure, and objection requests. Processors are contractually bound through Data Processing Agreements (DPAs) with specific security and compliance requirements. International transfers are safeguarded through Standard Contractual Clauses (SCCs) and adequacy decisions where applicable.",
      };
      if (section4Values.complianceMeasures) {
        generateSummaryForSection("4", section4Values);
      }
    }, 300);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Check feature flag after all hooks
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

  // IDs of completed assessments (from mock data)
  const completedAssessmentIds = ["3", "6", "9"];
  const assessmentId = router.query.id as string;
  const isCompletedAssessment = completedAssessmentIds.includes(assessmentId);

  const steps = isCompletedAssessment
    ? [
        { title: "Need", status: "finish" },
        { title: "Processing", status: "finish" },
        { title: "Consultation", status: "finish" },
        { title: "Necessity", status: "finish" },
        { title: "Risks", status: "finish" },
        { title: "Measures", status: "finish" },
        { title: "Sign off", status: "finish" },
      ]
    : [
        { title: "Need", status: "finish" },
        { title: "Processing", status: "finish" },
        { title: "Consultation", status: "wait" },
        { title: "Necessity", status: "finish" },
        { title: "Risks", status: "process" },
        { title: "Measures", status: "wait" },
        { title: "Sign off", status: "wait" },
      ];

  return (
    <Layout title="Privacy assessments">
      <Head>
        <style>{`
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
            transition: min-height 1.2s cubic-bezier(0.4, 0, 0.2, 1);
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
            transition: transform 1.2s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1;
          }
          .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-arrow {
            transform: rotate(90deg);
          }
          .privacy-assessment-collapse .ant-collapse-arrow svg {
            margin: 0;
            transition: transform 1.2s cubic-bezier(0.4, 0, 0.2, 1);
          }
          .privacy-assessment-collapse .ant-collapse-header-text {
            margin-left: 40px;
            margin-right: 0;
            width: calc(100% - 40px);
            transition: opacity 0.6s ease;
            overflow: hidden;
          }
          .privacy-assessment-collapse .ant-collapse-header-text > div {
            max-width: 100%;
            overflow: hidden;
          }
          .privacy-assessment-collapse .ant-collapse-content {
            transition: height 1.2s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.8s ease;
            overflow: hidden;
          }
          .privacy-assessment-collapse .ant-collapse-content-box {
            padding-top: 0;
            transition: padding 1.2s cubic-bezier(0.4, 0, 0.2, 1);
          }
          .privacy-assessment-collapse .ant-collapse-header-text .ant-tag {
            position: static !important;
            display: inline;
            margin-left: 4px;
          }
          .privacy-assessment-collapse .status-tag-container {
            position: absolute;
            right: 24px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 2;
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: flex-end;
            gap: 24px;
            max-width: min(800px, calc(100% - 250px));
            min-width: 300px;
            padding-right: 12px;
          }
          .privacy-assessment-collapse .status-tag-container .summary-text {
            font-size: 12px;
            color: ${palette.FIDESUI_NEUTRAL_600};
            line-height: 1.5;
            text-align: left;
            max-width: 550px;
            min-width: 0;
            word-wrap: break-word;
            word-break: break-word;
            white-space: normal;
            overflow-wrap: anywhere;
            hyphens: auto;
            margin-right: auto;
          }
          .privacy-assessment-collapse .status-tag-container .risk-confidence-container {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
            flex-shrink: 0;
            padding-right: 12px;
          }
          .privacy-assessment-collapse .status-tag-container .ant-tag {
            flex-shrink: 0;
            margin: 0;
            margin-left: 0;
          }
          .privacy-assessment-collapse .ant-collapse-header {
            padding-right: min(850px, calc(100% - 200px)) !important;
          }
          .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-header {
            padding-right: min(850px, calc(100% - 200px)) !important;
          }
          @media (max-width: 1400px) {
            .privacy-assessment-collapse .status-tag-container {
              max-width: min(700px, calc(100% - 300px));
            }
            .privacy-assessment-collapse .status-tag-container .summary-text {
              max-width: 450px;
            }
            .privacy-assessment-collapse .ant-collapse-header {
              padding-right: min(750px, calc(100% - 200px)) !important;
            }
            .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-header {
              padding-right: min(750px, calc(100% - 200px)) !important;
            }
          }
          @media (max-width: 1200px) {
            .privacy-assessment-collapse .status-tag-container {
              max-width: min(600px, calc(100% - 250px));
            }
            .privacy-assessment-collapse .status-tag-container .summary-text {
              max-width: 400px;
            }
            .privacy-assessment-collapse .ant-collapse-header {
              padding-right: min(650px, calc(100% - 200px)) !important;
            }
            .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-header {
              padding-right: min(650px, calc(100% - 200px)) !important;
            }
          }
          @media (max-width: 992px) {
            .privacy-assessment-collapse .status-tag-container {
              position: static;
              transform: none;
              top: auto;
              right: auto;
              max-width: 100%;
              min-width: 0;
              margin-top: 12px;
              padding-right: 0;
              flex-direction: column;
              align-items: flex-start;
              gap: 12px;
            }
            .privacy-assessment-collapse .status-tag-container .summary-text {
              max-width: 100%;
              margin-right: 0;
            }
            .privacy-assessment-collapse .status-tag-container .risk-confidence-container {
              flex-direction: row;
              align-items: center;
              gap: 12px;
              padding-right: 0;
            }
            .privacy-assessment-collapse .ant-collapse-header {
              padding-right: 24px !important;
              flex-direction: column;
              align-items: flex-start;
            }
            .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-header {
              padding-right: 24px !important;
            }
            .privacy-assessment-collapse .ant-collapse-header-text {
              width: 100%;
              margin-left: 40px;
            }
          }
          @media (max-width: 768px) {
            .privacy-assessment-collapse .status-tag-container {
              gap: 8px;
            }
            .privacy-assessment-collapse .status-tag-container .summary-text {
              font-size: 11px;
            }
            .privacy-assessment-collapse .status-tag-container .risk-confidence-container {
              flex-wrap: wrap;
            }
            .privacy-assessment-collapse .ant-collapse-header {
              padding: 12px 16px !important;
              padding-left: 18px !important;
              min-height: auto !important;
            }
            .privacy-assessment-collapse .ant-collapse-item-active .ant-collapse-header {
              min-height: auto !important;
            }
            .privacy-assessment-collapse .ant-collapse-arrow {
              top: 12px;
            }
            .privacy-assessment-collapse .ant-collapse-header-text {
              margin-left: 36px;
            }
            .privacy-assessment-collapse .ant-collapse-header-text > div {
              flex-direction: column;
              align-items: flex-start;
              gap: 8px;
            }
          }
          @media (max-width: 576px) {
            .privacy-assessment-collapse .status-tag-container .summary-text {
              display: none;
            }
            .privacy-assessment-collapse .status-tag-container {
              flex-direction: row;
              align-items: center;
              justify-content: space-between;
              width: 100%;
            }
            .privacy-assessment-collapse .status-tag-container .risk-confidence-container {
              flex-direction: row;
              gap: 8px;
            }
            .assessment-page-container {
              padding: 16px !important;
            }
          }
          @media (max-width: 480px) {
            .privacy-assessment-collapse .ant-collapse-header {
              padding: 10px 12px !important;
              padding-left: 16px !important;
            }
            .privacy-assessment-collapse .ant-collapse-arrow {
              left: 16px;
              top: 10px;
            }
            .privacy-assessment-collapse .ant-collapse-header-text {
              margin-left: 36px;
            }
            .assessment-page-container {
              padding: 12px !important;
            }
            .assessment-page-container .ant-steps {
              min-width: 500px !important;
            }
            .assessment-page-container .ant-input-search {
              min-width: 150px !important;
              max-width: 100% !important;
            }
          }
        `}</style>
      </Head>
      <PageHeader
        heading="Privacy assessments"
        breadcrumbItems={[
          { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
          {
            title: (
              <Flex
                align="center"
                gap="small"
                wrap="wrap"
                style={{ maxWidth: "100%" }}
              >
                <span style={{ flexShrink: 0 }}>
                  Customer Insight AI Module
                </span>
                <Tag
                  style={{
                    fontSize: 12,
                    margin: 0,
                    backgroundColor: palette.FIDESUI_NEUTRAL_300,
                    border: "none",
                    color: palette.FIDESUI_MINOS,
                    flexShrink: 0,
                  }}
                >
                  GDPR DPIA
                </Tag>
                {selectedRegions.length > 0 && (
                  <Flex
                    align="center"
                    gap="small"
                    wrap="wrap"
                    style={{ flexShrink: 0 }}
                  >
                    <GlobalOutlined
                      style={{
                        fontSize: 12,
                        color: palette.FIDESUI_NEUTRAL_500,
                      }}
                    />
                    <Flex gap="small" wrap="wrap">
                      {selectedRegions.slice(0, 2).map((region) => (
                        <Tag key={region} style={{ fontSize: 11, margin: 0 }}>
                          {formatRegionDisplay(region)}
                        </Tag>
                      ))}
                      {selectedRegions.length > 2 && (
                        <Tag style={{ fontSize: 11, margin: 0 }}>
                          +{selectedRegions.length - 2}
                        </Tag>
                      )}
                    </Flex>
                    <Button
                      type="link"
                      size="small"
                      onClick={() => setIsRegionModalOpen(true)}
                      style={{
                        padding: 0,
                        height: "auto",
                        fontSize: 11,
                        whiteSpace: "nowrap",
                      }}
                    >
                      Edit
                    </Button>
                  </Flex>
                )}
                {selectedRegions.length === 0 && (
                  <Button
                    type="link"
                    size="small"
                    icon={<GlobalOutlined />}
                    onClick={() => setIsRegionModalOpen(true)}
                    style={{
                      padding: 0,
                      height: "auto",
                      fontSize: 12,
                      whiteSpace: "nowrap",
                    }}
                  >
                    Configure regions
                  </Button>
                )}
              </Flex>
            ),
          },
        ]}
        rightContent={
          <Space wrap>
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
            <Button style={{ whiteSpace: "nowrap" }}>Save as draft</Button>
            <Button
              type="primary"
              onClick={() => setIsReportModalOpen(true)}
              style={{ whiteSpace: "nowrap" }}
            >
              Generate report
            </Button>
          </Space>
        }
      />
      <div
        style={{ padding: "24px 24px", maxWidth: "100%", overflowX: "hidden" }}
        className="assessment-page-container"
      >
        <Space
          direction="vertical"
          size="large"
          style={{ width: "100%", maxWidth: "100%" }}
        >
          <div style={{ overflowX: "auto", marginBottom: 32 }}>
            <Steps
              current={isCompletedAssessment ? 6 : 2}
              size="small"
              items={steps.map((step) => ({
                title: step.title,
                status: step.status as any,
              }))}
              style={{ minWidth: 600 }}
            />
          </div>

          <Flex
            justify="space-between"
            align="center"
            wrap="wrap"
            gap="small"
            style={{ marginTop: 16 }}
          >
            <SearchInput
              placeholder="Search risks, authors, or content"
              onChange={() => {}}
              style={{ flex: "1 1 300px", minWidth: 200, maxWidth: 400 }}
            />
            <Flex gap="small" wrap="wrap" style={{ flexShrink: 0 }}>
              <Button
                type="link"
                onClick={handleExpandAll}
                style={{ whiteSpace: "nowrap", fontSize: 13 }}
              >
                Expand all
              </Button>
              <Button
                type="link"
                onClick={handleCollapseAll}
                style={{ whiteSpace: "nowrap", fontSize: 13 }}
              >
                Collapse all
              </Button>
            </Flex>
          </Flex>

          {/* Controller Details Section - Compact Inline */}
          <div
            style={{
              marginBottom: 20,
              padding: "10px 14px",
              backgroundColor: palette.FIDESUI_BG_CORINTH,
              borderRadius: 6,
              border: `1px solid ${palette.FIDESUI_NEUTRAL_200}`,
              position: "relative",
            }}
          >
            <Flex
              gap="middle"
              wrap="wrap"
              align="center"
              justify="space-between"
              style={{ fontSize: 13, lineHeight: 1.5 }}
            >
              <Flex gap="middle" wrap="wrap" align="center" style={{ flex: 1 }}>
                <Flex align="center" gap="small">
                  <Text
                    type="secondary"
                    style={{
                      fontSize: 12,
                      color: palette.FIDESUI_NEUTRAL_600,
                      whiteSpace: "nowrap",
                    }}
                  >
                    Controller:
                  </Text>
                  {isEditingControllerDetails ? (
                    <Input
                      value={editControllerDetails.nameOfController}
                      onChange={(e) =>
                        setEditControllerDetails({
                          ...editControllerDetails,
                          nameOfController: e.target.value,
                        })
                      }
                      placeholder="Enter controller name"
                      style={{
                        fontSize: 13,
                        padding: "2px 6px",
                        height: "auto",
                        minHeight: "auto",
                        width: 200,
                      }}
                    />
                  ) : (
                    <Text
                      style={{
                        color: "#1A1F36",
                        minWidth: 200,
                        display: "inline-block",
                      }}
                    >
                      {controllerDetails.nameOfController ?? (
                        <span
                          style={{
                            fontStyle: "italic",
                            color: palette.FIDESUI_NEUTRAL_400,
                          }}
                        >
                          Enter controller name
                        </span>
                      )}
                    </Text>
                  )}
                </Flex>
                <Divider
                  type="vertical"
                  style={{ height: 14, margin: "0 4px" }}
                />
                <Flex align="center" gap="small">
                  <Text
                    type="secondary"
                    style={{
                      fontSize: 12,
                      color: palette.FIDESUI_NEUTRAL_600,
                      whiteSpace: "nowrap",
                    }}
                  >
                    DPO Title:
                  </Text>
                  {isEditingControllerDetails ? (
                    <Input
                      value={editControllerDetails.subjectTitleOfDPO}
                      onChange={(e) =>
                        setEditControllerDetails({
                          ...editControllerDetails,
                          subjectTitleOfDPO: e.target.value,
                        })
                      }
                      placeholder="Enter DPO subject/title"
                      style={{
                        fontSize: 13,
                        padding: "2px 6px",
                        height: "auto",
                        minHeight: "auto",
                        width: 300,
                      }}
                    />
                  ) : (
                    <Text
                      style={{
                        color: "#1A1F36",
                        minWidth: 300,
                        display: "inline-block",
                      }}
                    >
                      {controllerDetails.subjectTitleOfDPO ?? (
                        <span
                          style={{
                            fontStyle: "italic",
                            color: palette.FIDESUI_NEUTRAL_400,
                          }}
                        >
                          Enter DPO subject/title
                        </span>
                      )}
                    </Text>
                  )}
                </Flex>
                <Divider
                  type="vertical"
                  style={{ height: 14, margin: "0 4px" }}
                />
                <Flex align="center" gap="small">
                  <Text
                    type="secondary"
                    style={{
                      fontSize: 12,
                      color: palette.FIDESUI_NEUTRAL_600,
                      whiteSpace: "nowrap",
                    }}
                  >
                    Contact:
                  </Text>
                  {isEditingControllerDetails ? (
                    <Input
                      value={editControllerDetails.nameOfControllerContactDPO}
                      onChange={(e) =>
                        setEditControllerDetails({
                          ...editControllerDetails,
                          nameOfControllerContactDPO: e.target.value,
                        })
                      }
                      placeholder="Enter contact name"
                      style={{
                        fontSize: 13,
                        padding: "2px 6px",
                        height: "auto",
                        minHeight: "auto",
                        width: 200,
                      }}
                    />
                  ) : (
                    <Text
                      style={{
                        color: "#1A1F36",
                        minWidth: 200,
                        display: "inline-block",
                      }}
                    >
                      {controllerDetails.nameOfControllerContactDPO ?? (
                        <span
                          style={{
                            fontStyle: "italic",
                            color: palette.FIDESUI_NEUTRAL_400,
                          }}
                        >
                          Enter contact name
                        </span>
                      )}
                    </Text>
                  )}
                </Flex>
              </Flex>
              {isEditingControllerDetails ? (
                <Flex gap="small" align="center">
                  <Button
                    size="small"
                    onClick={() => {
                      setControllerDetails(editControllerDetails);
                      setIsEditingControllerDetails(false);
                    }}
                    icon={<CheckOutlined />}
                  >
                    Save
                  </Button>
                  <Button
                    size="small"
                    onClick={() => {
                      setEditControllerDetails(controllerDetails);
                      setIsEditingControllerDetails(false);
                    }}
                    icon={<CloseOutlined />}
                  >
                    Cancel
                  </Button>
                </Flex>
              ) : (
                <Button
                  type="text"
                  size="small"
                  icon={<Icons.Edit size={16} />}
                  onClick={() => {
                    setEditControllerDetails(controllerDetails);
                    setIsEditingControllerDetails(true);
                  }}
                  style={{ flexShrink: 0 }}
                >
                  Edit
                </Button>
              )}
            </Flex>
          </div>

          {/* Processing Overview - Single instance at assessment level */}
          {/* Show filled state for all existing assessments, empty state only for brand new assessments with id "new" */}
          <Card title="PROCESSING OVERVIEW" style={{ marginBottom: 24 }}>
            <Flex gap="large" wrap="wrap" style={{ marginBottom: 24 }}>
              {/* Scope Card */}
              <Card
                style={{
                  flex: "1 1 200px",
                  minWidth: 200,
                  border: `1px solid ${palette.FIDESUI_NEUTRAL_75}`,
                  borderRadius: 8,
                  padding: 16,
                  backgroundColor: palette.FIDESUI_BG_CORINTH,
                }}
                bodyStyle={{ padding: 0 }}
              >
                <Text
                  type="secondary"
                  style={{
                    fontSize: 12,
                    textTransform: "uppercase",
                    display: "block",
                    marginBottom: 8,
                  }}
                >
                  SCOPE
                </Text>
                {assessmentId === "new" ? (
                  <>
                    <Text
                      type="secondary"
                      style={{
                        fontSize: 14,
                        display: "block",
                        marginBottom: 8,
                        fontStyle: "italic",
                      }}
                    >
                      No data categories identified yet
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Complete your data mapping to populate
                    </Text>
                  </>
                ) : (
                  <>
                    <Text
                      strong
                      style={{
                        fontSize: 16,
                        display: "block",
                        marginBottom: 8,
                      }}
                    >
                      2 Categories Identified
                    </Text>
                    <Space size="small" wrap>
                      <Tag color={CUSTOM_TAG_COLOR.CORINTH}>PII</Tag>
                      <Tag color={CUSTOM_TAG_COLOR.CORINTH}>
                        Behavioral Data
                      </Tag>
                    </Space>
                  </>
                )}
              </Card>

              {/* Nature Card */}
              <Card
                style={{
                  flex: "1 1 200px",
                  minWidth: 200,
                  border: `1px solid ${palette.FIDESUI_NEUTRAL_75}`,
                  borderRadius: 8,
                  padding: 16,
                  backgroundColor: palette.FIDESUI_BG_CORINTH,
                }}
                bodyStyle={{ padding: 0 }}
              >
                <Text
                  type="secondary"
                  style={{
                    fontSize: 12,
                    textTransform: "uppercase",
                    display: "block",
                    marginBottom: 8,
                  }}
                >
                  NATURE
                </Text>
                {assessmentId === "new" ? (
                  <>
                    <Text
                      type="secondary"
                      style={{
                        fontSize: 14,
                        display: "block",
                        marginBottom: 8,
                        fontStyle: "italic",
                      }}
                    >
                      Processing details not yet defined
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Define how data will be processed
                    </Text>
                  </>
                ) : (
                  <>
                    <Flex
                      align="center"
                      gap="small"
                      style={{ marginBottom: 8 }}
                    >
                      <ThunderboltOutlined
                        style={{
                          fontSize: 16,
                          color: palette.FIDESUI_MINOS,
                        }}
                      />
                      <Text strong style={{ fontSize: 16 }}>
                        AI Analysis
                      </Text>
                    </Flex>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Automated Processing
                    </Text>
                  </>
                )}
              </Card>

              {/* Context Card */}
              <Card
                style={{
                  flex: "1 1 200px",
                  minWidth: 200,
                  border: `1px solid ${palette.FIDESUI_NEUTRAL_75}`,
                  borderRadius: 8,
                  padding: 16,
                  backgroundColor: palette.FIDESUI_BG_CORINTH,
                }}
                bodyStyle={{ padding: 0 }}
              >
                <Text
                  type="secondary"
                  style={{
                    fontSize: 12,
                    textTransform: "uppercase",
                    display: "block",
                    marginBottom: 8,
                  }}
                >
                  CONTEXT
                </Text>
                {assessmentId === "new" ? (
                  <>
                    <Text
                      type="secondary"
                      style={{
                        fontSize: 14,
                        display: "block",
                        marginBottom: 8,
                        fontStyle: "italic",
                      }}
                    >
                      Stakeholder information pending
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Identify who is affected by processing
                    </Text>
                  </>
                ) : (
                  <>
                    <Flex
                      align="center"
                      gap="small"
                      style={{ marginBottom: 8 }}
                    >
                      <GlobalOutlined
                        style={{
                          fontSize: 16,
                          color: palette.FIDESUI_MINOS,
                        }}
                      />
                      <Text strong style={{ fontSize: 16 }}>
                        External
                      </Text>
                    </Flex>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Customer Facing
                    </Text>
                  </>
                )}
              </Card>
            </Flex>

            {assessmentId !== "new" && (
              <Flex justify="flex-end" align="center" wrap="wrap" gap="small">
                <Flex align="center" gap="small">
                  <CheckCircleOutlined
                    style={{
                      color: palette.FIDESUI_SUCCESS,
                      fontSize: 14,
                    }}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Overview populated from system data
                  </Text>
                </Flex>
              </Flex>
            )}
          </Card>

          <Form
            form={form}
            layout="vertical"
            onValuesChange={handleFormValuesChange}
          >
            <Collapse
              activeKey={expandedKeys}
              onChange={(keys) => setExpandedKeys(keys as string[])}
              className="privacy-assessment-collapse"
              style={{
                backgroundColor: "white",
                border: "1px solid #f0f0f0",
                borderRadius: 8,
              }}
            >
              <Panel
                header={
                  <>
                    {expandedKeys.includes("1") ? (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "1",
                              "Identify the need for a DPIA",
                              true,
                            )}
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>1/1</span>
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
                                handleOpenEvidence("1");
                              }}
                              size="small"
                            >
                              View evidence
                            </Button>
                            <Button icon={<SlackOutlined />} size="small">
                              Request input from team
                            </Button>
                            <Flex align="center" gap="small">
                              <CheckCircleOutlined
                                style={{
                                  color: palette.FIDESUI_SUCCESS,
                                  fontSize: 14,
                                }}
                              />
                              <Text type="secondary" style={{ fontSize: 11 }}>
                                Request sent 2h ago to @DataSteward
                              </Text>
                            </Flex>
                          </Flex>
                        </div>
                      </Flex>
                    ) : (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "1",
                              "Identify the need for a DPIA",
                              false,
                            )}
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>1/1</span>
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
                        </div>
                      </Flex>
                    )}
                    <div className="status-tag-container">
                      <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                    </div>
                  </>
                }
                key="1"
              >
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <div
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
                      <Text strong>Identify the need for a DPIA</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.dpiaNeed}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          dpiaNeed: value,
                        })
                      }
                      placeholder="Summarise why you identified the need for a DPIA."
                      renderContent={(text) =>
                        renderTextWithSourceLinks(text, "1")
                      }
                      onComment={() => {
                        // TODO: Open comment modal/thread
                      }}
                      onRequestInput={() => {
                        // TODO: Open team input request
                      }}
                    />
                  </div>
                </Space>
              </Panel>

              <Panel
                header={
                  <>
                    {expandedKeys.includes("2") ? (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "2",
                              "Describe the processing",
                              true,
                            )}
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
                              Updated 5m ago by{" "}
                              <Tag
                                color={CUSTOM_TAG_COLOR.DEFAULT}
                                style={{ marginLeft: 4 }}
                              >
                                AI
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "5/5" : "4/5"}
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
                                handleOpenEvidence("2");
                              }}
                              size="small"
                            >
                              View evidence
                            </Button>
                            <Button icon={<SlackOutlined />} size="small">
                              Request input from team
                            </Button>
                            <Flex align="center" gap="small">
                              <CheckCircleOutlined
                                style={{
                                  color: palette.FIDESUI_SUCCESS,
                                  fontSize: 14,
                                }}
                              />
                              <Text type="secondary" style={{ fontSize: 11 }}>
                                Request sent 1h ago to @PrivacyTeam
                              </Text>
                            </Flex>
                          </Flex>
                        </div>
                      </Flex>
                    ) : (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "2",
                              "Describe the processing",
                              false,
                            )}
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>5/5</span>
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
                        </div>
                      </Flex>
                    )}
                    <div className="status-tag-container">
                      <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                    </div>
                  </>
                }
                key="2"
              >
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <div
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
                      <Text strong>Assessment framework</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.framework}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          framework: value,
                        })
                      }
                      placeholder="Enter assessment framework"
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>Nature of processing</Text>
                      <Flex gap="small" align="center">
                        <Text type="success" style={{ fontSize: 12 }}>
                          HIGH CONFIDENCE
                        </Text>
                        <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>AI</Tag>
                      </Flex>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.nature}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          nature: value,
                        })
                      }
                      placeholder="How will you collect, use, store and delete data? What is the source of the data? Will you be sharing data with anyone? What types of processing identified as likely high risk are involved?"
                      renderContent={(text) =>
                        renderTextWithSourceLinks(text, "2")
                      }
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>Scope of the processing</Text>
                      <Flex gap="small" align="center">
                        <Text type="success" style={{ fontSize: 12 }}>
                          MEDIUM CONFIDENCE
                        </Text>
                        <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG + AI</Tag>
                      </Flex>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.scope}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          scope: value,
                        })
                      }
                      placeholder="What is the nature of the data, and does it include special category or criminal offence data? How much data will you be collecting and using? How often? How long will you keep it? How many individuals are affected? What geographical area does it cover?"
                      renderContent={(text) =>
                        renderTextWithSourceLinks(text, "2")
                      }
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>Context of the processing</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.context}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          context: value,
                        })
                      }
                      placeholder="What is the nature of your relationship with the individuals? How much control will they have? Would they expect you to use their data in this way? Do they include children or other vulnerable groups? Are there prior concerns over this type of processing or security flaws?"
                      renderContent={(text) =>
                        renderTextWithSourceLinks(text, "2")
                      }
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>Purposes of the processing</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.purposes}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          purposes: value,
                        })
                      }
                      placeholder="What do you want to achieve? What is the intended effect on individuals? What are the benefits of the processing – for you, and more broadly?"
                      renderContent={(text) =>
                        renderTextWithSourceLinks(text, "2")
                      }
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>
                </Space>
              </Panel>

              <Panel
                header={
                  <>
                    {expandedKeys.includes("3") ? (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "3",
                              "Consultation process",
                              true,
                            )}
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
                              Updated 1h ago by{" "}
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "3/3" : "2/3"}
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
                                handleOpenEvidence("3");
                              }}
                              size="small"
                            >
                              View evidence
                            </Button>
                            <Button icon={<SlackOutlined />} size="small">
                              Request input from team
                            </Button>
                            <Flex align="center" gap="small">
                              <CheckCircleOutlined
                                style={{
                                  color: palette.FIDESUI_SUCCESS,
                                  fontSize: 14,
                                }}
                              />
                              <Text type="secondary" style={{ fontSize: 11 }}>
                                Request sent 30m ago to @LegalTeam
                              </Text>
                            </Flex>
                          </Flex>
                        </div>
                      </Flex>
                    ) : (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "3",
                              "Consultation process",
                              false,
                            )}
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
                              Updated 1h ago by{" "}
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "3/3" : "2/3"}
                              </span>
                            </Text>
                          </Flex>
                        </div>
                      </Flex>
                    )}
                    <div className="status-tag-container">
                      {isCompletedAssessment ? (
                        <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                      ) : (
                        <Tag color={CUSTOM_TAG_COLOR.WARNING}>In progress</Tag>
                      )}
                    </div>
                  </>
                }
                key="3"
              >
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <div
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
                      <Text strong>Stakeholder consultation</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.stakeholderConsultation}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          stakeholderConsultation: value,
                        })
                      }
                      placeholder="Consider how to consult with relevant stakeholders: describe when and how you will seek individuals' views – or justify why it's not appropriate to do so. Who else do you need to involve within your organisation? Do you need to ask your processors to assist? Do you plan to consult information security experts, or any other experts?"
                      renderContent={(text) =>
                        renderTextWithSourceLinks(text, "3")
                      }
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>
                </Space>
              </Panel>

              <Panel
                header={
                  <>
                    {expandedKeys.includes("4") ? (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "4",
                              "Assess necessity and proportionality",
                              true,
                            )}
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
                              Updated 5m ago by{" "}
                              <Tag
                                color={CUSTOM_TAG_COLOR.DEFAULT}
                                style={{ marginLeft: 4 }}
                              >
                                AI
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "1/1" : "0/1"}
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
                                handleOpenEvidence("4");
                              }}
                              size="small"
                            >
                              View evidence
                            </Button>
                            <Button icon={<SlackOutlined />} size="small">
                              Request input from team
                            </Button>
                            <Flex align="center" gap="small">
                              <CheckCircleOutlined
                                style={{
                                  color: palette.FIDESUI_SUCCESS,
                                  fontSize: 14,
                                }}
                              />
                              <Text type="secondary" style={{ fontSize: 11 }}>
                                Request sent 15m ago to @ComplianceTeam
                              </Text>
                            </Flex>
                          </Flex>
                        </div>
                      </Flex>
                    ) : (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "4",
                              "Assess necessity and proportionality",
                              false,
                            )}
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
                              Updated 5m ago by{" "}
                              <Tag
                                color={CUSTOM_TAG_COLOR.DEFAULT}
                                style={{ marginLeft: 4 }}
                              >
                                AI
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>4/4</span>
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
                        </div>
                      </Flex>
                    )}
                    <div className="status-tag-container">
                      <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                    </div>
                  </>
                }
                key="4"
              >
                <Form layout="vertical">
                  <Space
                    direction="vertical"
                    size="large"
                    style={{ width: "100%" }}
                  >
                    <div
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
                          Compliance and proportionality measures
                        </Text>
                        <Flex gap="small" align="center">
                          <Text type="success" style={{ fontSize: 12 }}>
                            HIGH CONFIDENCE
                          </Text>
                          <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>AI</Tag>
                        </Flex>
                      </Flex>
                      <EditableTextBlock
                        value={documentContent.complianceMeasures}
                        onChange={(value) =>
                          setDocumentContent({
                            ...documentContent,
                            complianceMeasures: value,
                          })
                        }
                        placeholder="What is your lawful basis for processing? Does the processing actually achieve your purpose? Is there another way to achieve the same outcome? How will you prevent function creep? How will you ensure data quality and data minimisation? What information will you give individuals? How will you help to support their rights? What measures do you take to ensure processors comply? How do you safeguard any international transfers?"
                        renderContent={(text) =>
                          renderTextWithSourceLinks(text, "4")
                        }
                        onComment={() => {
                          // TODO: Open comment modal/thread
                        }}
                        onRequestInput={() => {
                          // TODO: Open team input request
                        }}
                      />
                    </div>
                  </Space>
                </Form>
              </Panel>

              <Panel
                header={
                  <>
                    {expandedKeys.includes("5") ? (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "5",
                              "Identify and assess risks",
                              true,
                            )}
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
                              Updated 3h ago by{" "}
                              <Tag
                                color={CUSTOM_TAG_COLOR.DEFAULT}
                                style={{ marginLeft: 4 }}
                              >
                                JG
                              </Tag>
                              <span style={{ marginLeft: 4, marginRight: 4 }}>
                                +
                              </span>
                              <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>AI</Tag>
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "1/1" : "0/1"}
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
                                  backgroundColor: palette.FIDESUI_WARNING,
                                }}
                              />
                              <Text style={{ fontSize: 11 }}>Risk: Medium</Text>
                            </Flex>
                          </Flex>
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
                                handleOpenEvidence("5");
                              }}
                              size="small"
                            >
                              View evidence
                            </Button>
                            <Button icon={<SlackOutlined />} size="small">
                              Request input from team
                            </Button>
                            <Flex align="center" gap="small">
                              <CheckCircleOutlined
                                style={{
                                  color: palette.FIDESUI_SUCCESS,
                                  fontSize: 14,
                                }}
                              />
                              <Text type="secondary" style={{ fontSize: 11 }}>
                                Request sent 4h ago to @RiskTeam
                              </Text>
                            </Flex>
                          </Flex>
                        </div>
                      </Flex>
                    ) : (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "5",
                              "Identify and assess risks",
                              false,
                            )}
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
                              Updated 15m ago by{" "}
                              <Tag
                                color={CUSTOM_TAG_COLOR.DEFAULT}
                                style={{ marginLeft: 4 }}
                              >
                                JG
                              </Tag>
                              <span style={{ marginLeft: 8, marginRight: 8 }}>
                                +
                              </span>
                              <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>AI</Tag>
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
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "4/4" : "2/4"}
                              </span>
                            </Text>
                          </Flex>
                        </div>
                      </Flex>
                    )}
                    <div className="status-tag-container">
                      {isCompletedAssessment ? (
                        <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                      ) : (
                        <Tag color={CUSTOM_TAG_COLOR.WARNING}>In progress</Tag>
                      )}
                    </div>
                  </>
                }
                key="5"
              >
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <div
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
                      <Text strong>Risk assessment</Text>
                      <Flex gap="small" align="center">
                        <Text type="success" style={{ fontSize: 12 }}>
                          MEDIUM CONFIDENCE
                        </Text>
                        <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG + AI</Tag>
                      </Flex>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.risks}
                      onChange={(value) =>
                        setDocumentContent({ ...documentContent, risks: value })
                      }
                      placeholder="Describe source of risk and nature of potential impact on individuals. Include associated compliance and corporate risks as necessary. For each risk, assess the likelihood of harm (Remote, possible or probable) and severity of harm (Minimal, significant or severe) to determine overall risk (Low, medium or high)."
                      renderContent={(text) =>
                        renderTextWithSourceLinks(text, "5")
                      }
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>
                </Space>
              </Panel>

              <Panel
                header={
                  <>
                    {expandedKeys.includes("6") ? (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "6",
                              "Identify measures to reduce risk",
                              true,
                            )}
                          </Flex>
                          <Flex
                            gap="middle"
                            align="center"
                            wrap="wrap"
                            style={{ marginBottom: 8 }}
                          >
                            {isCompletedAssessment && (
                              <Text
                                type="secondary"
                                style={{
                                  fontSize: 11,
                                  lineHeight: "16px",
                                  display: "inline-flex",
                                  alignItems: "center",
                                }}
                              >
                                Updated 1d ago by{" "}
                                <Tag
                                  color={CUSTOM_TAG_COLOR.DEFAULT}
                                  style={{ marginLeft: 4 }}
                                >
                                  JG
                                </Tag>
                              </Text>
                            )}
                            <Text
                              type="secondary"
                              style={{
                                fontSize: 11,
                                lineHeight: "16px",
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                            >
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "1/1" : "0/1"}
                              </span>
                            </Text>
                            {isCompletedAssessment && (
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
                            )}
                          </Flex>
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
                                handleOpenEvidence("6");
                              }}
                              size="small"
                            >
                              View evidence
                            </Button>
                            <Button icon={<SlackOutlined />} size="small">
                              Request input from team
                            </Button>
                          </Flex>
                        </div>
                      </Flex>
                    ) : (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "6",
                              "Identify measures to reduce risk",
                              false,
                            )}
                          </Flex>
                          <Flex
                            gap="middle"
                            align="center"
                            wrap="wrap"
                            style={{ marginBottom: 8 }}
                          >
                            {isCompletedAssessment && (
                              <Text
                                type="secondary"
                                style={{
                                  fontSize: 11,
                                  lineHeight: "16px",
                                  display: "inline-flex",
                                  alignItems: "center",
                                }}
                              >
                                Updated 3d ago by{" "}
                                <Tag
                                  color={CUSTOM_TAG_COLOR.DEFAULT}
                                  style={{ marginLeft: 4 }}
                                >
                                  JG
                                </Tag>
                              </Text>
                            )}
                            <Text
                              type="secondary"
                              style={{
                                fontSize: 11,
                                lineHeight: "16px",
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                            >
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "3/3" : "0/3"}
                              </span>
                            </Text>
                            {isCompletedAssessment && (
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
                            )}
                          </Flex>
                        </div>
                      </Flex>
                    )}
                    <div className="status-tag-container">
                      {isCompletedAssessment ? (
                        <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                      ) : (
                        <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>Incomplete</Tag>
                      )}
                    </div>
                  </>
                }
                key="6"
              >
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <div
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
                      <Text strong>Measures to reduce or eliminate risk</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.measures}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          measures: value,
                        })
                      }
                      placeholder="Identify additional measures you could take to reduce or eliminate risks identified as medium or high risk in step 5. For each risk, describe: Options to reduce or eliminate risk, Effect on risk (Eliminated, reduced, accepted), Residual risk (Low, medium, high), and whether the measure is approved (Yes/no)."
                      renderContent={(text) =>
                        renderTextWithSourceLinks(text, "6")
                      }
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>
                </Space>
              </Panel>

              <Panel
                header={
                  <>
                    {expandedKeys.includes("7") ? (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "7",
                              "Sign off and record outcomes",
                              true,
                            )}
                          </Flex>
                          <Flex
                            gap="middle"
                            align="center"
                            wrap="wrap"
                            style={{ marginBottom: 8 }}
                          >
                            {isCompletedAssessment && (
                              <Text
                                type="secondary"
                                style={{
                                  fontSize: 11,
                                  lineHeight: "16px",
                                  display: "inline-flex",
                                  alignItems: "center",
                                }}
                              >
                                Updated 2d ago by{" "}
                                <Tag
                                  color={CUSTOM_TAG_COLOR.DEFAULT}
                                  style={{ marginLeft: 4 }}
                                >
                                  JG
                                </Tag>
                              </Text>
                            )}
                            <Text
                              type="secondary"
                              style={{
                                fontSize: 11,
                                lineHeight: "16px",
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                            >
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "7/7" : "0/7"}
                              </span>
                            </Text>
                            {isCompletedAssessment && (
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
                            )}
                          </Flex>
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
                                handleOpenEvidence("7");
                              }}
                              size="small"
                            >
                              View evidence
                            </Button>
                            <Button icon={<SlackOutlined />} size="small">
                              Request input from team
                            </Button>
                          </Flex>
                        </div>
                      </Flex>
                    ) : (
                      <Flex
                        gap="large"
                        align="flex-start"
                        style={{ flex: 1, minWidth: 0 }}
                      >
                        <div style={{ flex: 1 }}>
                          <Flex
                            justify="space-between"
                            align="center"
                            style={{ marginBottom: 12, alignItems: "center" }}
                          >
                            {renderSectionTitle(
                              "7",
                              "Sign off and record outcomes",
                              false,
                            )}
                          </Flex>
                          <Flex
                            gap="middle"
                            align="center"
                            wrap="wrap"
                            style={{ marginBottom: 8 }}
                          >
                            {isCompletedAssessment && (
                              <Text
                                type="secondary"
                                style={{
                                  fontSize: 11,
                                  lineHeight: "16px",
                                  display: "inline-flex",
                                  alignItems: "center",
                                }}
                              >
                                Updated 2d ago by{" "}
                                <Tag
                                  color={CUSTOM_TAG_COLOR.DEFAULT}
                                  style={{ marginLeft: 4 }}
                                >
                                  JG
                                </Tag>
                              </Text>
                            )}
                            <Text
                              type="secondary"
                              style={{
                                fontSize: 11,
                                lineHeight: "16px",
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                            >
                              <Text strong>Fields:</Text>{" "}
                              <span style={{ marginLeft: 4 }}>
                                {isCompletedAssessment ? "6/6" : "0/6"}
                              </span>
                            </Text>
                            {isCompletedAssessment && (
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
                            )}
                          </Flex>
                        </div>
                      </Flex>
                    )}
                    <div className="status-tag-container">
                      {isCompletedAssessment ? (
                        <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                      ) : (
                        <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>Incomplete</Tag>
                      )}
                    </div>
                  </>
                }
                key="7"
              >
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <div
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
                      <Text strong>Measures approved by</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.measuresApprovedBy}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          measuresApprovedBy: value,
                        })
                      }
                      placeholder="Name/date - Integrate actions back into project plan, with date and responsibility for completion"
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>Residual risks approved by</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.residualRisksApprovedBy}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          residualRisksApprovedBy: value,
                        })
                      }
                      placeholder="Name/date - If accepting any residual high risk, consult the ICO before going ahead"
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>DPO advice provided</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.dpoAdviceProvided}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          dpoAdviceProvided: value,
                        })
                      }
                      placeholder="Name/date - DPO should advise on compliance, step 6 measures and whether processing can proceed"
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>Summary of DPO advice</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.dpoAdviceSummary}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          dpoAdviceSummary: value,
                        })
                      }
                      placeholder="Enter summary of DPO advice"
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>DPO advice accepted or overruled by</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.dpoAdviceAccepted}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          dpoAdviceAccepted: value,
                        })
                      }
                      placeholder="Name/date - If overruled, you must explain your reasons"
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>Consultation responses reviewed by</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.consultationReviewedBy}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          consultationReviewedBy: value,
                        })
                      }
                      placeholder="Name/date - If your decision departs from individuals' views, you must explain your reasons"
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>

                  <div
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
                      <Text strong>This DPIA will be kept under review by</Text>
                      <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>JG</Tag>
                    </Flex>
                    <EditableTextBlock
                      value={documentContent.dpiaReviewBy}
                      onChange={(value) =>
                        setDocumentContent({
                          ...documentContent,
                          dpiaReviewBy: value,
                        })
                      }
                      placeholder="Name/date - The DPO should also review ongoing compliance with DPIA"
                      onComment={() => {
                        /* TODO: Open comment modal/thread */
                      }}
                      onRequestInput={() => {
                        /* TODO: Request team input */
                      }}
                    />
                  </div>
                </Space>
              </Panel>
            </Collapse>
          </Form>
        </Space>
      </div>

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
            <Space>
              <Button
                type="text"
                icon={<DownloadOutlined />}
                size="small"
                onClick={() => {
                  // Handle export
                }}
              >
                Export
              </Button>
            </Space>
          </Flex>
        }
        placement="right"
        onClose={() => {
          setIsDrawerOpen(false);
          setFocusedQuestionId(null);
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
        afterOpenChange={(open) => {
          if (open && focusedQuestionId) {
            // Expand the focused question if not already expanded
            if (!evidenceExpandedSections.includes(focusedQuestionId)) {
              setEvidenceExpandedSections([
                ...evidenceExpandedSections,
                focusedQuestionId,
              ]);
            }
            // Scroll to focused question after drawer opens
            setTimeout(() => {
              const element = document.querySelector(
                `[data-question-id="${focusedQuestionId}"]`,
              );
              if (element) {
                element.scrollIntoView({ behavior: "smooth", block: "start" });
                // Remove focus highlight after a delay
                setTimeout(() => {
                  setFocusedQuestionId(null);
                }, 3000);
              }
            }, 200);
          }
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
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            {Object.entries(filteredEvidenceByQuestion).map(
              ([questionId, evidence]) => {
                const systemKey = `${questionId}-system`;
                const humanKey = `${questionId}-human`;
                const isSystemExpanded =
                  expandedSystemItems[systemKey] ?? false;
                const isHumanExpanded = expandedHumanItems[humanKey] ?? false;
                // Default to collapsed (true = collapsed, false = expanded)
                const isSystemCollapsed =
                  collapsedSystemSections[systemKey] ?? true;
                const isHumanCollapsed =
                  collapsedHumanSections[humanKey] ?? true;
                const DEFAULT_ITEMS_TO_SHOW = 2;

                // Combine system and analysis items, sort by timestamp (newest first)
                const allSystemItems = [...evidence.system].sort(
                  (a, b) =>
                    new Date(b.timestamp).getTime() -
                    new Date(a.timestamp).getTime(),
                );
                const visibleSystemItems = isSystemExpanded
                  ? allSystemItems
                  : allSystemItems.slice(0, DEFAULT_ITEMS_TO_SHOW);
                const remainingSystemCount =
                  allSystemItems.length - DEFAULT_ITEMS_TO_SHOW;

                const visibleHumanItems = isHumanExpanded
                  ? evidence.human
                  : evidence.human.slice(0, DEFAULT_ITEMS_TO_SHOW);
                const remainingHumanCount =
                  evidence.human.length - DEFAULT_ITEMS_TO_SHOW;

                const renderSystemItem = (
                  item: SystemEvidenceItem | AnalysisEvidenceItem,
                ) => {
                  const isAnalysis = item.type === "analysis";
                  const systemRefs =
                    isAnalysis && item.references
                      ? evidence.system.filter((e) =>
                          item.references?.includes(e.id),
                        )
                      : [];
                  const humanRefs =
                    isAnalysis && item.references
                      ? evidence.human.filter((e) =>
                          item.references?.includes(e.id),
                        )
                      : [];
                  const allRefs = [...systemRefs, ...humanRefs];

                  if (isAnalysis) {
                    return (
                      <Card
                        key={item.id}
                        size="small"
                        style={{
                          backgroundColor: "#FFFFFF",
                          border: "1px solid #E8EBED",
                          borderRadius: 8,
                          transition: "all 0.15s ease",
                          marginBottom: 8,
                        }}
                        hoverable
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
                          style={{ marginBottom: 12 }}
                        >
                          <Tag
                            color={CUSTOM_TAG_COLOR.MINOS}
                            style={{ margin: 0, fontSize: 11 }}
                          >
                            {item.subtype === "summary" && "Summary"}
                            {item.subtype === "inference" && "Inference"}
                            {item.subtype === "risk-assessment" &&
                              "Risk assessment"}
                            {item.subtype === "compliance-check" &&
                              "Compliance check"}
                          </Tag>
                        </Flex>
                        <Descriptions
                          column={1}
                          size="small"
                          items={[
                            {
                              key: "generated",
                              label: "Generated",
                              children: formatTimestamp(item.timestamp),
                            },
                            {
                              key: "model",
                              label: "Model",
                              children: item.source.model,
                            },
                            {
                              key: "confidence",
                              label: "Confidence",
                              children: `${item.confidence}%`,
                            },
                          ]}
                        />
                        <Divider
                          style={{
                            margin: "12px 0",
                            borderColor: "#E8EBED",
                          }}
                        />
                        <Text
                          style={{
                            fontSize: 14,
                            color: "#1A1F36",
                            lineHeight: "1.6",
                          }}
                        >
                          {item.content}
                        </Text>
                        {allRefs.length > 0 && (
                          <>
                            <Divider
                              style={{
                                margin: "12px 0",
                                borderColor: "#E8EBED",
                              }}
                            />
                            <Text
                              strong
                              style={{
                                fontSize: 13,
                                display: "block",
                                marginBottom: 8,
                                color: "#1A1F36",
                                fontWeight: 500,
                              }}
                            >
                              Sources:
                            </Text>
                            <List
                              size="small"
                              dataSource={allRefs.map((ref, idx) => ({
                                key: ref.id ?? idx,
                                title:
                                  ref.content.substring(0, 60) +
                                  (ref.content.length > 60 ? "..." : ""),
                                description:
                                  ref.type === "system"
                                    ? `${ref.source.system} • ${formatTimestamp(ref.timestamp)}`
                                    : `${
                                        "person" in ref.source
                                          ? ref.source.person.name
                                          : "Unknown"
                                      } • ${formatTimestamp(ref.timestamp)}`,
                              }))}
                              renderItem={(listItem) => (
                                <List.Item>
                                  <List.Item.Meta
                                    title={listItem.title}
                                    description={listItem.description}
                                  />
                                </List.Item>
                              )}
                            />
                          </>
                        )}
                      </Card>
                    );
                  }

                  return (
                    <List.Item
                      key={item.id}
                      style={{
                        padding: "16px",
                        marginBottom: 8,
                        backgroundColor: "#FFFFFF",
                        borderRadius: 8,
                        border: "1px solid #E8EBED",
                        transition: "all 0.15s ease",
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
                      <List.Item.Meta
                        title={
                          <Flex vertical gap="small" style={{ flex: 1 }}>
                            <Flex align="center" gap="small">
                              <Tag
                                color={CUSTOM_TAG_COLOR.MINOS}
                                style={{
                                  margin: 0,
                                  fontSize: 11,
                                }}
                              >
                                {item.subtype === "data-classification" &&
                                  "Data classification"}
                                {item.subtype === "system-inventory" &&
                                  "System inventory"}
                                {item.subtype === "policy-document" &&
                                  "Policy document"}
                                {item.subtype === "compliance-monitor" &&
                                  "Compliance monitor"}
                              </Tag>
                            </Flex>
                            <Text
                              strong
                              style={{
                                fontSize: 13,
                                color: "#1A1F36",
                                lineHeight: 1.6,
                              }}
                            >
                              {item.content}
                            </Text>
                            <Descriptions
                              column={1}
                              size="small"
                              items={[
                                {
                                  key: "source",
                                  label: "Source",
                                  children: item.source.system,
                                },
                                {
                                  key: "extracted",
                                  label: "Extracted",
                                  children: formatTimestamp(item.timestamp),
                                },
                                ...(item.confidence
                                  ? [
                                      {
                                        key: "confidence",
                                        label: "Confidence",
                                        children: `${item.confidence}%`,
                                      },
                                    ]
                                  : []),
                              ]}
                            />
                          </Flex>
                        }
                      />
                    </List.Item>
                  );
                };

                const collapseContent = (
                  <>
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
                      {getQuestionTitle(questionId)}
                    </Text>

                    {/* System-Derived Data Section */}
                    {allSystemItems.length > 0 && (
                      <div style={{ marginBottom: 8 }}>
                        <Flex
                          align="center"
                          justify="space-between"
                          style={{ marginBottom: 12 }}
                        >
                          <Flex align="center" gap="small">
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
                            <Button
                              type="text"
                              size="small"
                              onClick={() => {
                                setCollapsedSystemSections({
                                  ...collapsedSystemSections,
                                  [systemKey]: !isSystemCollapsed,
                                });
                              }}
                              style={{
                                padding: "0 4px",
                                height: "auto",
                                fontSize: 12,
                                color: CUSTOM_TAG_COLOR.MINOS,
                                display: "flex",
                                alignItems: "center",
                                gap: 4,
                              }}
                              icon={
                                isSystemCollapsed ? (
                                  <RightOutlined
                                    style={{
                                      fontSize: 10,
                                      transition: "transform 0.2s",
                                    }}
                                  />
                                ) : (
                                  <DownOutlined
                                    style={{
                                      fontSize: 10,
                                      transition: "transform 0.2s",
                                    }}
                                  />
                                )
                              }
                            >
                              {isSystemCollapsed ? "Show" : "Hide"}
                            </Button>
                          </Flex>
                          <Badge
                            count={allSystemItems.length}
                            style={{
                              backgroundColor: CUSTOM_TAG_COLOR.MINOS,
                            }}
                          />
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
                          classifications, policies, and monitoring systems,
                          including inferences and summaries generated from
                          system data and human input.
                        </Text>
                        <Collapse
                          activeKey={isSystemCollapsed ? [] : [systemKey]}
                          onChange={(keys) => {
                            setCollapsedSystemSections({
                              ...collapsedSystemSections,
                              [systemKey]: !keys.includes(systemKey),
                            });
                          }}
                          ghost
                          style={{
                            backgroundColor: "transparent",
                          }}
                        >
                          <Panel
                            key={systemKey}
                            header={null}
                            showArrow={false}
                            style={{ padding: 0 }}
                          >
                            <Space
                              direction="vertical"
                              size="middle"
                              style={{ width: "100%" }}
                            >
                              {visibleSystemItems.map((item) => (
                                <div key={item.id}>
                                  {item.type === "analysis" ? (
                                    renderSystemItem(item)
                                  ) : (
                                    <List
                                      dataSource={[item]}
                                      renderItem={renderSystemItem}
                                    />
                                  )}
                                </div>
                              ))}
                              {!isSystemExpanded &&
                                remainingSystemCount > 0 && (
                                  <Button
                                    type="link"
                                    onClick={() => {
                                      setExpandedSystemItems({
                                        ...expandedSystemItems,
                                        [systemKey]: true,
                                      });
                                    }}
                                    style={{
                                      padding: 0,
                                      height: "auto",
                                      fontSize: 13,
                                      color: CUSTOM_TAG_COLOR.MINOS,
                                    }}
                                  >
                                    Show {remainingSystemCount} more
                                    {remainingSystemCount === 1
                                      ? " item"
                                      : " items"}
                                  </Button>
                                )}
                              {isSystemExpanded && remainingSystemCount > 0 && (
                                <Button
                                  type="link"
                                  onClick={() => {
                                    setExpandedSystemItems({
                                      ...expandedSystemItems,
                                      [systemKey]: false,
                                    });
                                  }}
                                  style={{
                                    padding: 0,
                                    height: "auto",
                                    fontSize: 13,
                                    color: CUSTOM_TAG_COLOR.MINOS,
                                  }}
                                >
                                  Show less
                                </Button>
                              )}
                            </Space>
                          </Panel>
                        </Collapse>
                      </div>
                    )}

                    {/* Human Input Section */}
                    {evidence.human.length > 0 && (
                      <div style={{ marginBottom: 8 }}>
                        <Flex
                          align="center"
                          justify="space-between"
                          style={{ marginBottom: 12 }}
                        >
                          <Flex align="center" gap="small">
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
                            <Button
                              type="text"
                              size="small"
                              onClick={() => {
                                setCollapsedHumanSections({
                                  ...collapsedHumanSections,
                                  [humanKey]: !isHumanCollapsed,
                                });
                              }}
                              style={{
                                padding: "0 4px",
                                height: "auto",
                                fontSize: 12,
                                color: CUSTOM_TAG_COLOR.MINOS,
                                display: "flex",
                                alignItems: "center",
                                gap: 4,
                              }}
                              icon={
                                isHumanCollapsed ? (
                                  <RightOutlined
                                    style={{
                                      fontSize: 10,
                                      transition: "transform 0.2s",
                                    }}
                                  />
                                ) : (
                                  <DownOutlined
                                    style={{
                                      fontSize: 10,
                                      transition: "transform 0.2s",
                                    }}
                                  />
                                )
                              }
                            >
                              {isHumanCollapsed ? "Show" : "Hide"}
                            </Button>
                          </Flex>
                          <Badge
                            count={evidence.human.length}
                            style={{
                              backgroundColor: CUSTOM_TAG_COLOR.MINOS,
                            }}
                          />
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
                          Manual entries and stakeholder communications that
                          inform this assessment.
                        </Text>
                        <Collapse
                          activeKey={isHumanCollapsed ? [] : [humanKey]}
                          onChange={(keys) => {
                            setCollapsedHumanSections({
                              ...collapsedHumanSections,
                              [humanKey]: !keys.includes(humanKey),
                            });
                          }}
                          ghost
                          style={{
                            backgroundColor: "transparent",
                          }}
                        >
                          <Panel
                            key={humanKey}
                            header={null}
                            showArrow={false}
                            style={{ padding: 0 }}
                          >
                            <Space
                              direction="vertical"
                              size="middle"
                              style={{ width: "100%" }}
                            >
                              {visibleHumanItems.map((item) => (
                                <Card
                                  key={item.id}
                                  size="small"
                                  style={{
                                    backgroundColor: "#FFFFFF",
                                    border: "1px solid #E8EBED",
                                    borderRadius: 8,
                                    transition: "all 0.15s ease",
                                    marginBottom: 8,
                                  }}
                                  hoverable
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
                                  {item.subtype === "manual-entry" ? (
                                    <>
                                      <Flex
                                        justify="space-between"
                                        align="flex-start"
                                        style={{ marginBottom: 12 }}
                                      >
                                        <Tag
                                          color={CUSTOM_TAG_COLOR.MINOS}
                                          style={{ margin: 0, fontSize: 11 }}
                                        >
                                          Manual entry
                                        </Tag>
                                        {item.status && (
                                          <Tag
                                            color={
                                              // eslint-disable-next-line no-nested-ternary
                                              item.status === "verified"
                                                ? CUSTOM_TAG_COLOR.SUCCESS
                                                : item.status ===
                                                    "pending-review"
                                                  ? CUSTOM_TAG_COLOR.WARNING
                                                  : CUSTOM_TAG_COLOR.DEFAULT
                                            }
                                            style={{
                                              margin: 0,
                                              fontSize: 11,
                                            }}
                                          >
                                            {item.status === "verified" &&
                                              "Verified"}
                                            {item.status === "pending-review" &&
                                              "Pending review"}
                                            {item.status === "draft" && "Draft"}
                                          </Tag>
                                        )}
                                      </Flex>
                                      <Text
                                        style={{
                                          fontSize: 13,
                                          display: "block",
                                          marginBottom: 12,
                                          color: "#1A1F36",
                                          lineHeight: 1.6,
                                        }}
                                      >
                                        {item.content}
                                      </Text>
                                      <Descriptions
                                        column={1}
                                        size="small"
                                        items={[
                                          {
                                            key: "entered",
                                            label: "Entered by",
                                            children: `${item.source.person.name}, ${item.source.person.role}`,
                                          },
                                          {
                                            key: "date",
                                            label: "Date",
                                            children: formatTimestamp(
                                              item.timestamp,
                                            ),
                                          },
                                        ]}
                                      />
                                    </>
                                  ) : (
                                    <>
                                      <Flex
                                        justify="space-between"
                                        align="flex-start"
                                        style={{ marginBottom: 12 }}
                                      >
                                        <Tag
                                          color={CUSTOM_TAG_COLOR.MINOS}
                                          style={{ margin: 0, fontSize: 11 }}
                                        >
                                          Stakeholder communication
                                        </Tag>
                                      </Flex>
                                      <Descriptions
                                        column={1}
                                        size="small"
                                        items={[
                                          {
                                            key: "channel",
                                            label: "Channel",
                                            children: item.channel ?? "N/A",
                                          },
                                          {
                                            key: "participants",
                                            label: "Participants",
                                            children:
                                              item.participants?.join(", ") ??
                                              "N/A",
                                          },
                                          {
                                            key: "thread",
                                            label: "Thread",
                                            children: item.content,
                                          },
                                          {
                                            key: "date",
                                            label: "Date range",
                                            children: formatTimestamp(
                                              item.timestamp,
                                            ),
                                          },
                                          {
                                            key: "messages",
                                            label: "Message count",
                                            children:
                                              item.threadMessages?.length.toString() ??
                                              "0",
                                          },
                                        ]}
                                      />
                                      {item.threadMessages &&
                                        item.threadMessages.length > 0 && (
                                          <Collapse
                                            ghost
                                            style={{ marginTop: 12 }}
                                            items={[
                                              {
                                                key: "thread",
                                                label: `View ${item.threadMessages.length} message${item.threadMessages.length === 1 ? "" : "s"}`,
                                                children: (
                                                  <List
                                                    size="small"
                                                    dataSource={
                                                      item.threadMessages
                                                    }
                                                    renderItem={(msg) => (
                                                      <List.Item
                                                        style={{
                                                          padding: "8px 0",
                                                          borderBottom: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
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
                                                                style={{
                                                                  fontSize: 12,
                                                                }}
                                                              >
                                                                {msg.sender}
                                                              </Text>
                                                              <Text
                                                                type="secondary"
                                                                style={{
                                                                  fontSize: 11,
                                                                }}
                                                              >
                                                                {new Date(
                                                                  msg.timestamp,
                                                                ).toLocaleString(
                                                                  "en-US",
                                                                  {
                                                                    month:
                                                                      "short",
                                                                    day: "numeric",
                                                                    hour: "2-digit",
                                                                    minute:
                                                                      "2-digit",
                                                                  },
                                                                )}
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
                                    </>
                                  )}
                                </Card>
                              ))}
                              {!isHumanExpanded && remainingHumanCount > 0 && (
                                <Button
                                  type="link"
                                  onClick={() => {
                                    setExpandedHumanItems({
                                      ...expandedHumanItems,
                                      [humanKey]: true,
                                    });
                                  }}
                                  style={{
                                    padding: 0,
                                    height: "auto",
                                    fontSize: 13,
                                    color: CUSTOM_TAG_COLOR.MINOS,
                                  }}
                                >
                                  Show {remainingHumanCount} more
                                  {remainingHumanCount === 1
                                    ? " item"
                                    : " items"}
                                </Button>
                              )}
                              {isHumanExpanded && remainingHumanCount > 0 && (
                                <Button
                                  type="link"
                                  onClick={() => {
                                    setExpandedHumanItems({
                                      ...expandedHumanItems,
                                      [humanKey]: false,
                                    });
                                  }}
                                  style={{
                                    padding: 0,
                                    height: "auto",
                                    fontSize: 13,
                                    color: CUSTOM_TAG_COLOR.MINOS,
                                  }}
                                >
                                  Show less
                                </Button>
                              )}
                            </Space>
                          </Panel>
                        </Collapse>
                      </div>
                    )}
                  </>
                );

                // Remove Card wrapper for "Describe the processing" (questionId "2")
                if (questionId === "2") {
                  return (
                    <div
                      key={questionId}
                      data-question-id={questionId}
                      style={{ marginBottom: 16 }}
                    >
                      {collapseContent}
                    </div>
                  );
                }

                return (
                  <Card
                    key={questionId}
                    data-question-id={questionId}
                    style={{
                      border: `1px solid ${focusedQuestionId === questionId ? "#4A6CF7" : "#E8EBED"}`,
                      borderRadius: 12,
                      backgroundColor: "#FFFFFF",
                      boxShadow:
                        focusedQuestionId === questionId
                          ? "0 0 0 2px rgba(74, 108, 247, 0.12)"
                          : "none",
                      transition: "all 0.2s ease",
                      marginBottom: 16,
                    }}
                    bodyStyle={{ padding: "20px" }}
                    hoverable
                    onMouseEnter={(e) => {
                      if (focusedQuestionId !== questionId) {
                        const target = e.currentTarget;
                        target.style.borderColor = "#D1D9E6";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (focusedQuestionId !== questionId) {
                        const target = e.currentTarget;
                        target.style.borderColor = "#E8EBED";
                      }
                    }}
                  >
                    {collapseContent}
                  </Card>
                );
              },
            )}
          </Space>
        </div>
      </Drawer>

      <Modal
        title={
          <Flex align="center" gap="small">
            <CheckCircleOutlined
              style={{ color: palette.FIDESUI_SUCCESS, fontSize: 20 }}
            />
            <span>Assessment Generated</span>
          </Flex>
        }
        open={isReportModalOpen}
        onCancel={() => setIsReportModalOpen(false)}
        footer={null}
        width={600}
      >
        <Space
          direction="vertical"
          size="large"
          style={{ width: "100%", marginTop: 8 }}
        >
          <div
            style={{
              paddingBottom: 24,
              borderBottom: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
            }}
          >
            <Title
              level={5}
              style={{
                marginBottom: 16,
                textTransform: "uppercase",
                fontSize: 11,
                letterSpacing: 1,
                fontWeight: 600,
                color: palette.FIDESUI_NEUTRAL_700,
              }}
            >
              Executive Summary
            </Title>
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Flex align="center" gap="small">
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    backgroundColor: palette.FIDESUI_WARNING,
                  }}
                />
                <Text style={{ fontSize: 14 }}>
                  <Text strong style={{ marginRight: 8 }}>
                    Risk Level:
                  </Text>
                  Medium
                </Text>
              </Flex>
              <Flex align="center" gap="small">
                <SafetyOutlined
                  style={{ color: palette.FIDESUI_MINOS, fontSize: 16 }}
                />
                <Text style={{ fontSize: 14 }}>
                  <Text strong style={{ marginRight: 8 }}>
                    Compliance:
                  </Text>
                  GDPR
                </Text>
              </Flex>
              <Flex align="center" gap="small">
                <ThunderboltOutlined
                  style={{ color: palette.FIDESUI_MINOS, fontSize: 16 }}
                />
                <Text style={{ fontSize: 14 }}>
                  <Text strong style={{ marginRight: 8 }}>
                    Confidence:
                  </Text>
                  94% AI
                </Text>
              </Flex>
            </Space>
          </div>

          <div
            style={{
              paddingBottom: 24,
              borderBottom: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
            }}
          >
            <Title
              level={5}
              style={{
                marginBottom: 16,
                textTransform: "uppercase",
                fontSize: 11,
                letterSpacing: 1,
                fontWeight: 600,
                color: palette.FIDESUI_NEUTRAL_700,
              }}
            >
              Document Details
            </Title>
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Flex justify="space-between" align="center">
                <Text type="secondary" style={{ fontSize: 14 }}>
                  Project:
                </Text>
                <Text strong style={{ fontSize: 14 }}>
                  Customer Insight AI
                </Text>
              </Flex>
              <Flex justify="space-between" align="center">
                <Text type="secondary" style={{ fontSize: 14 }}>
                  Data Types:
                </Text>
                <Space size="small">
                  <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>PII</Tag>
                  <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>Behavioral</Tag>
                </Space>
              </Flex>
              <Flex justify="space-between" align="center">
                <Text type="secondary" style={{ fontSize: 14 }}>
                  Retention:
                </Text>
                <Text strong style={{ fontSize: 14 }}>
                  24 Months
                </Text>
              </Flex>
            </Space>
          </div>

          <div style={{ paddingBottom: 24 }}>
            <Title
              level={5}
              style={{
                marginBottom: 16,
                textTransform: "uppercase",
                fontSize: 11,
                letterSpacing: 1,
                fontWeight: 600,
                color: palette.FIDESUI_NEUTRAL_700,
              }}
            >
              Responsible Parties
            </Title>
            <Flex align="center" gap="middle">
              <Avatar
                size={40}
                style={{ backgroundColor: palette.FIDESUI_MINOS }}
              >
                AM
              </Avatar>
              <Flex vertical gap={4} style={{ flex: 1 }}>
                <Text strong style={{ fontSize: 15 }}>
                  Alex Morgan
                </Text>
                <Flex align="center" gap="small">
                  <Text type="secondary" style={{ fontSize: 13 }}>
                    Privacy Officer • Primary Owner
                  </Text>
                  <EditOutlined
                    style={{
                      fontSize: 13,
                      color: palette.FIDESUI_NEUTRAL_500,
                      cursor: "pointer",
                    }}
                  />
                </Flex>
              </Flex>
            </Flex>
          </div>

          <Flex
            gap="small"
            style={{
              marginTop: 8,
              paddingTop: 24,
              borderTop: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
              justifyContent: "flex-end",
            }}
          >
            <Button
              icon={<FilePdfOutlined />}
              onClick={() => {
                // Handle PDF download
                setIsReportModalOpen(false);
              }}
            >
              Download PDF
            </Button>
            <Button
              type="primary"
              icon={<EditOutlined />}
              onClick={() => {
                // Handle sign document
                setIsReportModalOpen(false);
              }}
            >
              Sign Document
            </Button>
          </Flex>
        </Space>
      </Modal>

      <Modal
        title="Configure Applicable Regions"
        open={isRegionModalOpen}
        onCancel={() => setIsRegionModalOpen(false)}
        onOk={() => setIsRegionModalOpen(false)}
        okText="Save"
        width={600}
      >
        <Space
          direction="vertical"
          size="large"
          style={{ width: "100%", marginTop: 16 }}
        >
          <Text type="secondary" style={{ display: "block", fontSize: 13 }}>
            Select the regions where this assessment applies. This allows you to
            scope a template (e.g., GDPR) to specific jurisdictions.
          </Text>

          <div>
            <Text
              strong
              style={{ display: "block", marginBottom: 12, fontSize: 13 }}
            >
              Selected Regions
            </Text>
            {selectedRegions.length > 0 ? (
              <Flex gap="small" wrap="wrap" style={{ marginBottom: 16 }}>
                {selectedRegions.map((region) => (
                  <Tag
                    key={region}
                    closable
                    onClose={() =>
                      setSelectedRegions(
                        selectedRegions.filter((r) => r !== region),
                      )
                    }
                    style={{ margin: 0, fontSize: 12 }}
                  >
                    {formatRegionDisplay(region)}
                  </Tag>
                ))}
              </Flex>
            ) : (
              <Text
                type="secondary"
                style={{
                  display: "block",
                  marginBottom: 16,
                  fontSize: 12,
                  fontStyle: "italic",
                }}
              >
                No regions selected. The assessment will apply to all regions by
                default.
              </Text>
            )}
          </div>

          <div>
            <Text
              strong
              style={{ display: "block", marginBottom: 12, fontSize: 13 }}
            >
              Add Regions
            </Text>
            <LocationSelect
              mode="multiple"
              value={selectedRegions}
              onChange={(value) => setSelectedRegions(value ?? [])}
              placeholder="Search and select regions..."
              style={{ width: "100%" }}
              allowClear
              showSearch
              includeCountryOnlyOptions
            />
          </div>
        </Space>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        title="Delete assessment"
        open={isDeleteModalOpen}
        onCancel={() => setIsDeleteModalOpen(false)}
        onOk={handleConfirmDelete}
        okText="Delete"
        okButtonProps={{ danger: true }}
        width={480}
      >
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Text>Are you sure you want to delete this assessment?</Text>
          <Text type="secondary">
            This action cannot be undone. All assessment data, including any
            responses and documentation, will be permanently removed.
          </Text>
        </Space>
      </Modal>

      {/* Questions Modal */}
      <Modal
        title={
          <Flex align="center" gap="small">
            <Icons.Information
              size={20}
              style={{ color: palette.FIDESUI_MINOS }}
            />
            <Text strong style={{ fontSize: 18 }}>
              {selectedSectionKey
                ? `${selectedSectionKey}. ${sections.find((s) => s.key === selectedSectionKey)?.title}`
                : "Questions"}
            </Text>
          </Flex>
        }
        open={questionsModalOpen}
        onCancel={() => {
          setQuestionsModalOpen(false);
          setSelectedSectionKey(null);
        }}
        footer={[
          <Button
            key="close"
            onClick={() => {
              setQuestionsModalOpen(false);
              setSelectedSectionKey(null);
            }}
          >
            Close
          </Button>,
        ]}
        width={600}
        styles={{
          body: {
            padding: "20px 24px",
          },
        }}
      >
        {selectedSectionKey && sectionQuestions[selectedSectionKey] && (
          <div style={{ lineHeight: 1.8 }}>
            {sectionQuestions[selectedSectionKey].map((question, index) => (
              <Text
                // eslint-disable-next-line react/no-array-index-key
                key={index}
                style={{
                  fontSize: 14,
                  color: "#1A1F36",
                  display: "block",
                  marginBottom:
                    index < sectionQuestions[selectedSectionKey].length - 1
                      ? 16
                      : 0,
                }}
              >
                {question}
              </Text>
            ))}
          </div>
        )}
      </Modal>
    </Layout>
  );
};

export default PrivacyAssessmentDetailPage;
