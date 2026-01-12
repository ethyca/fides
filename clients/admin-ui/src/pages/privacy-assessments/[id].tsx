import {
  Avatar,
  Button,
  Card,
  Collapse,
  CUSTOM_TAG_COLOR,
  Drawer,
  Flex,
  Form,
  Input,
  LocationSelect,
  Modal,
  Select,
  Space,
  Steps,
  Tag,
  Typography,
  CheckOutlined,
  PlusOutlined,
} from "fidesui";
import React from "react";
// TODO: fix this export to be better encapsulated in fidesui
import palette from "fidesui/src/palette/palette.module.scss";
import {
  InfoCircleOutlined,
  LockOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  GlobalOutlined,
  ThunderboltOutlined,
  CloseOutlined,
  MessageOutlined,
  FilePdfOutlined,
  EditOutlined,
} from "@ant-design/icons";
import type { NextPage } from "next";
import Head from "next/head";
import { useRouter } from "next/router";
import { useState, useEffect, useMemo } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import SearchInput from "~/features/common/SearchInput";
import { formatIsoLocation, isoStringToEntry } from "fidesui/src/components/data-display/location.utils";

const { Title, Text } = Typography;
const { Panel } = Collapse;

interface ChatMessage {
  id: string;
  sender: "astralis" | "jack";
  senderName: string;
  message: string;
  timestamp: string;
}

interface SectionSummary {
  sectionKey: string;
  summary: string;
  isLoading: boolean;
}

/**
 * Generates a lawyer-perspective summary of assessment section answers.
 * This is a mock implementation that can be replaced with a real API call.
 */
const generateSectionSummary = async (
  sectionKey: string,
  sectionTitle: string,
  formValues: Record<string, any>
): Promise<string> => {
  // Mock delay to simulate API call
  await new Promise((resolve) => setTimeout(resolve, 500));

  // Extract answers from form values
  const answers = Object.entries(formValues)
    .filter(([_, value]) => value && typeof value === "string" && value.trim().length > 0)
    .map(([_, value]) => value as string)
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

  return mockSummaries[sectionKey] || `Summary for ${sectionTitle}: ${answers.substring(0, 200)}...`;
};

const PrivacyAssessmentDetailPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const [expandedKeys, setExpandedKeys] = useState<string[]>(["1"]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRegionModalOpen, setIsRegionModalOpen] = useState(false);
  const [sectionSummaries, setSectionSummaries] = useState<Record<string, SectionSummary>>({});
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [form] = Form.useForm();

  // Format region code to display name
  const formatRegionDisplay = (regionCode: string): string => {
    const entry = isoStringToEntry(regionCode);
    if (entry) {
      return formatIsoLocation({ isoEntry: entry, showFlag: true });
    }
    return regionCode;
  };

  // Mock Slack conversation data
  const chatMessages: ChatMessage[] = [
    {
      id: "1",
      sender: "astralis",
      senderName: "Astralis agent",
      message: "I've analyzed the Customer Insight AI Module and identified 2 data categories: PII and Behavioral Data. The processing involves automated AI analysis for personalized recommendations.",
      timestamp: "2:15 PM",
    },
    {
      id: "2",
      sender: "jack",
      senderName: "Jack Gale",
      message: "Thanks! Can you help me understand the data flow? How is the data ingested?",
      timestamp: "2:18 PM",
    },
    {
      id: "3",
      sender: "astralis",
      senderName: "Astralis agent",
      message: "Based on the system architecture, data is ingested via API from the core commerce engine. It's processed in a secure isolated environment with machine learning algorithms analyzing purchase history and browsing behavior.",
      timestamp: "2:19 PM",
    },
    {
      id: "4",
      sender: "jack",
      senderName: "Jack Gale",
      message: "What about the retention period? Do we have that information?",
      timestamp: "2:22 PM",
    },
    {
      id: "5",
      sender: "astralis",
      senderName: "Astralis agent",
      message: "The retention period is 24 months based on the legitimate interest lawful basis. This aligns with the marketing communication opt-in period for customers.",
      timestamp: "2:23 PM",
    },
    {
      id: "6",
      sender: "jack",
      senderName: "Jack Gale",
      message: "Perfect, that helps. I'll update the assessment with this information.",
      timestamp: "2:25 PM",
    },
  ];

  const handleExpandAll = () => {
    setExpandedKeys(["1", "2", "3", "4", "5", "6", "7"]);
  };

  const handleCollapseAll = () => {
    setExpandedKeys([]);
  };

  const sections = [
    { key: "1", title: "Identify the need for a DPIA", fields: ["projectOverview", "dpiaNeed"] },
    { key: "2", title: "Describe the processing", fields: ["projectName", "framework", "nature", "scope", "context", "purposes"] },
    { key: "3", title: "Consultation process", fields: ["stakeholderConsultation"] },
    { key: "4", title: "Assess necessity and proportionality", fields: ["complianceMeasures"] },
    { key: "5", title: "Identify and assess risks", fields: ["risks"] },
    { key: "6", title: "Identify measures to reduce risk", fields: ["measures"] },
    { key: "7", title: "Sign off and record outcomes", fields: ["measuresApprovedBy", "residualRisksApprovedBy", "dpoAdviceProvided", "dpoAdviceSummary", "dpoAdviceAccepted", "consultationReviewedBy", "dpiaReviewBy"] },
  ];

  // Generate summary for a specific section
  const generateSummaryForSection = async (sectionKey: string, allValues: any) => {
    const section = sections.find((s) => s.key === sectionKey);
    if (!section) return;

    const sectionValues: Record<string, any> = {};
    section.fields.forEach((field) => {
      if (allValues[field]) {
        sectionValues[field] = allValues[field];
      }
    });

    // Only generate if we have values and don't already have a summary
    if (Object.keys(sectionValues).length > 0 && !sectionSummaries[sectionKey]?.summary) {
      setSectionSummaries((prev) => ({
        ...prev,
        [sectionKey]: { sectionKey, summary: "", isLoading: true },
      }));

      try {
        const summary = await generateSectionSummary(sectionKey, section.title, sectionValues);
        setSectionSummaries((prev) => ({
          ...prev,
          [sectionKey]: { sectionKey, summary, isLoading: false },
        }));
      } catch (error) {
        setSectionSummaries((prev) => ({
          ...prev,
          [sectionKey]: { sectionKey, summary: "", isLoading: false },
        }));
      }
    }
  };

  // Generate summaries for sections when form values change
  const handleFormValuesChange = async (changedValues: any, allValues: any) => {
    // Find which section was changed
    const changedFields = Object.keys(changedValues);
    const affectedSection = sections.find((section) =>
      section.fields.some((field) => changedFields.includes(field))
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
      // Section 1: projectOverview, dpiaNeed
      const section1Values = {
        projectOverview: formValues.projectOverview || "The Customer Insight AI Module is a machine learning system designed to analyze customer purchase history and browsing behavior to generate personalized product recommendations. This project involves automated processing of personal data through AI algorithms to enhance customer experience and increase sales conversion rates.",
        dpiaNeed: formValues.dpiaNeed || "A DPIA is required because this project involves systematic and extensive evaluation of personal aspects relating to natural persons based on automated processing, including profiling. The processing uses new technologies (AI/ML algorithms) and involves processing of personal data on a large scale, including special category data. The automated decision-making aspects and the scale of data processing present potential high risks to individuals' rights and freedoms.",
      };
      if (section1Values.projectOverview || section1Values.dpiaNeed) {
        generateSummaryForSection("1", section1Values);
      }

      // Section 2: projectName, framework, nature, scope, context, purposes
      const section2Values = {
        projectName: formValues.projectName || "Customer Insight AI Module",
        framework: formValues.framework || "GDPR-DPIA",
        nature: formValues.nature || "The system uses machine learning algorithms to analyze customer purchase history and browsing behavior to generate personalized product recommendations. Data is ingested via API from the core commerce engine and processed in a secure isolated environment.",
        scope: formValues.scope || "Names, email addresses, IP addresses, purchase history, and clickstream data.",
        context: formValues.context || "Data subjects are existing customers who have opted-in to marketing communications. The relationship is direct B2C. There are no known vulnerable groups in the standard customer base.",
        purposes: formValues.purposes || "",
      };
      if (section2Values.projectName || section2Values.framework || section2Values.nature || section2Values.scope || section2Values.context) {
        generateSummaryForSection("2", section2Values);
      }

      // Section 4: complianceMeasures
      const section4Values = {
        complianceMeasures: formValues.complianceMeasures || "Lawful basis: Legitimate interests (Article 6(1)(f)) for personalized recommendations to enhance customer experience. The processing achieves the purpose of providing relevant product suggestions, and there is no less intrusive alternative that would achieve the same outcome. Function creep is prevented through strict access controls and regular audits. Data quality is ensured through validation at ingestion points and automated data cleansing processes. Data minimisation is achieved by only processing necessary data fields (purchase history, browsing behavior) and implementing data retention policies (24 months). Individuals are informed through privacy notices and cookie banners. Data subject rights are supported through a self-service portal for access, rectification, erasure, and objection requests. Processors are contractually bound through Data Processing Agreements (DPAs) with specific security and compliance requirements. International transfers are safeguarded through Standard Contractual Clauses (SCCs) and adequacy decisions where applicable.",
      };
      if (section4Values.complianceMeasures) {
        generateSummaryForSection("4", section4Values);
      }
    }, 300);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const steps = [
    {
      title: "Need",
      status: "finish",
    },
    {
      title: "Processing",
      status: "finish",
    },
    {
      title: "Consultation",
      status: "wait",
    },
    {
      title: "Necessity",
      status: "finish",
    },
    {
      title: "Risks",
      status: "process",
    },
    {
      title: "Measures",
      status: "wait",
    },
    {
      title: "Sign off",
      status: "wait",
    },
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
              <Flex align="center" gap="small" wrap="wrap" style={{ maxWidth: "100%" }}>
                <span style={{ flexShrink: 0 }}>Customer Insight AI Module</span>
                <Tag style={{ fontSize: 12, margin: 0, backgroundColor: palette.FIDESUI_NEUTRAL_300, border: "none", color: palette.FIDESUI_MINOS, flexShrink: 0 }}>
                  GDPR DPIA
                </Tag>
                {selectedRegions.length > 0 && (
                  <Flex align="center" gap="small" wrap="wrap" style={{ flexShrink: 0 }}>
                    <GlobalOutlined style={{ fontSize: 12, color: palette.FIDESUI_NEUTRAL_500 }} />
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
                      style={{ padding: 0, height: "auto", fontSize: 11, whiteSpace: "nowrap" }}
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
                    style={{ padding: 0, height: "auto", fontSize: 12, whiteSpace: "nowrap" }}
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
            <Button style={{ whiteSpace: "nowrap" }}>Save as draft</Button>
            <Button type="primary" onClick={() => setIsReportModalOpen(true)} style={{ whiteSpace: "nowrap" }}>Generate report</Button>
          </Space>
        }
      />
      <div style={{ padding: "24px 24px", maxWidth: "100%", overflowX: "hidden" }} className="assessment-page-container">
        <Space direction="vertical" size="large" style={{ width: "100%", maxWidth: "100%" }}>
          <div style={{ overflowX: "auto", marginBottom: 32 }}>
            <Steps
              current={2}
              size="small"
              items={steps.map((step, index) => ({
                title: step.title,
                status: step.status as any,
              }))}
              style={{ minWidth: 600 }}
            />
          </div>

          <Flex justify="space-between" align="center" wrap="wrap" gap="small" style={{ marginTop: 16 }}>
            <SearchInput
              placeholder="Search risks, authors, or content"
              onChange={() => {}}
              style={{ flex: "1 1 300px", minWidth: 200, maxWidth: 400 }}
            />
            <Flex gap="small" wrap="wrap" style={{ flexShrink: 0 }}>
              <Button type="link" onClick={handleExpandAll} style={{ whiteSpace: "nowrap", fontSize: 13 }}>
                Expand all
              </Button>
              <Button type="link" onClick={handleCollapseAll} style={{ whiteSpace: "nowrap", fontSize: 13 }}>
                Collapse all
              </Button>
            </Flex>
          </Flex>

          <Form form={form} layout="vertical" onValuesChange={handleFormValuesChange}>
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
                    <Flex justify="space-between" align="center" style={{ width: "100%", paddingRight: 140 }}>
                      <Text strong style={{ fontSize: 16 }}>1. Identify the need for a DPIA</Text>
                    </Flex>
                  ) : (
                    <Flex gap="large" align="flex-start" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 12, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            1. Identify the need for a DPIA
                          </Text>
                        </Flex>
                        <Flex gap="middle" align="center" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            Updated 2m ago by{" "}
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 4 }}>JG</Tag>
                          </Text>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            <Text strong>Fields:</Text> <span style={{ marginLeft: 4 }}>2/2</span>
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    {sectionSummaries["1"]?.summary && !sectionSummaries["1"].isLoading && (
                      <Text className="summary-text">
                        <Text style={{ color: palette.FIDESUI_MINOS, fontWeight: 500 }}>Summary:</Text> {sectionSummaries["1"].summary}
                      </Text>
                    )}
                    {sectionSummaries["1"]?.summary && !sectionSummaries["1"].isLoading && (
                      <div className="risk-confidence-container">
                        <Flex gap="small" align="center" style={{ fontSize: 11, color: palette.FIDESUI_NEUTRAL_600, marginBottom: 4 }}>
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
                        <Flex gap="small" align="center" style={{ fontSize: 11, color: palette.FIDESUI_NEUTRAL_600 }}>
                          <div
                            style={{
                              width: 6,
                              height: 6,
                              borderRadius: "50%",
                              backgroundColor: palette.FIDESUI_SUCCESS,
                            }}
                          />
                          <Text style={{ fontSize: 11 }}>Confidence: High</Text>
                        </Flex>
                      </div>
                    )}
                    <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                  </div>
                </>
              }
              key="1"
            >
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <Card
                  title="PROCESSING OVERVIEW"
                  style={{ marginBottom: 24 }}
                >
                  <Flex gap="large" wrap="wrap" style={{ marginBottom: 24 }}>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        SCOPE
                      </Text>
                      <Text strong style={{ fontSize: 16, display: "block", marginBottom: 8 }}>
                        2 Categories Identified
                      </Text>
                      <Space size="small" wrap>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>PII</Tag>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Behavioral Data</Tag>
                      </Space>
                    </Card>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        NATURE
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <ThunderboltOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>AI Analysis</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Automated Processing
                      </Text>
                    </Card>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        CONTEXT
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <GlobalOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>External</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Customer Facing
                      </Text>
                    </Card>
                  </Flex>
                  <Flex justify="space-between" align="center" wrap="wrap" gap="small">
                    <Flex align="center" gap="small">
                      <CheckCircleOutlined style={{ color: palette.FIDESUI_SUCCESS, fontSize: 14 }} />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Request sent 2h ago to @DataSteward
                      </Text>
                    </Flex>
                    <Space wrap>
                      <Button icon={<MessageOutlined />} size="small">
                        Request information from team
                      </Button>
                      <Button type="default" onClick={() => setIsDrawerOpen(true)} size="small">
                        View AI Context
                      </Button>
                    </Space>
                  </Flex>
                </Card>

                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Project overview</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="projectOverview"
                      initialValue="The Customer Insight AI Module is a machine learning system designed to analyze customer purchase history and browsing behavior to generate personalized product recommendations. This project involves automated processing of personal data through AI algorithms to enhance customer experience and increase sales conversion rates."
                    >
                      <Input.TextArea
                        rows={4}
                        placeholder="Explain broadly what the project aims to achieve and what type of processing it involves. You may find it helpful to refer or link to other documents, such as a project proposal."
                      />
                    </Form.Item>
                  </div>

                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Why a DPIA is needed</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="dpiaNeed"
                      initialValue="A DPIA is required because this project involves systematic and extensive evaluation of personal aspects relating to natural persons based on automated processing, including profiling. The processing uses new technologies (AI/ML algorithms) and involves processing of personal data on a large scale, including special category data. The automated decision-making aspects and the scale of data processing present potential high risks to individuals' rights and freedoms."
                    >
                      <Input.TextArea
                        rows={4}
                        placeholder="Summarise why you identified the need for a DPIA."
                      />
                    </Form.Item>
                  </div>
                </Space>
              </Space>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("2") ? (
                    <Flex justify="space-between" align="center" style={{ width: "100%", paddingRight: 140 }}>
                      <Text strong style={{ fontSize: 16 }}>2. Describe the processing</Text>
                    </Flex>
                  ) : (
                    <Flex gap="large" align="flex-start" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 12, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            2. Describe the processing
                          </Text>
                        </Flex>
                        <Flex gap="middle" align="center" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            Updated 2m ago by{" "}
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 4 }}>JG</Tag>
                          </Text>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            <Text strong>Fields:</Text> <span style={{ marginLeft: 4 }}>5/5</span>
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    {sectionSummaries["2"]?.summary && !sectionSummaries["2"].isLoading && (
                      <Text className="summary-text">
                        <Text style={{ color: palette.FIDESUI_MINOS, fontWeight: 500 }}>Summary:</Text> {sectionSummaries["2"].summary}
                      </Text>
                    )}
                    {sectionSummaries["2"]?.summary && !sectionSummaries["2"].isLoading && (
                      <div className="risk-confidence-container">
                        <Flex gap="small" align="center" style={{ fontSize: 11, color: palette.FIDESUI_NEUTRAL_600, marginBottom: 4 }}>
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
                        <Flex gap="small" align="center" style={{ fontSize: 11, color: palette.FIDESUI_NEUTRAL_600 }}>
                          <div
                            style={{
                              width: 6,
                              height: 6,
                              borderRadius: "50%",
                              backgroundColor: palette.FIDESUI_SUCCESS,
                            }}
                          />
                          <Text style={{ fontSize: 11 }}>Confidence: High</Text>
                        </Flex>
                      </div>
                    )}
                    <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                  </div>
                </>
              }
              key="2"
            >
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <Card
                  title="PROCESSING OVERVIEW"
                  style={{ marginBottom: 24 }}
                >
                  <Flex gap="large" wrap="wrap" style={{ marginBottom: 24 }}>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        SCOPE
                      </Text>
                      <Text strong style={{ fontSize: 16, display: "block", marginBottom: 8 }}>
                        2 Categories Identified
                      </Text>
                      <Space size="small" wrap>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>PII</Tag>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Behavioral Data</Tag>
                      </Space>
                    </Card>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        NATURE
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <ThunderboltOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>AI Analysis</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Automated Processing
                      </Text>
                    </Card>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        CONTEXT
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <GlobalOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>External</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Customer Facing
                      </Text>
                    </Card>
                  </Flex>
                  <Flex justify="space-between" align="center" wrap="wrap" gap="small">
                    <Flex align="center" gap="small">
                      <CheckCircleOutlined style={{ color: palette.FIDESUI_SUCCESS, fontSize: 14 }} />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Request sent 2h ago to @DataSteward
                      </Text>
                    </Flex>
                    <Space wrap>
                      <Button icon={<MessageOutlined />} size="small">
                        Request information from team
                      </Button>
                      <Button type="default" onClick={() => setIsDrawerOpen(true)} size="small">
                        View AI Context
                      </Button>
                    </Space>
                  </Flex>
                </Card>

                <Form layout="vertical">
                  <Space direction="vertical" size="large" style={{ width: "100%" }}>
                    <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                      <Flex gap="middle" align="flex-start">
                        <Form.Item
                          label={
                            <Flex justify="space-between" align="center">
                              <Text strong>Project name</Text>
                              <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                            </Flex>
                          }
                          name="projectName"
                          initialValue="Customer Insight AI Module"
                          style={{ flex: 1 }}
                        >
                          <Input />
                        </Form.Item>
                        <Form.Item
                          label={
                            <Flex justify="space-between" align="center">
                              <Text strong>Assessment Framework</Text>
                              <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                            </Flex>
                          }
                          name="framework"
                          initialValue="GDPR-DPIA"
                          style={{ flex: 1 }}
                        >
                          <Select
                            options={[
                              { value: "GDPR-DPIA", label: "GDPR - Data Protection Impact Assessment" },
                              { value: "CCPA-PIA", label: "CCPA Privacy Impact Assessment" },
                            ]}
                          />
                        </Form.Item>
                      </Flex>
                    </div>

                    <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                      <Form.Item
                        label={
                          <Flex justify="space-between" align="center">
                            <Text strong>Nature of processing</Text>
                            <Flex gap="small" align="center">
                              <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 8 }}>
                                AI
                              </Tag>
                              <Text type="success" style={{ fontSize: 12 }}>
                                HIGH CONFIDENCE
                              </Text>
                            </Flex>
                          </Flex>
                        }
                        name="nature"
                      >
                        <Input.TextArea
                          rows={6}
                          defaultValue="The system uses machine learning algorithms to analyze customer purchase history and browsing behavior to generate personalized product recommendations. Data is ingested via API from the core commerce engine and processed in a secure isolated environment."
                          placeholder="How will you collect, use, store and delete data? What is the source of the data? Will you be sharing data with anyone? What types of processing identified as likely high risk are involved?"
                        />
                      </Form.Item>
                    </div>

                    <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                      <Form.Item
                        label={
                          <Flex justify="space-between" align="center">
                            <Text strong>Scope of the processing</Text>
                            <Tag color={CUSTOM_TAG_COLOR.CORINTH} style={{ marginLeft: 8 }}>
                              JG + AI
                            </Tag>
                          </Flex>
                        }
                        name="scope"
                      >
                        <div>
                          <Flex gap="small" wrap="wrap" style={{ marginBottom: 12 }}>
                            <Tag
                              color={CUSTOM_TAG_COLOR.MARBLE}
                              closable
                              onClose={() => {}}
                            >
                              Personal Identifiable Information (PII)
                            </Tag>
                            <Tag
                              color={CUSTOM_TAG_COLOR.MARBLE}
                              closable
                              onClose={() => {}}
                            >
                              Behavioral Data
                            </Tag>
                            <Button type="dashed" size="small" icon={<PlusOutlined />}>
                              Add Category
                            </Button>
                          </Flex>
                          <Input.TextArea
                            rows={4}
                            defaultValue="Names, email addresses, IP addresses, purchase history, and clickstream data."
                            placeholder="What is the nature of the data, and does it include special category or criminal offence data? How much data will you be collecting and using? How often? How long will you keep it? How many individuals are affected? What geographical area does it cover?"
                          />
                        </div>
                      </Form.Item>
                    </div>

                    <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                      <Form.Item
                        label={
                          <Flex justify="space-between" align="center">
                            <Text strong>Context of the processing</Text>
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                          </Flex>
                        }
                        name="context"
                      >
                        <Input.TextArea
                          rows={4}
                          defaultValue="Data subjects are existing customers who have opted-in to marketing communications. The relationship is direct B2C. There are no known vulnerable groups in the standard customer base."
                          placeholder="What is the nature of your relationship with the individuals? How much control will they have? Would they expect you to use their data in this way? Do they include children or other vulnerable groups? Are there prior concerns over this type of processing or security flaws?"
                        />
                      </Form.Item>
                    </div>

                    <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                      <Form.Item
                        label={
                          <Flex justify="space-between" align="center">
                            <Text strong>Purposes of the processing</Text>
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                          </Flex>
                        }
                        name="purposes"
                      >
                        <Input.TextArea
                          rows={4}
                          placeholder="What do you want to achieve? What is the intended effect on individuals? What are the benefits of the processing – for you, and more broadly?"
                        />
                      </Form.Item>
                    </div>
                  </Space>
                </Form>
              </Space>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("3") ? (
                    <Flex justify="space-between" align="center" style={{ width: "100%", paddingRight: 140 }}>
                      <Text strong style={{ fontSize: 16 }}>3. Consultation process</Text>
                    </Flex>
                  ) : (
                    <Flex gap="large" align="flex-start" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 12, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            3. Consultation process
                          </Text>
                        </Flex>
                        <Flex gap="middle" align="center" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            Updated 1h ago by{" "}
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 4 }}>JG</Tag>
                          </Text>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            <Text strong>Fields:</Text> <span style={{ marginLeft: 4 }}>2/3</span>
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.WARNING}>In progress</Tag>
                  </div>
                </>
              }
              key="3"
            >
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <Card
                  title="PROCESSING OVERVIEW"
                  style={{ marginBottom: 24 }}
                >
                  <Flex gap="large" wrap="wrap" style={{ marginBottom: 24 }}>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        SCOPE
                      </Text>
                      <Text strong style={{ fontSize: 16, display: "block", marginBottom: 8 }}>
                        2 Categories Identified
                      </Text>
                      <Space size="small" wrap>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>PII</Tag>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Behavioral Data</Tag>
                      </Space>
                    </Card>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        NATURE
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <ThunderboltOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>AI Analysis</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Automated Processing
                      </Text>
                    </Card>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        CONTEXT
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <GlobalOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>External</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Customer Facing
                      </Text>
                    </Card>
                  </Flex>
                  <Flex justify="space-between" align="center" wrap="wrap" gap="small">
                    <Flex align="center" gap="small">
                      <CheckCircleOutlined style={{ color: palette.FIDESUI_SUCCESS, fontSize: 14 }} />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Request sent 2h ago to @DataSteward
                      </Text>
                    </Flex>
                    <Space wrap>
                      <Button icon={<MessageOutlined />} size="small">
                        Request information from team
                      </Button>
                      <Button type="default" onClick={() => setIsDrawerOpen(true)} size="small">
                        View AI Context
                      </Button>
                    </Space>
                  </Flex>
                </Card>

                <Form layout="vertical">
                  <Space direction="vertical" size="large" style={{ width: "100%" }}>
                    <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                      <Form.Item
                        label={
                          <Flex justify="space-between" align="center">
                            <Text strong>Stakeholder consultation</Text>
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                          </Flex>
                        }
                        name="stakeholderConsultation"
                        initialValue="We will consult with the Data Protection Officer (DPO) and the Information Security team before implementation. Customer feedback will be gathered through opt-in surveys during the initial rollout phase. We will also consult with our data processors (cloud infrastructure provider) to ensure compliance measures are in place. The Legal and Compliance teams will review the processing activities and provide guidance on lawful basis and data subject rights."
                      >
                        <Input.TextArea
                          rows={6}
                          placeholder="Consider how to consult with relevant stakeholders: describe when and how you will seek individuals' views – or justify why it's not appropriate to do so. Who else do you need to involve within your organisation? Do you need to ask your processors to assist? Do you plan to consult information security experts, or any other experts?"
                        />
                      </Form.Item>
                    </div>
                  </Space>
                </Form>
              </Space>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("4") ? (
                    <Flex justify="space-between" align="center" style={{ width: "100%", paddingRight: 140 }}>
                      <Text strong style={{ fontSize: 16 }}>Assess necessity and proportionality</Text>
                    </Flex>
                  ) : (
                    <Flex gap="large" align="flex-start" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 12, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            4. Assess necessity and proportionality
                          </Text>
                        </Flex>
                        <Flex gap="middle" align="center" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            Updated 5m ago by{" "}
                            <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 4 }}>AI</Tag>
                          </Text>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            <Text strong>Fields:</Text> <span style={{ marginLeft: 4 }}>4/4</span>
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    {sectionSummaries["4"]?.summary && !sectionSummaries["4"].isLoading && (
                      <Text className="summary-text">
                        <Text style={{ color: palette.FIDESUI_MINOS, fontWeight: 500 }}>Summary:</Text> {sectionSummaries["4"].summary}
                      </Text>
                    )}
                    {sectionSummaries["4"]?.summary && !sectionSummaries["4"].isLoading && (
                      <div className="risk-confidence-container">
                        <Flex gap="small" align="center" style={{ fontSize: 11, color: palette.FIDESUI_NEUTRAL_600, marginBottom: 4 }}>
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
                        <Flex gap="small" align="center" style={{ fontSize: 11, color: palette.FIDESUI_NEUTRAL_600 }}>
                          <div
                            style={{
                              width: 6,
                              height: 6,
                              borderRadius: "50%",
                              backgroundColor: palette.FIDESUI_SUCCESS,
                            }}
                          />
                          <Text style={{ fontSize: 11 }}>Confidence: High</Text>
                        </Flex>
                      </div>
                    )}
                    <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>Completed</Tag>
                  </div>
                </>
              }
              key="4"
            >
              <Space direction="vertical" size="large" style={{ width: "100%" }}>
                <Card
                  title="PROCESSING OVERVIEW"
                  style={{ marginBottom: 24 }}
                >
                  <Flex gap="large" wrap="wrap" style={{ marginBottom: 24 }}>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        SCOPE
                      </Text>
                      <Text strong style={{ fontSize: 16, display: "block", marginBottom: 8 }}>
                        2 Categories Identified
                      </Text>
                      <Space size="small" wrap>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>PII</Tag>
                        <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Behavioral Data</Tag>
                      </Space>
                    </Card>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        NATURE
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <ThunderboltOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>AI Analysis</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Automated Processing
                      </Text>
                    </Card>
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
                      <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                        CONTEXT
                      </Text>
                      <Flex align="center" gap="small" style={{ marginBottom: 8 }}>
                        <GlobalOutlined style={{ fontSize: 16, color: palette.FIDESUI_MINOS }} />
                        <Text strong style={{ fontSize: 16 }}>External</Text>
                      </Flex>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Customer Facing
                      </Text>
                    </Card>
                  </Flex>
                  <Flex justify="space-between" align="center" wrap="wrap" gap="small">
                    <Flex align="center" gap="small">
                      <CheckCircleOutlined style={{ color: palette.FIDESUI_SUCCESS, fontSize: 14 }} />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Request sent 2h ago to @DataSteward
                      </Text>
                    </Flex>
                    <Space wrap>
                      <Button icon={<MessageOutlined />} size="small">
                        Request information from team
                      </Button>
                      <Button type="default" onClick={() => setIsDrawerOpen(true)} size="small">
                        View AI Context
                      </Button>
                    </Space>
                  </Flex>
                </Card>

                <Form layout="vertical">
                  <Space direction="vertical" size="large" style={{ width: "100%" }}>
                    <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                      <Form.Item
                        label={
                          <Flex justify="space-between" align="center">
                            <Text strong>Compliance and proportionality measures</Text>
                            <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 8 }}>
                              AI
                            </Tag>
                          </Flex>
                        }
                        name="complianceMeasures"
                        initialValue="Lawful basis: Legitimate interests (Article 6(1)(f)) for personalized recommendations to enhance customer experience. The processing achieves the purpose of providing relevant product suggestions, and there is no less intrusive alternative that would achieve the same outcome. Function creep is prevented through strict access controls and regular audits. Data quality is ensured through validation at ingestion points and automated data cleansing processes. Data minimisation is achieved by only processing necessary data fields (purchase history, browsing behavior) and implementing data retention policies (24 months). Individuals are informed through privacy notices and cookie banners. Data subject rights are supported through a self-service portal for access, rectification, erasure, and objection requests. Processors are contractually bound through Data Processing Agreements (DPAs) with specific security and compliance requirements. International transfers are safeguarded through Standard Contractual Clauses (SCCs) and adequacy decisions where applicable."
                      >
                        <Input.TextArea
                          rows={8}
                          placeholder="What is your lawful basis for processing? Does the processing actually achieve your purpose? Is there another way to achieve the same outcome? How will you prevent function creep? How will you ensure data quality and data minimisation? What information will you give individuals? How will you help to support their rights? What measures do you take to ensure processors comply? How do you safeguard any international transfers?"
                        />
                      </Form.Item>
                    </div>
                  </Space>
                </Form>
              </Space>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("5") ? (
                    <Flex justify="space-between" align="center" style={{ width: "100%", paddingRight: 140 }}>
                      <Text strong style={{ fontSize: 16 }}>Identify and assess risks</Text>
                    </Flex>
                  ) : (
                    <Flex gap="large" align="flex-start" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 12, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            5. Identify and assess risks
                          </Text>
                        </Flex>
                        <Flex gap="middle" align="center" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            Updated 15m ago by{" "}
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 4 }}>JG</Tag>
                            <span style={{ marginLeft: 8, marginRight: 8 }}>+</span>
                            <Tag color={CUSTOM_TAG_COLOR.MINOS}>AI</Tag>
                          </Text>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            <Text strong>Fields:</Text> <span style={{ marginLeft: 4 }}>2/4</span>
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.WARNING}>In progress</Tag>
                  </div>
                </>
              }
              key="5"
            >
              <Form layout="vertical">
                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Risk assessment</Text>
                          <Flex gap="small">
                            <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                            <Tag color={CUSTOM_TAG_COLOR.MINOS} style={{ marginLeft: 4 }}>AI</Tag>
                          </Flex>
                        </Flex>
                      }
                      name="risks"
                    >
                      <Input.TextArea
                        rows={8}
                        placeholder="Describe source of risk and nature of potential impact on individuals. Include associated compliance and corporate risks as necessary. For each risk, assess the likelihood of harm (Remote, possible or probable) and severity of harm (Minimal, significant or severe) to determine overall risk (Low, medium or high)."
                      />
                    </Form.Item>
                  </div>
                </Space>
              </Form>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("6") ? (
                    <Flex justify="space-between" align="center" style={{ width: "100%", paddingRight: 140 }}>
                      <Text strong style={{ fontSize: 16 }}>6. Identify measures to reduce risk</Text>
                    </Flex>
                  ) : (
                    <Flex gap="large" align="flex-start" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 12, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            6. Identify measures to reduce risk
                          </Text>
                        </Flex>
                        <Flex gap="middle" align="center" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            <Text strong>Fields:</Text> <span style={{ marginLeft: 4 }}>0/3</span>
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Incomplete</Tag>
                  </div>
                </>
              }
              key="6"
            >
              <Form layout="vertical">
                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Measures to reduce or eliminate risk</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="measures"
                    >
                      <Input.TextArea
                        rows={8}
                        placeholder="Identify additional measures you could take to reduce or eliminate risks identified as medium or high risk in step 5. For each risk, describe: Options to reduce or eliminate risk, Effect on risk (Eliminated, reduced, accepted), Residual risk (Low, medium, high), and whether the measure is approved (Yes/no)."
                      />
                    </Form.Item>
                  </div>
                </Space>
              </Form>
            </Panel>

            <Panel
              header={
                <>
                  {expandedKeys.includes("7") ? (
                    <Flex justify="space-between" align="center" style={{ width: "100%", paddingRight: 140 }}>
                      <Text strong style={{ fontSize: 16 }}>7. Sign off and record outcomes</Text>
                    </Flex>
                  ) : (
                    <Flex gap="large" align="flex-start" style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Flex justify="space-between" align="center" style={{ marginBottom: 12, alignItems: "center" }}>
                          <Text strong style={{ fontSize: 16 }}>
                            7. Sign off and record outcomes
                          </Text>
                        </Flex>
                        <Flex gap="middle" align="center" wrap="wrap" style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 11, lineHeight: "16px", display: "inline-flex", alignItems: "center" }}>
                            <Text strong>Fields:</Text> <span style={{ marginLeft: 4 }}>0/6</span>
                          </Text>
                        </Flex>
                      </div>
                    </Flex>
                  )}
                  <div className="status-tag-container">
                    <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Incomplete</Tag>
                  </div>
                </>
              }
              key="7"
            >
              <Form layout="vertical">
                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Measures approved by</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="measuresApprovedBy"
                    >
                      <Input placeholder="Name/date - Integrate actions back into project plan, with date and responsibility for completion" />
                    </Form.Item>
                  </div>

                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Residual risks approved by</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="residualRisksApprovedBy"
                    >
                      <Input placeholder="Name/date - If accepting any residual high risk, consult the ICO before going ahead" />
                    </Form.Item>
                  </div>

                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>DPO advice provided</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="dpoAdviceProvided"
                    >
                      <Input placeholder="Name/date - DPO should advise on compliance, step 6 measures and whether processing can proceed" />
                    </Form.Item>
                  </div>

                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Summary of DPO advice</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="dpoAdviceSummary"
                    >
                      <Input.TextArea rows={3} />
                    </Form.Item>
                  </div>

                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>DPO advice accepted or overruled by</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="dpoAdviceAccepted"
                    >
                      <Input placeholder="Name/date - If overruled, you must explain your reasons" />
                    </Form.Item>
                  </div>

                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>Consultation responses reviewed by</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="consultationReviewedBy"
                    >
                      <Input placeholder="Name/date - If your decision departs from individuals' views, you must explain your reasons" />
                    </Form.Item>
                  </div>

                  <div style={{ backgroundColor: palette.FIDESUI_BG_CORINTH, padding: 16, borderRadius: 8 }}>
                    <Form.Item
                      label={
                        <Flex justify="space-between" align="center">
                          <Text strong>This DPIA will be kept under review by</Text>
                          <Tag color={CUSTOM_TAG_COLOR.MARBLE} style={{ marginLeft: 8 }}>JG</Tag>
                        </Flex>
                      }
                      name="dpiaReviewBy"
                    >
                      <Input placeholder="Name/date - The DPO should also review ongoing compliance with DPIA" />
                    </Form.Item>
                  </div>
                </Space>
              </Form>
            </Panel>
          </Collapse>
          </Form>
        </Space>
      </div>

      <Drawer
        title="AI Context - Slack Conversation"
        placement="right"
        onClose={() => setIsDrawerOpen(false)}
        open={isDrawerOpen}
        width={480}
        styles={{
          body: {
            padding: 0,
            display: "flex",
            flexDirection: "column",
            height: "100%",
          },
        }}
      >
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: 16,
            backgroundColor: "#fafafa",
          }}
        >
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: "flex",
                gap: 12,
                justifyContent: msg.sender === "astralis" ? "flex-start" : "flex-end",
                flexDirection: msg.sender === "astralis" ? "row" : "row-reverse",
              }}
            >
              <Avatar
                style={{
                  backgroundColor: msg.sender === "astralis" ? palette.FIDESUI_MINOS : palette.FIDESUI_MARBLE,
                  flexShrink: 0,
                }}
                size={32}
              >
                {msg.sender === "astralis" ? "A" : "JG"}
              </Avatar>
              <div
                style={{
                  maxWidth: "75%",
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    justifyContent: msg.sender === "astralis" ? "flex-start" : "flex-end",
                  }}
                >
                  <Text strong style={{ fontSize: 13 }}>
                    {msg.senderName}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {msg.timestamp}
                  </Text>
                </div>
                <div
                  style={{
                    padding: "12px 16px",
                    borderRadius: 12,
                    backgroundColor: msg.sender === "astralis" ? "white" : palette.FIDESUI_MINOS,
                    color: msg.sender === "astralis" ? "#1a1a1a" : "white",
                    boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
                    wordWrap: "break-word",
                  }}
                >
                  <Text
                    style={{
                      fontSize: 14,
                      lineHeight: "20px",
                      color: msg.sender === "astralis" ? "#1a1a1a" : "white",
                      margin: 0,
                    }}
                  >
                    {msg.message}
                  </Text>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Drawer>

      <Modal
        title={
          <Flex align="center" gap="small">
            <CheckCircleOutlined style={{ color: palette.FIDESUI_SUCCESS, fontSize: 20 }} />
            <span>Assessment Generated</span>
          </Flex>
        }
        open={isReportModalOpen}
        onCancel={() => setIsReportModalOpen(false)}
        footer={null}
        width={600}
      >
        <Space direction="vertical" size="large" style={{ width: "100%", marginTop: 8 }}>
          <div style={{ paddingBottom: 24, borderBottom: `1px solid ${palette.FIDESUI_NEUTRAL_100}` }}>
            <Title level={5} style={{ marginBottom: 16, textTransform: "uppercase", fontSize: 11, letterSpacing: 1, fontWeight: 600, color: palette.FIDESUI_NEUTRAL_700 }}>
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
                  <Text strong style={{ marginRight: 8 }}>Risk Level:</Text>Medium
                </Text>
              </Flex>
              <Flex align="center" gap="small">
                <SafetyOutlined style={{ color: palette.FIDESUI_MINOS, fontSize: 16 }} />
                <Text style={{ fontSize: 14 }}>
                  <Text strong style={{ marginRight: 8 }}>Compliance:</Text>GDPR
                </Text>
              </Flex>
              <Flex align="center" gap="small">
                <ThunderboltOutlined style={{ color: palette.FIDESUI_MINOS, fontSize: 16 }} />
                <Text style={{ fontSize: 14 }}>
                  <Text strong style={{ marginRight: 8 }}>Confidence:</Text>94% AI
                </Text>
              </Flex>
            </Space>
          </div>

          <div style={{ paddingBottom: 24, borderBottom: `1px solid ${palette.FIDESUI_NEUTRAL_100}` }}>
            <Title level={5} style={{ marginBottom: 16, textTransform: "uppercase", fontSize: 11, letterSpacing: 1, fontWeight: 600, color: palette.FIDESUI_NEUTRAL_700 }}>
              Document Details
            </Title>
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Flex justify="space-between" align="center">
                <Text type="secondary" style={{ fontSize: 14 }}>Project:</Text>
                <Text strong style={{ fontSize: 14 }}>Customer Insight AI</Text>
              </Flex>
              <Flex justify="space-between" align="center">
                <Text type="secondary" style={{ fontSize: 14 }}>Data Types:</Text>
                <Space size="small">
                  <Tag color={CUSTOM_TAG_COLOR.MARBLE}>PII</Tag>
                  <Tag color={CUSTOM_TAG_COLOR.MARBLE}>Behavioral</Tag>
                </Space>
              </Flex>
              <Flex justify="space-between" align="center">
                <Text type="secondary" style={{ fontSize: 14 }}>Retention:</Text>
                <Text strong style={{ fontSize: 14 }}>24 Months</Text>
              </Flex>
            </Space>
          </div>

          <div style={{ paddingBottom: 24 }}>
            <Title level={5} style={{ marginBottom: 16, textTransform: "uppercase", fontSize: 11, letterSpacing: 1, fontWeight: 600, color: palette.FIDESUI_NEUTRAL_700 }}>
              Responsible Parties
            </Title>
            <Flex align="center" gap="middle">
              <Avatar size={40} style={{ backgroundColor: palette.FIDESUI_MINOS }}>AM</Avatar>
              <Flex vertical gap={4} style={{ flex: 1 }}>
                <Text strong style={{ fontSize: 15 }}>Alex Morgan</Text>
                <Flex align="center" gap="small">
                  <Text type="secondary" style={{ fontSize: 13 }}>
                    Privacy Officer • Primary Owner
                  </Text>
                  <EditOutlined style={{ fontSize: 13, color: palette.FIDESUI_NEUTRAL_500, cursor: "pointer" }} />
                </Flex>
              </Flex>
            </Flex>
          </div>

          <Flex gap="small" style={{ marginTop: 8, paddingTop: 24, borderTop: `1px solid ${palette.FIDESUI_NEUTRAL_100}`, justifyContent: "flex-end" }}>
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
        <Space direction="vertical" size="large" style={{ width: "100%", marginTop: 16 }}>
          <Text type="secondary" style={{ display: "block", fontSize: 13 }}>
            Select the regions where this assessment applies. This allows you to scope a template (e.g., GDPR) to specific jurisdictions.
          </Text>

          <div>
            <Text strong style={{ display: "block", marginBottom: 12, fontSize: 13 }}>
              Selected Regions
            </Text>
            {selectedRegions.length > 0 ? (
              <Flex gap="small" wrap="wrap" style={{ marginBottom: 16 }}>
                {selectedRegions.map((region) => (
                  <Tag
                    key={region}
                    closable
                    onClose={() => setSelectedRegions(selectedRegions.filter((r) => r !== region))}
                    style={{ margin: 0, fontSize: 12 }}
                  >
                    {formatRegionDisplay(region)}
                  </Tag>
                ))}
              </Flex>
            ) : (
              <Text type="secondary" style={{ display: "block", marginBottom: 16, fontSize: 12, fontStyle: "italic" }}>
                No regions selected. The assessment will apply to all regions by default.
              </Text>
            )}
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 12, fontSize: 13 }}>
              Add Regions
            </Text>
            <LocationSelect
              mode="multiple"
              value={selectedRegions}
              onChange={(value) => setSelectedRegions(value || [])}
              placeholder="Search and select regions..."
              style={{ width: "100%" }}
              allowClear
              showSearch
              includeCountryOnlyOptions={true}
            />
          </div>
        </Space>
      </Modal>
    </Layout>
  );
};

export default PrivacyAssessmentDetailPage;
