import {
  Button,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  Result,
  Space,
  Spin,
  Tag,
  Text,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useCallback, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  buildQuestionGroupPanelItem,
  DeleteAssessmentModal,
  EvidenceDrawer,
  QuestionGroupCollapse,
  QuestionnaireStatusBar,
  SlackIcon,
  useCreateQuestionnaireMutation,
  useCreateQuestionnaireReminderMutation,
  useDeletePrivacyAssessmentMutation,
  useGetPrivacyAssessmentQuery,
  useUpdateAssessmentAnswerMutation,
} from "~/features/privacy-assessments";
import {
  filterEvidence,
  getGroupEvidence,
  getSlackQuestions,
  getTimeSince,
  isAssessmentComplete,
  truncate,
} from "~/features/privacy-assessments/utils";
import { RTKErrorResult } from "~/types/errors/api";

const { Title } = Typography;

const PrivacyAssessmentDetailPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const message = useMessage();
  const { id } = router.query;
  const assessmentId = id as string;

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [focusedGroupId, setFocusedGroupId] = useState<string | null>(null);
  const [evidenceSearchQuery, setEvidenceSearchQuery] = useState("");
  const [localAnswers, setLocalAnswers] = useState<Record<string, string>>({});

  const {
    data: assessment,
    isLoading,
    isError,
    refetch,
  } = useGetPrivacyAssessmentQuery(assessmentId, { skip: !assessmentId });

  const [updateAnswer] = useUpdateAssessmentAnswerMutation();
  const [deleteAssessment, { isLoading: isDeleting }] =
    useDeletePrivacyAssessmentMutation();
  const [createQuestionnaire, { isLoading: isSendingQuestionnaire }] =
    useCreateQuestionnaireMutation();
  const [createReminder, { isLoading: isSendingReminder }] =
    useCreateQuestionnaireReminderMutation();

  const questionGroups = useMemo(
    () => assessment?.question_groups ?? [],
    [assessment?.question_groups],
  );

  const allQuestions = useMemo(
    () => questionGroups.flatMap((g) => g.questions),
    [questionGroups],
  );

  const getAnswerValue = useCallback(
    (questionId: string, apiAnswer: string): string =>
      localAnswers[questionId] ?? apiAnswer,
    [localAnswers],
  );

  const { slackQuestions, answeredSlackQuestions } = useMemo(
    () => getSlackQuestions(allQuestions, getAnswerValue),
    [allQuestions, getAnswerValue],
  );

  const isComplete = useMemo(
    () => isAssessmentComplete(allQuestions, getAnswerValue),
    [allQuestions, getAnswerValue],
  );

  const { questionnaireSentAt, timeSinceSent } = useMemo(() => {
    const sentAt = assessment?.questionnaire?.sent_at
      ? new Date(assessment.questionnaire.sent_at)
      : null;
    return {
      questionnaireSentAt: sentAt,
      timeSinceSent: sentAt ? getTimeSince(sentAt.toISOString()) : "",
    };
  }, [assessment?.questionnaire?.sent_at]);

  const handleAnswerChange = useCallback(
    (questionId: string, newAnswer: string) => {
      setLocalAnswers((prev) => ({ ...prev, [questionId]: newAnswer }));
    },
    [],
  );

  const handleAnswerSave = useCallback(
    async (questionId: string, newAnswer: string) => {
      try {
        await updateAnswer({
          id: assessmentId,
          questionId,
          body: { answer_text: newAnswer },
        }).unwrap();
        setLocalAnswers((prev) => {
          const updated = { ...prev };
          delete updated[questionId];
          return updated;
        });
      } catch (error) {
        message.error(
          getErrorMessage(
            error as RTKErrorResult["error"],
            "Failed to save answer. Please try again.",
          ),
        );
      }
    },
    [assessmentId, message, updateAnswer],
  );

  const handleComment = useCallback(
    (selection: { text: string; start: number; end: number }) => {
      message.success(`Comment added on "${truncate(selection.text, 30)}"`);
    },
    [message],
  );

  const handleRequestInput = useCallback(async () => {
    try {
      await createQuestionnaire({
        id: assessmentId,
        body: { channel: "#privacy-team" },
      }).unwrap();
      message.success("Questionnaire sent to #privacy-team on Slack.");
      refetch();
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to send questionnaire. Please try again.",
        ),
      );
    }
  }, [assessmentId, createQuestionnaire, message, refetch]);

  const handleSendReminder = async () => {
    try {
      await createReminder({ id: assessmentId }).unwrap();
      message.success("Reminder sent to #privacy-team.");
      refetch();
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to send reminder. Please try again.",
        ),
      );
    }
  };

  const handleViewEvidence = useCallback((groupId: string) => {
    setFocusedGroupId(groupId);
    setIsDrawerOpen(true);
  }, []);

  const handleDelete = async () => {
    try {
      await deleteAssessment(assessmentId).unwrap();
      message.success("Assessment deleted.");
      setIsDeleteModalOpen(false);
      router.push(PRIVACY_ASSESSMENTS_ROUTE);
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to delete assessment. Please try again.",
        ),
      );
    }
  };

  const filteredEvidence = useMemo(() => {
    if (!focusedGroupId) {
      return [];
    }
    return filterEvidence(
      getGroupEvidence(questionGroups, focusedGroupId),
      evidenceSearchQuery,
    );
  }, [focusedGroupId, evidenceSearchQuery, questionGroups]);

  const collapseItems = useMemo(
    () =>
      questionGroups.map((group) =>
        buildQuestionGroupPanelItem({
          group,
          isExpanded: expandedKeys.includes(group.id),
          getAnswerValue,
          onAnswerChange: handleAnswerChange,
          onAnswerSave: handleAnswerSave,
          onComment: handleComment,
          onRequestInput: handleRequestInput,
          onViewEvidence: handleViewEvidence,
        }),
      ),
    [
      questionGroups,
      expandedKeys,
      getAnswerValue,
      handleAnswerChange,
      handleAnswerSave,
      handleComment,
      handleRequestInput,
      handleViewEvidence,
    ],
  );

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

  if (isLoading) {
    return (
      <Layout title="Privacy Assessment">
        <PageHeader heading="Privacy assessments" isSticky />
        <Flex align="center" justify="center" className="p-20">
          <Spin size="large" />
        </Flex>
      </Layout>
    );
  }

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
              <NextLink href={PRIVACY_ASSESSMENTS_ROUTE} passHref>
                <Button>Back to list</Button>
              </NextLink>
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
                <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>CPRA</Tag>
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
                loading={isDeleting}
                icon={<Icons.TrashCan size={16} />}
              />
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

      <div>
        <Space direction="vertical" size="small" className="w-full">
          <div>
            <Flex align="center" gap="small" className="mb-1">
              <Title level={4} className="m-0">
                {assessmentName}
              </Title>
              <Tag
                color={
                  isComplete
                    ? CUSTOM_TAG_COLOR.SUCCESS
                    : CUSTOM_TAG_COLOR.DEFAULT
                }
              >
                {isComplete ? "Completed" : "In progress"}
              </Tag>
            </Flex>
            <Text type="secondary" size="sm" className="mb-2 block">
              System: {assessment.system_name}
            </Text>
            <Text type="secondary" className="block">
              Processing{" "}
              {(assessment.data_categories ?? []).map((category, idx) => (
                <span key={category}>
                  <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>{category}</Tag>
                  {idx < (assessment.data_categories ?? []).length - 1 && " "}
                </span>
              ))}{" "}
              for{" "}
              <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>
                {assessment.data_use_name}
              </Tag>
            </Text>
          </div>

          {!isComplete &&
            (!questionnaireSentAt ? (
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
              <QuestionnaireStatusBar
                timeSinceSent={timeSinceSent}
                answeredCount={answeredSlackQuestions.length}
                totalCount={slackQuestions.length}
                isSendingReminder={isSendingReminder}
                onSendReminder={handleSendReminder}
              />
            ))}

          <QuestionGroupCollapse
            activeKey={expandedKeys}
            onChange={(keys) => setExpandedKeys(keys as string[])}
            items={collapseItems}
          />
        </Space>
      </div>

      <DeleteAssessmentModal
        open={isDeleteModalOpen}
        isDeleting={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setIsDeleteModalOpen(false)}
      />

      <EvidenceDrawer
        open={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
          setFocusedGroupId(null);
          setEvidenceSearchQuery("");
        }}
        focusedGroupId={focusedGroupId}
        questionGroups={questionGroups}
        evidence={filteredEvidence}
        searchQuery={evidenceSearchQuery}
        onSearchChange={setEvidenceSearchQuery}
      />
    </Layout>
  );
};

export default PrivacyAssessmentDetailPage;
