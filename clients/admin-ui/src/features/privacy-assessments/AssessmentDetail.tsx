import {
  Button,
  Collapse,
  CUSTOM_TAG_COLOR,
  Drawer,
  Flex,
  Space,
  Tag,
  TagList,
  Text,
  Tooltip,
  Typography,
  useMessage,
  useNotification,
} from "fidesui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { getErrorMessage } from "~/features/common/helpers";
import { useRelativeTime } from "~/features/common/hooks/useRelativeTime";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { RTKErrorResult } from "~/types/errors/api";

import { useGetChatConfigsQuery } from "../chat-provider/chatProvider.slice";
import { SlackLogo } from "../common/logos/SlackLogo";
import styles from "./AssessmentDetail.module.scss";
import { EvidenceDrawer } from "./EvidenceDrawer";
import QuestionnaireChat from "./QuestionnaireChat";
import {
  useCreateQuestionnaireMutation,
  useCreateQuestionnaireReminderMutation,
  useGetAssessmentConfigQuery,
  useGetPrivacyAssessmentQuery,
} from "./privacy-assessments.slice";
import { QuestionCard } from "./QuestionCard";
import { QuestionGroupPanel } from "./QuestionGroupPanel";
import { QuestionnaireStatusBar } from "./QuestionnaireStatusBar";
import {
  AnswerSource,
  AnswerStatus,
  EvidenceItem,
  PrivacyAssessmentDetailResponse,
  QuestionGroup,
  QuestionnaireSessionStatus,
} from "./types";
import { deduplicateEvidence, filterEvidence } from "./utils";

interface AssessmentDetailProps {
  assessment: PrivacyAssessmentDetailResponse;
}

const POLL_INTERVAL = 15_000;

export const AssessmentDetail = ({ assessment }: AssessmentDetailProps) => {
  const message = useMessage();
  const notificationApi = useNotification();
  const { getDataCategoryDisplayName } = useTaxonomies();
  const currentUser = useAppSelector(selectUser);

  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [focusedGroupId, setFocusedGroupId] = useState<string | null>(null);
  const [evidenceSearchQuery, setEvidenceSearchQuery] = useState("");

  const focusedGroup = useMemo<QuestionGroup | undefined>(
    () =>
      focusedGroupId
        ? (assessment.question_groups ?? []).find(
            (g) => g.id === focusedGroupId,
          )
        : undefined,
    [focusedGroupId, assessment.question_groups],
  );

  const focusedGroupEvidence = useMemo<EvidenceItem[]>(
    () =>
      focusedGroup
        ? deduplicateEvidence(focusedGroup.questions.flatMap((q) => q.evidence))
        : [],
    [focusedGroup],
  );

  const filteredEvidence = useMemo(
    () => filterEvidence(focusedGroupEvidence, evidenceSearchQuery),
    [focusedGroupEvidence, evidenceSearchQuery],
  );

  const handleViewEvidence = useCallback((groupId: string) => {
    setFocusedGroupId(groupId);
    setDrawerOpen(true);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setDrawerOpen(false);
    setEvidenceSearchQuery("");
  }, []);

  const { data: config } = useGetAssessmentConfigQuery();
  const { data: chatConfigs } = useGetChatConfigsQuery();
  const [createQuestionnaire, { isLoading: isSending }] =
    useCreateQuestionnaireMutation();
  const [createReminder, { isLoading: isSendingReminder }] =
    useCreateQuestionnaireReminderMutation();

  const enabledChatConfig = chatConfigs?.items.find((c) => c.enabled);
  const isFidesProvider = enabledChatConfig?.provider_type === "fides";

  const channelName = config?.slack_channel_name
    ? `#${config.slack_channel_name}`
    : null;
  const hasChannel = isFidesProvider || !!channelName;

  const [chatOpen, setChatOpen] = useState(false);
  const [chatSessionKey, setChatSessionKey] = useState<string>("new");

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

    if (hasNewAnswers && !chatOpen) {
      notificationApi.success({
        message: isFidesProvider
          ? "New answer received"
          : "New answer from Slack",
      });
    }
    teamInputIdsRef.current = currentIds;
  }, [allQuestions, notificationApi, isFidesProvider, chatOpen]);

  const questionnaireSentAt = useMemo(
    () =>
      assessment.questionnaire?.sent_at
        ? new Date(assessment.questionnaire.sent_at)
        : null,
    [assessment.questionnaire?.sent_at],
  );

  const timeSinceSent = useRelativeTime(questionnaireSentAt);

  const handleRequestInput = async () => {
    if (!hasChannel) {
      return;
    }

    if (isFidesProvider) {
      setChatSessionKey(
        assessment.questionnaire?.status ===
          QuestionnaireSessionStatus.IN_PROGRESS
          ? (assessment.questionnaire?.questionnaire_id ?? "new")
          : `new-${Date.now()}`,
      );
      setChatOpen(true);
      return;
    }

    const needsInputIds = allQuestions
      .filter((q) => q.answer_status === AnswerStatus.NEEDS_INPUT)
      .map((q) => q.question_id);

    try {
      await createQuestionnaire({
        id: assessment.id,
        body: {
          channel: channelName!,
          include_question_ids: needsInputIds,
        },
      }).unwrap();
      message.success(`Questions sent to ${channelName} on Slack.`);
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
      message.success(`Reminder sent to ${channelName}.`);
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
            onViewEvidence={() => handleViewEvidence(group.id)}
          />
        ),
        children: (
          <Space orientation="vertical" size="medium" className="w-full">
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
    [
      assessment.question_groups,
      assessment.id,
      expandedKeys,
      handleViewEvidence,
    ],
  );

  return (
    <Space orientation="vertical" size="small" className="w-full">
      <div>
        <Flex align="center" gap="small" className="mb-1">
          <Typography.Title level={2} className="m-0">
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
        {assessment.template_name && (
          <Text type="secondary" size="sm" className="block">
            {assessment.template_name}
          </Text>
        )}
      </div>

      <Flex justify="space-between" align="center" className="mb-2 w-full">
        <div>
          {(assessment.data_categories ?? []).length > 0 ? (
            <TagList
              tags={(assessment.data_categories ?? []).map((key) => ({
                value: key,
                label: getDataCategoryDisplayName(key),
              }))}
              maxTags={2}
              expandable
            />
          ) : (
            <Tag>0 data categories</Tag>
          )}
        </div>
        {!isComplete && (
          <Tooltip
            title={
              !hasChannel
                ? "Configure a chat provider in assessment settings to enable this feature"
                : undefined
            }
          >
            <Button
              icon={isFidesProvider ? undefined : <SlackLogo size={14} />}
              size="small"
              onClick={handleRequestInput}
              disabled={!hasChannel}
              loading={isSending}
            >
              {isFidesProvider
                ? assessment.questionnaire?.sent_at &&
                  assessment.questionnaire?.status ===
                    QuestionnaireSessionStatus.IN_PROGRESS
                  ? "Resume questionnaire"
                  : "Start questionnaire"
                : "Request input from team"}
            </Button>
          </Tooltip>
        )}
      </Flex>

      {questionnaireSentAt && (
        <QuestionnaireStatusBar
          status={assessment.questionnaire!.status}
          stopReason={assessment.questionnaire!.stop_reason}
          channel={isFidesProvider ? "Fides" : (channelName ?? "")}
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

      <EvidenceDrawer
        open={drawerOpen}
        onClose={handleCloseDrawer}
        focusedGroupId={focusedGroupId}
        group={focusedGroup}
        evidence={filteredEvidence}
        searchQuery={evidenceSearchQuery}
        onSearchChange={setEvidenceSearchQuery}
      />

      {isFidesProvider && (
        <Drawer
          title="Privacy Assessment Questionnaire"
          open={chatOpen}
          onClose={() => setChatOpen(false)}
          width={480}
          destroyOnClose={assessment.questionnaire?.status !== QuestionnaireSessionStatus.IN_PROGRESS}
          styles={{ body: { padding: 0, display: "flex", flexDirection: "column" } }}
        >
          <QuestionnaireChat
            key={chatSessionKey}
            assessmentId={assessment.id}
            questionnaireId={
              assessment.questionnaire?.status === QuestionnaireSessionStatus.IN_PROGRESS
                ? (assessment.questionnaire?.questionnaire_id ?? undefined)
                : undefined
            }
            userName={
              currentUser?.isRootUser
                ? "Root User"
                : `${currentUser?.first_name ?? ""} ${currentUser?.last_name ?? ""}`.trim() ||
                  currentUser?.username ||
                  currentUser?.email_address ||
                  "User"
            }
            onStatusChange={() => undefined}
          />
        </Drawer>
      )}
    </Space>
  );
};
