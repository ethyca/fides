import {
  CheckCircleOutlined,
  DownloadOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import {
  Button,
  Collapse,
  CUSTOM_TAG_COLOR,
  Drawer,
  Flex,
  Icons,
  Input,
  List,
  Modal,
  Result,
  Space,
  Spin,
  Tag,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentQuestion,
  EvidenceItem,
  ManualEntryEvidenceItem,
  QuestionGroup,
  SlackCommunicationEvidenceItem,
  SystemEvidenceItem,
  useCreateQuestionnaireMutation,
  useCreateQuestionnaireReminderMutation,
  useDeletePrivacyAssessmentMutation,
  useGetPrivacyAssessmentQuery,
  useUpdateAssessmentAnswerMutation,
} from "~/features/privacy-assessments";

import { EditableTextBlock } from "./components/EditableTextBlock";
import { SlackIcon } from "./components/SlackIcon";

const { Title, Text } = Typography;

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

// Helper function to render text with reference badges
const renderTextWithReferences = (
  text: string,
  onReferenceClick?: (label: string) => void
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
      </span>
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

// Calculate time since a date
const getTimeSince = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) {
    return `${diffDays}d ago`;
  }
  if (diffHours > 0) {
    return `${diffHours}h ago`;
  }
  if (diffMins > 0) {
    return `${diffMins}m ago`;
  }
  return "Just now";
};

const PrivacyAssessmentDetailPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const message = useMessage();
  const { id } = router.query;
  const assessmentId = id as string;

  // UI state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [focusedGroupId, setFocusedGroupId] = useState<string | null>(null);
  const [highlightedCitationNumber, setHighlightedCitationNumber] = useState<
    string | null
  >(null);
  const [evidenceSearchQuery, setEvidenceSearchQuery] = useState("");

  // Local state for optimistic answer updates
  const [localAnswers, setLocalAnswers] = useState<Record<string, string>>({});

  // API queries and mutations
  const {
    data: assessment,
    isLoading,
    isError,
    refetch,
  } = useGetPrivacyAssessmentQuery(assessmentId, {
    skip: !assessmentId,
  });

  const [updateAnswer, { isLoading: isSavingAnswer }] =
    useUpdateAssessmentAnswerMutation();
  const [deleteAssessment, { isLoading: isDeleting }] =
    useDeletePrivacyAssessmentMutation();
  const [createQuestionnaire, { isLoading: isSendingQuestionnaire }] =
    useCreateQuestionnaireMutation();
  const [createReminder, { isLoading: isSendingReminder }] =
    useCreateQuestionnaireReminderMutation();

  // Get question groups from assessment
  const questionGroups = assessment?.question_groups ?? [];

  // Flatten all questions for progress calculations
  const allQuestions = useMemo(
    () => questionGroups.flatMap((g) => g.questions),
    [questionGroups]
  );

  // Get current answer value (local override or from API)
  const getAnswerValue = useCallback(
    (questionId: string, apiAnswer: string): string =>
      localAnswers[questionId] ?? apiAnswer,
    [localAnswers]
  );

  // Calculate progress for slack questions
  const slackQuestions = allQuestions.filter(
    (q) => q.answer_source === "slack" || q.answer_status === "needs_input"
  );
  const answeredSlackQuestions = slackQuestions.filter((q) => {
    const answer = getAnswerValue(q.question_id, q.answer_text);
    return answer.trim().length > 0;
  });
  const slackProgress = `${answeredSlackQuestions.length}/${slackQuestions.length}`;

  // Assessment is complete when all questions have answers
  const isComplete = useMemo(() => {
    return allQuestions.every((q) => {
      const answer = getAnswerValue(q.question_id, q.answer_text);
      return answer.trim().length > 0;
    });
  }, [allQuestions, getAnswerValue]);

  // Questionnaire status
  const questionnaireSentAt = assessment?.questionnaire?.sent_at
    ? new Date(assessment.questionnaire.sent_at)
    : null;

  // Time since questionnaire sent (updates on component render)
  const timeSinceSent = questionnaireSentAt
    ? getTimeSince(questionnaireSentAt.toISOString())
    : "";

  // Handle answer change (optimistic update for UI)
  const handleAnswerChange = useCallback(
    (questionId: string, newAnswer: string) => {
      // Optimistic update
      setLocalAnswers((prev) => ({ ...prev, [questionId]: newAnswer }));
    },
    []
  );

  // Save answer to API when user clicks Save
  const handleAnswerSave = useCallback(
    async (questionId: string, newAnswer: string) => {
      try {
        await updateAnswer({
          id: assessmentId,
          questionId,
          body: { answer_text: newAnswer },
        }).unwrap();

        // Clear local override after successful save
        setLocalAnswers((prev) => {
          const updated = { ...prev };
          delete updated[questionId];
          return updated;
        });
      } catch (error) {
        console.error("Failed to save answer:", error);
        message.error("Failed to save answer. Please try again.");
      }
    },
    [assessmentId, message, updateAnswer]
  );

  const handleComment = (selection: {
    text: string;
    start: number;
    end: number;
  }) => {
    message.success(
      `Comment added on "${selection.text.substring(0, 30)}${selection.text.length > 30 ? "..." : ""}"`
    );
  };

  const handleRequestInput = async () => {
    try {
      await createQuestionnaire({
        id: assessmentId,
        body: { channel: "#privacy-team" },
      }).unwrap();

      message.success("Questionnaire sent to #privacy-team on Slack.");
      refetch();
    } catch (error) {
      console.error("Failed to send questionnaire:", error);
      message.error("Failed to send questionnaire. Please try again.");
    }
  };

  const handleSendReminder = async () => {
    try {
      await createReminder({
        id: assessmentId,
      }).unwrap();

      message.success("Reminder sent to #privacy-team.");
      refetch();
    } catch (error) {
      console.error("Failed to send reminder:", error);
      message.error("Failed to send reminder. Please try again.");
    }
  };

  const handleViewEvidence = (groupId: string, citationNumber?: string) => {
    setFocusedGroupId(groupId);
    setHighlightedCitationNumber(citationNumber ?? null);
    setIsDrawerOpen(true);
  };

  const handleDelete = async () => {
    try {
      await deleteAssessment(assessmentId).unwrap();
      message.success("Assessment deleted.");
      setIsDeleteModalOpen(false);
      router.push(PRIVACY_ASSESSMENTS_ROUTE);
    } catch (error) {
      console.error("Failed to delete assessment:", error);
      message.error("Failed to delete assessment. Please try again.");
    }
  };

  // Get all evidence items from all questions in a group (deduplicated by ID)
  const getGroupEvidence = useCallback(
    (groupId: string): EvidenceItem[] => {
      const group = questionGroups.find((g) => g.id === groupId);
      if (!group) return [];

      // Flatten all evidence and deduplicate by ID
      const allEvidence = group.questions.flatMap((q) => q.evidence);
      const uniqueEvidence = new Map<string, EvidenceItem>();
      allEvidence.forEach((item) => {
        if (!uniqueEvidence.has(item.id)) {
          uniqueEvidence.set(item.id, item);
        }
      });

      return Array.from(uniqueEvidence.values());
    },
    [questionGroups]
  );

  // Filter evidence based on search query
  const getFilteredEvidence = useCallback(
    (groupId: string): EvidenceItem[] => {
      const evidence = getGroupEvidence(groupId);

      if (!evidenceSearchQuery) return evidence;

      const query = evidenceSearchQuery.toLowerCase();
      return evidence.filter((item) => {
        if (item.type === "system") {
          const sysItem = item as SystemEvidenceItem;
          return (
            sysItem.source.source_name.toLowerCase().includes(query) ||
            sysItem.value_display.toLowerCase().includes(query)
          );
        }
        if (item.type === "manual_entry") {
          const manualItem = item as ManualEntryEvidenceItem;
          return (
            manualItem.author.user_name.toLowerCase().includes(query) ||
            manualItem.entry.new_value.toLowerCase().includes(query)
          );
        }
        if (item.type === "slack_communication") {
          const slackItem = item as SlackCommunicationEvidenceItem;
          return (
            slackItem.channel.channel_name.toLowerCase().includes(query) ||
            (slackItem.summary?.toLowerCase().includes(query) ?? false)
          );
        }
        return false;
      });
    },
    [evidenceSearchQuery, getGroupEvidence]
  );

  // Feature flag check
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

  // Loading state
  if (isLoading) {
    return (
      <Layout title="Privacy Assessment">
        <PageHeader heading="Privacy assessments" isSticky />
        <Flex align="center" justify="center" style={{ padding: "80px 40px" }}>
          <Spin size="large" />
        </Flex>
      </Layout>
    );
  }

  // Error state
  if (isError || !assessment) {
    return (
      <Layout title="Privacy Assessment">
        <PageHeader heading="Privacy assessments" isSticky />
        <Result
          status="error"
          title="Failed to load assessment"
          subTitle="There was an error loading this privacy assessment. Please try again."
          extra={
            <Space>
              <Button onClick={() => router.push(PRIVACY_ASSESSMENTS_ROUTE)}>
                Back to list
              </Button>
              <Button type="primary" onClick={() => refetch()}>
                Retry
              </Button>
            </Space>
          }
        />
      </Layout>
    );
  }

  const assessmentName = assessment.name;

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
                loading={isDeleting}
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
            <Text
              type="secondary"
              style={{ display: "block", marginBottom: 8, fontSize: 12 }}
            >
              System: {assessment.system_name}
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
              {assessment.data_categories.map((category, idx) => (
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
                  {idx < assessment.data_categories.length - 1 && " "}
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
                {assessment.data_use_name}
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
                    loading={isSendingQuestionnaire}
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
                            answeredSlackQuestions.length ===
                            slackQuestions.length
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
                      loading={isSendingReminder}
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
            items={questionGroups.map((group) => {
              const answeredCount = group.questions.filter((q) => {
                const answer = getAnswerValue(q.question_id, q.answer_text);
                return answer.trim().length > 0;
              }).length;
              const totalCount = group.questions.length;
              const isGroupCompleted = answeredCount === totalCount;
              const isExpanded = expandedKeys.includes(group.id);

              return {
                key: group.id,
                label: (
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
                            {group.last_updated_at
                              ? `Updated ${getTimeSince(group.last_updated_at)}`
                              : "Not updated yet"}
                            {group.last_updated_by && (
                              <>
                                {" by "}
                                <Tag
                                  color={CUSTOM_TAG_COLOR.DEFAULT}
                                  style={{ marginLeft: 4 }}
                                >
                                  {group.last_updated_by
                                    .split(" ")
                                    .map((n) => n[0])
                                    .join("")}
                                </Tag>
                              </>
                            )}
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
                                backgroundColor:
                                  group.risk_level === "high"
                                    ? palette.FIDESUI_ERROR
                                    : group.risk_level === "medium"
                                      ? palette.FIDESUI_WARNING
                                      : palette.FIDESUI_SUCCESS,
                              }}
                            />
                            <Text style={{ fontSize: 11 }}>
                              Risk:{" "}
                              {group.risk_level
                                ? group.risk_level.charAt(0).toUpperCase() +
                                  group.risk_level.slice(1)
                                : "Low"}
                            </Text>
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
                ),
                children: (
                  <Space
                    direction="vertical"
                    size="middle"
                    style={{ width: "100%" }}
                  >
                    {group.questions.map((q) => {
                      const currentAnswer = getAnswerValue(
                        q.question_id,
                        q.answer_text
                      );
                      const sourceLabel =
                        q.answer_source === "system"
                          ? "System derived"
                          : q.answer_source === "ai_analysis"
                            ? "AI derived"
                            : "Team input";
                      const sourceColor =
                        q.answer_source === "system" ||
                        q.answer_source === "ai_analysis"
                          ? CUSTOM_TAG_COLOR.SUCCESS
                          : CUSTOM_TAG_COLOR.DEFAULT;

                      return (
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
                              {q.id}. {q.question_text}
                            </Text>
                            {q.answer_status === "partial" ? (
                              <Tooltip
                                title={
                                  q.missing_data && q.missing_data.length > 0
                                    ? `This answer can be automatically derived if you populate: ${q.missing_data.join(", ")}`
                                    : "This answer can be derived from Fides data if the relevant field is populated"
                                }
                              >
                                <Tag color={CUSTOM_TAG_COLOR.WARNING}>
                                  System derivable
                                </Tag>
                              </Tooltip>
                            ) : (
                              <Tag color={sourceColor}>{sourceLabel}</Tag>
                            )}
                          </Flex>
                          <EditableTextBlock
                            value={currentAnswer}
                            onChange={(newValue) =>
                              handleAnswerChange(q.question_id, newValue)
                            }
                            onSave={(newValue) =>
                              handleAnswerSave(q.question_id, newValue)
                            }
                            placeholder="Enter your answer..."
                            onComment={handleComment}
                            onRequestInput={
                              q.answer_source === "slack" ||
                              q.answer_status === "needs_input"
                                ? handleRequestInput
                                : undefined
                            }
                            renderContent={(text) =>
                              renderTextWithReferences(text, (label) =>
                                handleViewEvidence(group.id, label)
                              )
                            }
                          />
                        </div>
                      );
                    })}
                  </Space>
                ),
              };
            })}
          />
        </Space>
      </div>

      <Modal
        title="Delete assessment"
        open={isDeleteModalOpen}
        onCancel={() => setIsDeleteModalOpen(false)}
        onOk={handleDelete}
        okText="Delete"
        okButtonProps={{ danger: true, loading: isDeleting }}
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
          setHighlightedCitationNumber(null);
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
        afterOpenChange={(open) => {
          if (open && highlightedCitationNumber) {
            // Scroll to the highlighted evidence item after drawer opens
            setTimeout(() => {
              const element = document.querySelector(
                `[data-citation-number="${highlightedCitationNumber}"]`
              );
              if (element) {
                element.scrollIntoView({ behavior: "smooth", block: "start" });
                // Remove highlight after a delay (but keep content visible)
                setTimeout(() => {
                  setHighlightedCitationNumber(null);
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
          <Space direction="vertical" size="large" style={{ width: "100%" }}>
            {focusedGroupId && (
              <EvidenceSection
                groupId={focusedGroupId}
                group={questionGroups.find((g) => g.id === focusedGroupId)}
                evidence={getFilteredEvidence(focusedGroupId)}
                formatTimestamp={formatTimestamp}
                highlightedCitationNumber={highlightedCitationNumber}
              />
            )}
          </Space>
        </div>
      </Drawer>
    </Layout>
  );
};

// Evidence section component
const EvidenceSection = ({
  groupId,
  group,
  evidence,
  formatTimestamp,
  highlightedCitationNumber,
}: {
  groupId: string;
  group: QuestionGroup | undefined;
  evidence: EvidenceItem[];
  formatTimestamp: (ts: string) => string;
  highlightedCitationNumber?: string | null;
}) => {
  if (!group) return null;

  const systemEvidence = evidence.filter(
    (e) => e.type === "system"
  ) as SystemEvidenceItem[];
  const manualEvidence = evidence.filter(
    (e) => e.type === "manual_entry"
  ) as ManualEntryEvidenceItem[];
  const slackEvidence = evidence.filter(
    (e) => e.type === "slack_communication"
  ) as SlackCommunicationEvidenceItem[];

  // Helper to get highlight styles for a specific citation number
  const getHighlightStyles = (citationNumber: number | null | undefined) => {
    if (
      citationNumber != null &&
      String(citationNumber) === highlightedCitationNumber
    ) {
      return {
        border: "1px solid #4A6CF7",
        boxShadow: "0 0 0 2px rgba(74, 108, 247, 0.12)",
      };
    }
    return {};
  };

  return (
    <div data-group-id={groupId}>
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
          <Text
            strong
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "#1A1F36",
              display: "block",
              marginBottom: 12,
            }}
          >
            System-derived data
          </Text>
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
          <Space direction="vertical" size="small" style={{ width: "100%" }}>
            {systemEvidence.map((item) => (
              <div
                key={item.id}
                data-citation-number={item.citation_number}
                style={{
                  padding: "12px 16px",
                  backgroundColor: "#FFFFFF",
                  borderRadius: 8,
                  border: "1px solid #E8EBED",
                  transition: "all 0.3s ease",
                  ...getHighlightStyles(item.citation_number),
                }}
              >
                <Flex
                  justify="space-between"
                  align="flex-start"
                  style={{ marginBottom: 8 }}
                >
                  <Text strong style={{ fontSize: 13, color: "#1A1F36" }}>
                    {item.source.source_name}
                  </Text>
                  {item.citation_number && (
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
                      {item.citation_number}
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
                  <Text style={{ color: "#6B7280", marginRight: 4 }}>
                    {item.field.field_label}:
                  </Text>
                  {item.value_display}
                </Text>
                <Text
                  type="secondary"
                  style={{ fontSize: 12, display: "block" }}
                >
                  Last updated: {formatTimestamp(item.created_at)}
                </Text>
              </div>
            ))}
          </Space>
        </div>
      )}

      {/* Manual Entry Section */}
      {manualEvidence.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <Text
            strong
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "#1A1F36",
              display: "block",
              marginBottom: 12,
            }}
          >
            Manual entries
          </Text>
          <Space direction="vertical" size="small" style={{ width: "100%" }}>
            {manualEvidence.map((item) => (
              <div
                key={item.id}
                data-citation-number={item.citation_number}
                style={{
                  padding: "12px 16px",
                  backgroundColor: "#FFFFFF",
                  borderRadius: 8,
                  border: "1px solid #E8EBED",
                  transition: "all 0.3s ease",
                  ...getHighlightStyles(item.citation_number),
                }}
              >
                <Flex
                  justify="space-between"
                  align="flex-start"
                  style={{ marginBottom: 8 }}
                >
                  <Text strong style={{ fontSize: 13, color: "#1A1F36" }}>
                    Manual entry
                  </Text>
                  {item.citation_number && (
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
                      {item.citation_number}
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
                  {item.entry.new_value}
                </Text>
                <Text
                  type="secondary"
                  style={{ fontSize: 12, display: "block" }}
                >
                  {item.author.user_name}
                  {item.author.role && `, ${item.author.role}`} •{" "}
                  {formatTimestamp(item.created_at)}
                </Text>
              </div>
            ))}
          </Space>
        </div>
      )}

      {/* Slack Communication Section */}
      {slackEvidence.length > 0 && (
        <div>
          <Text
            strong
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "#1A1F36",
              display: "block",
              marginBottom: 12,
            }}
          >
            Stakeholder communications
          </Text>
          <Space direction="vertical" size="small" style={{ width: "100%" }}>
            {slackEvidence.map((item) => (
              <div
                key={item.id}
                data-citation-number={item.citation_number}
                style={{
                  padding: "8px 16px 12px 16px",
                  backgroundColor: "#FFFFFF",
                  borderRadius: 8,
                  border: "1px solid #E8EBED",
                  transition: "all 0.3s ease",
                  ...getHighlightStyles(item.citation_number),
                }}
              >
                <Flex
                  justify="space-between"
                  align="flex-start"
                  style={{ marginBottom: 8 }}
                >
                  <Text strong style={{ fontSize: 13, color: "#1A1F36" }}>
                    Slack thread
                  </Text>
                  {item.citation_number && (
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
                      {item.citation_number}
                    </span>
                  )}
                </Flex>
                {item.summary && (
                  <Text
                    style={{
                      fontSize: 13,
                      color: "#4B5563",
                      display: "block",
                      lineHeight: 1.5,
                      marginBottom: 8,
                    }}
                  >
                    {item.summary}
                  </Text>
                )}
                <Text
                  type="secondary"
                  style={{ fontSize: 12, display: "block", marginBottom: 4 }}
                >
                  {item.channel.channel_name} • {item.thread.message_count}{" "}
                  messages • {formatTimestamp(item.created_at)}
                </Text>
                {item.messages && item.messages.length > 0 && (
                  <Collapse
                    ghost
                    style={{ marginTop: 8 }}
                    items={[
                      {
                        key: "thread",
                        label: `View ${item.messages.length} message${item.messages.length === 1 ? "" : "s"}`,
                        children: (
                          <List
                            size="small"
                            style={{ marginTop: -8 }}
                            dataSource={item.messages}
                            renderItem={(msg, index) => (
                              <List.Item
                                style={{
                                  padding: "8px 0",
                                  borderBottom:
                                    index === item.messages.length - 1
                                      ? "none"
                                      : `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
                                }}
                              >
                                <List.Item.Meta
                                  title={
                                    <Flex align="center" gap="small">
                                      <Text strong style={{ fontSize: 12 }}>
                                        {msg.sender.display_name}
                                      </Text>
                                      <Text
                                        type="secondary"
                                        style={{ fontSize: 11 }}
                                      >
                                        {new Date(msg.timestamp).toLocaleString(
                                          "en-US",
                                          {
                                            month: "short",
                                            day: "numeric",
                                            hour: "2-digit",
                                            minute: "2-digit",
                                          }
                                        )}
                                      </Text>
                                    </Flex>
                                  }
                                  description={
                                    <Text style={{ fontSize: 13, marginTop: 4 }}>
                                      {msg.content.text}
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
            ))}
          </Space>
        </div>
      )}

      {/* No evidence message */}
      {evidence.length === 0 && (
        <Text type="secondary" style={{ fontSize: 13 }}>
          No evidence collected yet for this section.
        </Text>
      )}
    </div>
  );
};

export default PrivacyAssessmentDetailPage;
