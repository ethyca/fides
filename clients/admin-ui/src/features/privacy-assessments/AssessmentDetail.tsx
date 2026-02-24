import {
  Button,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  Space,
  Tag,
  Text,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import { RTKErrorResult } from "~/types/errors/api";

import { DEFAULT_SLACK_CHANNEL } from "./constants";
import { DeleteAssessmentModal } from "./DeleteAssessmentModal";
import {
  useCreateQuestionnaireMutation,
  useCreateQuestionnaireReminderMutation,
  useDeletePrivacyAssessmentMutation,
  useUpdateAssessmentAnswerMutation,
} from "./privacy-assessments.slice";
import { QuestionGroupCollapse } from "./QuestionGroupCollapse";
import { buildQuestionGroupPanelItem } from "./QuestionGroupPanel";
import { QuestionnaireStatusBar } from "./QuestionnaireStatusBar";
import { SlackIcon } from "./SlackIcon";
import { PrivacyAssessmentDetailResponse } from "./types";
import {
  getSlackQuestions,
  getTimeSince,
  isAssessmentComplete,
  truncate,
} from "./utils";

const { Title } = Typography;

interface AssessmentDetailProps {
  assessment: PrivacyAssessmentDetailResponse;
  refetch: () => void;
}

export const AssessmentDetail = ({
  assessment,
  refetch,
}: AssessmentDetailProps) => {
  const router = useRouter();
  const message = useMessage();

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [localAnswers, setLocalAnswers] = useState<Record<string, string>>({});

  const [updateAnswer] = useUpdateAssessmentAnswerMutation();
  const [deleteAssessment, { isLoading: isDeleting }] =
    useDeletePrivacyAssessmentMutation();
  const [createQuestionnaire, { isLoading: isSendingQuestionnaire }] =
    useCreateQuestionnaireMutation();
  const [createReminder, { isLoading: isSendingReminder }] =
    useCreateQuestionnaireReminderMutation();

  const questionGroups = useMemo(
    () => assessment.question_groups ?? [],
    [assessment.question_groups],
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
    const sentAt = assessment.questionnaire?.sent_at
      ? new Date(assessment.questionnaire.sent_at)
      : null;
    return {
      questionnaireSentAt: sentAt,
      timeSinceSent: sentAt ? getTimeSince(sentAt.toISOString()) : "",
    };
  }, [assessment.questionnaire?.sent_at]);

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
          id: assessment.id,
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
    [assessment.id, message, updateAnswer],
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
        id: assessment.id,
        body: { channel: DEFAULT_SLACK_CHANNEL },
      }).unwrap();
      message.success(
        `Questionnaire sent to ${DEFAULT_SLACK_CHANNEL} on Slack.`,
      );
      refetch();
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to send questionnaire. Please try again.",
        ),
      );
    }
  }, [assessment.id, createQuestionnaire, message, refetch]);

  const handleSendReminder = async () => {
    try {
      await createReminder({ id: assessment.id }).unwrap();
      message.success(`Reminder sent to ${DEFAULT_SLACK_CHANNEL}.`);
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

  const handleDelete = async () => {
    try {
      await deleteAssessment(assessment.id).unwrap();
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
    ],
  );

  const assessmentName = assessment.name;

  return (
    <>
      <Space direction="vertical" size="small" className="w-full">
        <Flex justify="space-between" align="flex-start">
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
        </Flex>

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

      <DeleteAssessmentModal
        open={isDeleteModalOpen}
        isDeleting={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setIsDeleteModalOpen(false)}
      />
    </>
  );
};
