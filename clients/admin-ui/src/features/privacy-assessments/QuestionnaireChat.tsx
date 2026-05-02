import type { BubbleItemType } from "fidesui";
import {
  Avatar,
  Bubble,
  Flex,
  Sender,
  Spin,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import Image from "~/features/common/Image";
import { RTKErrorResult } from "~/types/errors";

import {
  useGetQuestionnaireChatMessagesQuery,
  useSendQuestionnaireChatReplyMutation,
  useStartQuestionnaireChatMutation,
} from "./privacy-assessments.slice";
import styles from "./QuestionnaireChat.module.scss";
import { QuestionnaireChatMessage } from "./types";

interface QuestionnaireChatProps {
  assessmentId: string;
  questionnaireId?: string;
  userName?: string;
  onStatusChange?: () => void;
}

const AgentLogoMark = ({ size = 20 }: { size?: number }) => (
  <Image
    src="/images/logomark-ethyca.svg"
    alt="Ethyca"
    width={size}
    height={size}
  />
);

const AgentAvatar = () => (
  <Avatar
    shape="square"
    size="medium"
    className={styles.agentAvatar}
    icon={<AgentLogoMark size={15} />}
  />
);

interface LocalMessage {
  key: string;
  role: "user" | "ai";
  content: string;
  senderName?: string;
}

const QuestionnaireChat = ({
  assessmentId,
  questionnaireId: initialQuestionnaireId,
  userName,
  onStatusChange,
}: QuestionnaireChatProps) => {
  const messageApi = useMessage();
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [questionnaireId, setQuestionnaireId] = useState(
    initialQuestionnaireId,
  );
  const [inputValue, setInputValue] = useState("");
  const [status, setStatus] = useState("in_progress");
  const [progress, setProgress] = useState({ answered: 0, total: 0 });
  const [isStarting, setIsStarting] = useState(!initialQuestionnaireId);
  const messageCounterRef = useRef(0);
  const initialLoadDone = useRef(false);

  const [startChat] = useStartQuestionnaireChatMutation();
  const [sendReply, { isLoading: isSending }] =
    useSendQuestionnaireChatReplyMutation();

  const { data: existingMessages } = useGetQuestionnaireChatMessagesQuery(
    questionnaireId!,
    { skip: !questionnaireId || !initialQuestionnaireId },
  );

  const nextKey = useCallback((prefix: string) => {
    messageCounterRef.current += 1;
    return `${prefix}-${messageCounterRef.current}`;
  }, []);

  const mapBackendMessages = useCallback(
    (msgs: QuestionnaireChatMessage[]): LocalMessage[] =>
      msgs.map((m) => ({
        key: nextKey(m.is_bot_message ? "ai" : "user"),
        role: m.is_bot_message ? ("ai" as const) : ("user" as const),
        content: m.text,
        senderName: m.sender_display_name ?? m.sender_email ?? undefined,
      })),
    [nextKey],
  );

  useEffect(() => {
    if (initialLoadDone.current) {
      return;
    }
    if (existingMessages && existingMessages.length > 0) {
      initialLoadDone.current = true;
      setMessages(mapBackendMessages(existingMessages));
      setIsStarting(false);
    }
  }, [existingMessages, mapBackendMessages]);

  const initChatCalled = useRef(false);

  useEffect(() => {
    if (initialQuestionnaireId || initChatCalled.current) {
      return;
    }
    initChatCalled.current = true;

    const initChat = async () => {
      try {
        const response = await startChat({
          assessment_id: assessmentId,
        }).unwrap();

        initialLoadDone.current = true;
        setQuestionnaireId(response.questionnaire_id);
        setProgress({
          answered: 0,
          total: response.total_questions,
        });
        setMessages(mapBackendMessages(response.messages));
        onStatusChange?.();
      } catch (error) {
        messageApi.error(getErrorMessage(error as RTKErrorResult["error"]));
      } finally {
        setIsStarting(false);
      }
    };

    initChat();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isSending) {
        return;
      }

      if (!questionnaireId) {
        return;
      }

      setMessages((prev) => [
        ...prev,
        { key: nextKey("user"), role: "user", content: trimmed, senderName: userName },
      ]);
      setInputValue("");

      try {
        const response = await sendReply({
          questionnaire_id: questionnaireId,
          message_text: trimmed,
        }).unwrap();

        const botMessages: LocalMessage[] = response.bot_messages.map((m) => ({
          key: nextKey("ai"),
          role: "ai" as const,
          content: m.text,
        }));

        setMessages((prev) => [...prev, ...botMessages]);
        setStatus(response.status);
        setProgress({
          answered: response.answered_questions,
          total: response.total_questions,
        });
        onStatusChange?.();
      } catch (error) {
        messageApi.error(getErrorMessage(error as RTKErrorResult["error"]));
        setMessages((prev) => [
          ...prev,
          {
            key: nextKey("error"),
            role: "ai",
            content: "Something went wrong. Please try again.",
          },
        ]);
      }
    },
    [
      isSending,
      status,
      questionnaireId,
      nextKey,
      sendReply,
      onStatusChange,
      messageApi,
    ],
  );

  const bubbleItems: BubbleItemType[] = useMemo(
    () =>
      messages.map((msg) => ({
        key: msg.key,
        role: msg.role,
        content: msg.content,
        header: msg.role === "user" ? msg.senderName : undefined,
      })),
    [messages],
  );

  const roles = useMemo(
    () => ({
      user: {
        placement: "end" as const,
        variant: "filled" as const,
      },
      ai: {
        placement: "start" as const,
        variant: "outlined" as const,
        avatar: <AgentAvatar />,
      },
    }),
    [],
  );

  const isComplete = status === "completed" || status === "stopped";
  const progressText =
    progress.total > 0
      ? `${progress.answered}/${progress.total} answered`
      : "";

  return (
    <Flex vertical className={styles.panel} data-testid="questionnaire-chat">
      <Flex align="center" justify="space-between" className={styles.header}>
        <Typography.Text strong>Assessment Questionnaire</Typography.Text>
        {progressText && (
          <Typography.Text type="secondary">{progressText}</Typography.Text>
        )}
      </Flex>

      <div className={styles.body}>
        {isStarting ? (
          <Flex
            vertical
            align="center"
            justify="center"
            gap="small"
            className={styles.emptyState}
          >
            <Spin />
            <Typography.Text type="secondary">
              Preparing questionnaire...
            </Typography.Text>
          </Flex>
        ) : messages.length === 0 ? (
          <Flex
            vertical
            align="center"
            justify="center"
            gap="small"
            className={styles.emptyState}
          >
            <Typography.Text type="secondary">
              No messages yet.
            </Typography.Text>
          </Flex>
        ) : (
          <Bubble.List
            className={styles.list}
            autoScroll
            role={roles}
            items={bubbleItems}
          />
        )}
      </div>

      <div className={styles.footer}>
        <Sender
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSend}
          loading={isSending}
          disabled={isComplete || isStarting}
          placeholder={
            status === "stopped"
              ? "Questionnaire stopped"
              : status === "completed"
                ? "Questionnaire complete"
                : "Type your response..."
          }
        />
      </div>
    </Flex>
  );
};

export default QuestionnaireChat;
