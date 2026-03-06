import {
  Button,
  Collapse,
  CUSTOM_TAG_COLOR,
  Flex,
  notification,
  Space,
  Tag,
  TagList,
  Text,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useMemo, useRef, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { RTKErrorResult } from "~/types/errors/api";

import styles from "./AssessmentDetail.module.scss";
import {
  useCreateQuestionnaireMutation,
  useCreateQuestionnaireReminderMutation,
  useGetAssessmentConfigQuery,
  useGetPrivacyAssessmentQuery,
} from "./privacy-assessments.slice";
import { QuestionCard } from "./QuestionCard";
import { QuestionGroupPanel } from "./QuestionGroupPanel";
import { QuestionnaireStatusBar } from "./QuestionnaireStatusBar";
import { SlackIcon } from "./SlackIcon";
import {
  AnswerSource,
  AnswerStatus,
  PrivacyAssessmentDetailResponse,
} from "./types";

interface AssessmentDetailProps {
  assessment: PrivacyAssessmentDetailResponse;
}

const POLL_INTERVAL = 15_000;

export const AssessmentDetail = ({ assessment }: AssessmentDetailProps) => {
  const message = useMessage();
  const [notificationApi, notificationHolder] = notification.useNotification();
  const { getDataCategoryDisplayName } = useTaxonomies();

  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);

  const { data: config } = useGetAssessmentConfigQuery();
  const [createQuestionnaire, { isLoading: isSending }] =
    useCreateQuestionnaireMutation();
  const [createReminder, { isLoading: isSendingReminder }] =
    useCreateQuestionnaireReminderMutation();

  const slackChannelName = config?.slack_channel_name
    ? `#${config.slack_channel_name}`
    : null;

  const allQuestions = useMemo(
    () => (assessment.question_groups ?? []).flatMap((g) => g.questions),
    [assessment.question_groups],
  );

  const isComplete = useMemo(
    () => allQuestions.every((q) => q.answer_text.trim().length > 0),
    [allQuestions],
  );

  const shouldPoll = !!assessment.questionnaire?.sent_at && !isComplete;
  useGetPrivacyAssessmentQuery(assessment.id, {
    pollingInterval: POLL_INTERVAL,
    skip: !shouldPoll,
  });

  const teamInputIdsRef = useRef<Set<string> | null>(null);
  if (teamInputIdsRef.current === null) {
    teamInputIdsRef.current = new Set(
      allQuestions
        .filter((q) => q.answer_source === AnswerSource.TEAM_INPUT)
        .map((q) => q.question_id),
    );
  }

  useEffect(() => {
    const currentIds = new Set(
      allQuestions
        .filter((q) => q.answer_source === AnswerSource.TEAM_INPUT)
        .map((q) => q.question_id),
    );
    const prevIds = teamInputIdsRef.current!;
    const hasNewAnswers = [...currentIds].some((id) => !prevIds.has(id));

    if (hasNewAnswers) {
      notificationApi.success({
        message: "New answer from Slack",
      });
    }
    teamInputIdsRef.current = currentIds;
  }, [allQuestions, notificationApi]);

  const questionnaireSentAt = useMemo(
    () =>
      assessment.questionnaire?.sent_at
        ? new Date(assessment.questionnaire.sent_at)
        : null,
    [assessment.questionnaire?.sent_at],
  );

  const timeSinceSent = useRelativeTime(questionnaireSentAt);

  const handleRequestInput = async () => {
    if (!slackChannelName) {
      return;
    }

    const needsInputIds = allQuestions
      .filter((q) => q.answer_status === AnswerStatus.NEEDS_INPUT)
      .map((q) => q.question_id);

    try {
      await createQuestionnaire({
        id: assessment.id,
        body: {
          channel: slackChannelName,
          include_question_ids: needsInputIds,
        },
      }).unwrap();
      message.success(`Questions sent to ${slackChannelName} on Slack.`);
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to send questionnaire. Please try again.",
        ),
      );
    }
  };

  const handleSendReminder = async () => {
    try {
      await createReminder({ id: assessment.id }).unwrap();
      message.success(`Reminder sent to ${slackChannelName}.`);
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to send reminder. Please try again.",
        ),
      );
    }
  };

  const collapseItems = useMemo(
    () =>
      (assessment.question_groups ?? []).map((group) => ({
        key: group.id,
        label: (
          <QuestionGroupPanel
            group={group}
            isExpanded={expandedKeys.includes(group.id)}
          />
        ),
        children: (
          <Space direction="vertical" size="middle" className="w-full">
            {group.questions.map((q) => (
              <QuestionCard
                key={q.id}
                assessmentId={assessment.id}
                question={q}
              />
            ))}
          </Space>
        ),
      })),
    [assessment.question_groups, assessment.id, expandedKeys],
  );

  return (
    <Space direction="vertical" size="small" className="w-full">
      {notificationHolder}
      <div>
        <Flex align="center" gap="small" className="mb-1">
          <Typography.Title level={4} className="m-0">
            {assessment.name}
          </Typography.Title>
          <Tag
            color={
              isComplete ? CUSTOM_TAG_COLOR.SUCCESS : CUSTOM_TAG_COLOR.DEFAULT
            }
          >
            {isComplete ? "Completed" : "In progress"}
          </Tag>
        </Flex>
        <Text type="secondary" size="sm" className="block">
          System: {assessment.system_name}
        </Text>
      </div>

      <Flex justify="space-between" align="center" className="mb-2 w-full">
        <Text type="secondary" className="leading-loose">
          Processing{" "}
          {(assessment.data_categories ?? []).length > 0 ? (
            <TagList
              tags={(assessment.data_categories ?? []).map((key) => ({
                value: key,
                label: getDataCategoryDisplayName(key),
              }))}
              maxTags={1}
              expandable
            />
          ) : (
            <Tag>0 data categories</Tag>
          )}{" "}
          for{" "}
          <TagList
            tags={assessment.data_use_name ? [assessment.data_use_name] : []}
            maxTags={1}
          />
        </Text>
        {!isComplete && (
          <Tooltip
            title={
              !slackChannelName
                ? "Configure a Slack channel in assessment settings to enable this feature"
                : undefined
            }
          >
            <Button
              icon={<SlackIcon size={14} />}
              size="small"
              onClick={handleRequestInput}
              disabled={!slackChannelName}
              loading={isSending}
            >
              Request input from team
            </Button>
          </Tooltip>
        )}
      </Flex>

      {!isComplete && questionnaireSentAt && (
        <QuestionnaireStatusBar
          channel={slackChannelName ?? ""}
          timeSinceSent={timeSinceSent}
          answeredCount={assessment.questionnaire!.answered_questions}
          totalCount={assessment.questionnaire!.total_questions}
          isSendingReminder={isSendingReminder}
          onSendReminder={handleSendReminder}
        />
      )}

      <Collapse
        className={styles.collapse}
        activeKey={expandedKeys}
        onChange={(keys) => setExpandedKeys(keys as string[])}
        items={collapseItems}
        size="large"
      />

      {/* Commented out because it does not fit demo needs at the moment */}
      {/* {slackChannelName && (
        <RequestInputModal
          open={isRequestInputOpen}
          onClose={() => setIsRequestInputOpen(false)}
          assessmentId={assessment.id}
          questions={allQuestions}
          slackChannelName={slackChannelName}
        />
      )} */}
    </Space>
  );
};
