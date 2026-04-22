import type { BubbleItemType } from "fidesui";
import {
  Avatar,
  Bubble,
  Flex,
  Sender,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useMemo, useRef, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import Image from "~/features/common/Image";
import { RTKErrorResult } from "~/types/errors";

import { useSendAccessPolicyChatMessageMutation } from "./agent-chat.slice";
import styles from "./AgentChatPanel.module.scss";

interface AgentChatPanelProps {
  currentYaml: string;
  onYamlProposed: (yaml: string) => void;
}

interface ChatMessage {
  key: string;
  role: "user" | "agent";
  content: string;
  yamlApplied?: boolean;
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

const AgentChatPanel = ({
  currentYaml,
  onYamlProposed,
}: AgentChatPanelProps) => {
  const messageApi = useMessage();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatHistoryId, setChatHistoryId] = useState<string>();
  const [inputValue, setInputValue] = useState("");
  const messageCounterRef = useRef(0);

  const [sendMessage, { isLoading }] = useSendAccessPolicyChatMessageMutation();

  const nextKey = useCallback((prefix: string) => {
    messageCounterRef.current += 1;
    return `${prefix}-${messageCounterRef.current}`;
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) {
        return;
      }

      const userMsg: ChatMessage = {
        key: nextKey("user"),
        role: "user",
        content: trimmed,
      };

      setMessages((prev) => [...prev, userMsg]);
      setInputValue("");

      try {
        const response = await sendMessage({
          prompt: trimmed,
          chat_history_id: chatHistoryId,
          current_policy_yaml: currentYaml,
        }).unwrap();

        setChatHistoryId(response.chat_history_id);

        const agentMsg: ChatMessage = {
          key: nextKey("agent"),
          role: "agent",
          content: response.message,
          yamlApplied: !!response.new_policy_yaml,
        };

        setMessages((prev) => [...prev, agentMsg]);

        if (response.new_policy_yaml) {
          onYamlProposed(response.new_policy_yaml);
        }
      } catch (error) {
        messageApi.error(getErrorMessage(error as RTKErrorResult["error"]));
        setMessages((prev) => [
          ...prev,
          {
            key: nextKey("error"),
            role: "agent",
            content: "Something went wrong. Please try again.",
          },
        ]);
      }
    },
    [
      isLoading,
      nextKey,
      chatHistoryId,
      currentYaml,
      sendMessage,
      onYamlProposed,
      messageApi,
    ],
  );

  const bubbleItems: BubbleItemType[] = useMemo(
    () =>
      messages.map((msg) => ({
        key: msg.key,
        role: msg.role === "user" ? "user" : "ai",
        content: msg.content,
        footer: msg.yamlApplied ? (
          <Tag color="success">Policy updated</Tag>
        ) : undefined,
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

  return (
    <Flex vertical className={styles.panel} data-testid="agent-chat-panel">
      <Flex align="center" gap="small" className={styles.header}>
        <Typography.Text strong>Policy builder agent</Typography.Text>
      </Flex>

      <div className={styles.body}>
        {messages.length === 0 ? (
          <Flex
            vertical
            align="center"
            justify="center"
            gap="small"
            className={styles.emptyState}
          >
            <Typography.Text type="secondary">
              Describe what your policy should do and the agent will help you
              build it.
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
          loading={isLoading}
          placeholder="Describe your policy…"
        />
      </div>
    </Flex>
  );
};

export default AgentChatPanel;
