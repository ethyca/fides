import { formatDistanceToNow } from "date-fns";
import {
  Button,
  Collapse,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  Space,
  Tag,
  TagList,
  Text,
  Tooltip,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import { RTKErrorResult } from "~/types/errors/api";

import styles from "./AssessmentDetail.module.scss";
import {
  useCreateQuestionnaireReminderMutation,
  useDeletePrivacyAssessmentMutation,
  useGetAssessmentConfigQuery,
} from "./privacy-assessments.slice";
import { QuestionCard } from "./QuestionCard";
import { QuestionGroupPanel } from "./QuestionGroupPanel";
import { QuestionnaireStatusBar } from "./QuestionnaireStatusBar";
import { RequestInputModal } from "./RequestInputModal";
import { SlackIcon } from "./SlackIcon";
import { PrivacyAssessmentDetailResponse } from "./types";
import { getSlackQuestions } from "./utils";

interface AssessmentDetailProps {
  assessment: PrivacyAssessmentDetailResponse;
}

export const AssessmentDetail = ({ assessment }: AssessmentDetailProps) => {
  const router = useRouter();
  const message = useMessage();
  const modalApi = useModal();
  const { getDataCategoryDisplayName } = useTaxonomies();

  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [isRequestInputOpen, setIsRequestInputOpen] = useState(false);

  const { data: config } = useGetAssessmentConfigQuery();
  const [deleteAssessment, { isLoading: isDeleting }] =
    useDeletePrivacyAssessmentMutation();
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

  const { slackQuestions, answeredSlackQuestions } = useMemo(
    () => getSlackQuestions(allQuestions),
    [allQuestions],
  );

  const questionnaireSentAt = useMemo(
    () =>
      assessment.questionnaire?.sent_at
        ? new Date(assessment.questionnaire.sent_at)
        : null,
    [assessment.questionnaire?.sent_at],
  );

  const [timeSinceSent, setTimeSinceSent] = useState(() =>
    questionnaireSentAt
      ? formatDistanceToNow(questionnaireSentAt, { addSuffix: true })
      : "",
  );

  useEffect(() => {
    if (!questionnaireSentAt) {
      return undefined;
    }
    setTimeSinceSent(
      formatDistanceToNow(questionnaireSentAt, { addSuffix: true }),
    );
    const interval = setInterval(() => {
      setTimeSinceSent(
        formatDistanceToNow(questionnaireSentAt, { addSuffix: true }),
      );
    }, 60_000);
    return () => {
      clearInterval(interval);
    };
  }, [questionnaireSentAt]);

  const handleDelete = () => {
    modalApi.confirm({
      title: "Delete assessment",
      content: (
        <Space direction="vertical" size="middle" className="w-full">
          <Text>Are you sure you want to delete this assessment?</Text>
          <Text type="secondary">
            This action cannot be undone. All assessment data, including any
            responses and documentation, will be permanently removed.
          </Text>
        </Space>
      ),
      okText: "Delete",
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        try {
          await deleteAssessment(assessment.id).unwrap();
          message.success("Assessment deleted.");
          router.push(PRIVACY_ASSESSMENTS_ROUTE);
        } catch (error) {
          message.error(
            getErrorMessage(
              error as RTKErrorResult["error"],
              "Failed to delete assessment. Please try again.",
            ),
          );
        }
      },
    });
  };

  const handleRequestInput = () => {
    if (!slackChannelName) {
      return;
    }
    setIsRequestInputOpen(true);
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
      <Flex justify="space-between" align="flex-start">
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
          <Text type="secondary" size="sm" className="mb-2 block">
            System: {assessment.system_name}
          </Text>
          <Text type="secondary" className="block leading-loose">
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
        </div>

        <Space>
          <Tooltip title="Delete assessment">
            <Button
              type="text"
              danger
              onClick={handleDelete}
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
              >
                Request input from team
              </Button>
            </Tooltip>
          </Flex>
        ) : (
          <QuestionnaireStatusBar
            channel={slackChannelName ?? ""}
            timeSinceSent={timeSinceSent}
            answeredCount={answeredSlackQuestions.length}
            totalCount={slackQuestions.length}
            isSendingReminder={isSendingReminder}
            onSendReminder={handleSendReminder}
          />
        ))}

      <Collapse
        className={styles.collapse}
        activeKey={expandedKeys}
        onChange={(keys) => setExpandedKeys(keys as string[])}
        items={collapseItems}
        size="large"
      />

      {slackChannelName && (
        <RequestInputModal
          open={isRequestInputOpen}
          onClose={() => setIsRequestInputOpen(false)}
          assessmentId={assessment.id}
          questions={allQuestions}
          slackChannelName={slackChannelName}
        />
      )}
    </Space>
  );
};
