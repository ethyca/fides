import type { BubbleItemType } from "fidesui";
import {
  Avatar,
  Bubble,
  Flex,
  Icons,
  Sender,
  Typography,
  useMessage,
  XMarkdown,
} from "fidesui";
import { useCallback, useMemo, useRef, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import Image from "~/features/common/Image";
import { RTKErrorResult } from "~/types/errors";

import {
  PolicyUpdate,
  useSendAccessPolicyChatMessageMutation,
} from "./agent-chat.slice";
import styles from "./AgentChatPanel.module.scss";
import PolicyAgentWorking from "./PolicyAgentWorking";

interface AgentChatPanelProps {
  currentYaml: string;
  onPolicyUpdate: (update: PolicyUpdate) => void;
  isAgentWorking: boolean;
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

const renderAgentMarkdown = (content: string) => (
  <Typography>
    <XMarkdown escapeRawHtml openLinksInNewTab content={content} />
  </Typography>
);

const AgentChatPanel = ({
  currentYaml,
  onPolicyUpdate,
  isAgentWorking,
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
          yamlApplied: !!response.policy_update,
        };

        setMessages((prev) => [...prev, agentMsg]);

        if (response.policy_update) {
          onPolicyUpdate(response.policy_update);
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
      onPolicyUpdate,
      messageApi,
    ],
  );

  const latestYamlAppliedKey = useMemo(
    () => messages.findLast((m) => m.yamlApplied)?.key,
    [messages],
  );

  const bubbleItems: BubbleItemType[] = useMemo(
    () =>
      messages.map((msg) => {
        let footer;
        if (msg.yamlApplied) {
          const isLatest = msg.key === latestYamlAppliedKey;
          footer =
            isLatest && isAgentWorking ? (
              <PolicyAgentWorking size="small" />
            ) : (
              <Flex align="center" gap="small">
                <Icons.CheckmarkFilled
                  style={{ color: "var(--fidesui-color-success)" }}
                />
                <Typography.Text type="secondary">
                  The policy was updated
                </Typography.Text>
              </Flex>
            );
        }
        return {
          key: msg.key,
          role: msg.role === "user" ? "user" : "ai",
          content: msg.content,
          footer,
        };
      }),
    [messages, latestYamlAppliedKey, isAgentWorking],
  );

  const roles = useMemo(
    () => ({
      user: {
        placement: "end" as const,
        variant: "filled" as const,
        styles: {
          content: { background: "var(--fidesui-color-fill-content)" },
        },
      },
      ai: {
        placement: "start" as const,
        variant: "outlined" as const,
        avatar: <AgentAvatar />,
        contentRender: renderAgentMarkdown,
      },
    }),
    [],
  );

  return (
    <Flex vertical className={styles.panel} data-testid="agent-chat-panel">
      <Flex align="center" gap="small" className={styles.header}>
        <Typography.Title level={3}>Policy agent</Typography.Title>
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
          autoSize={{ minRows: 1, maxRows: 12 }}
        />
      </div>
    </Flex>
  );
};

export default AgentChatPanel;
