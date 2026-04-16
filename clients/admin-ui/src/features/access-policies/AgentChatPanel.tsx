import type { BubbleItemType } from "@ant-design/x";
import { Bubble, Sender } from "@ant-design/x";
import { Flex, Icons, Tag, Typography, useMessage } from "fidesui";
import { useCallback, useRef, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors";

import { useSendAccessPolicyChatMessageMutation } from "./agent-chat.slice";

interface AgentChatPanelProps {
  currentYaml: string;
  onYamlProposed: (yaml: string) => void;
}

interface ChatMessage {
  key: string;
  role: "user" | "ai";
  content: string;
  yamlApplied?: boolean;
}

let messageCounter = 0;

const AgentChatPanel = ({
  currentYaml,
  onYamlProposed,
}: AgentChatPanelProps) => {
  const messageApi = useMessage();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatHistoryId, setChatHistoryId] = useState<string>();
  const [inputValue, setInputValue] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  const [sendMessage, { isLoading }] = useSendAccessPolicyChatMessageMutation();

  const handleSend = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) {
        return;
      }

      messageCounter += 1;
      const userKey = `user-${messageCounter}`;
      const userMsg: ChatMessage = {
        key: userKey,
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

        messageCounter += 1;
        const assistantMsg: ChatMessage = {
          key: `ai-${messageCounter}`,
          role: "ai",
          content: response.message,
          yamlApplied: !!response.new_policy_yaml,
        };

        setMessages((prev) => [...prev, assistantMsg]);

        if (response.new_policy_yaml) {
          onYamlProposed(response.new_policy_yaml);
        }
      } catch (error) {
        messageApi.error(getErrorMessage((error as RTKErrorResult).error));
        messageCounter += 1;
        setMessages((prev) => [
          ...prev,
          {
            key: `error-${messageCounter}`,
            role: "ai",
            content: "Something went wrong. Please try again.",
          },
        ]);
      }
    },
    [
      isLoading,
      chatHistoryId,
      currentYaml,
      sendMessage,
      onYamlProposed,
      messageApi,
    ],
  );

  const bubbleItems: BubbleItemType[] = messages.map((msg) => ({
    key: msg.key,
    role: msg.role === "user" ? "user" : "ai",
    content: msg.content,
    footer: msg.yamlApplied ? (
      <Tag color="success" icon={<Icons.Checkmark size={12} />}>
        Policy updated
      </Tag>
    ) : undefined,
  }));

  return (
    <Flex vertical style={{ height: "100%", overflow: "hidden" }}>
      <Flex
        align="center"
        gap="small"
        style={{
          padding: "8px 12px",
          borderBottom: "1px solid var(--ant-color-border)",
          flexShrink: 0,
        }}
      >
        <Icons.Ai size={16} />
        <Typography.Text strong>Policy assistant</Typography.Text>
      </Flex>

      <div ref={listRef} style={{ flex: 1, overflow: "hidden" }}>
        {messages.length === 0 ? (
          <Flex
            vertical
            align="center"
            justify="center"
            gap="small"
            style={{
              height: "100%",
              padding: 24,
              color: "var(--ant-color-text-tertiary)",
              textAlign: "center",
            }}
          >
            <Icons.Ai size={32} />
            <Typography.Text type="secondary">
              Describe what your policy should do and the assistant will help
              you build it.
            </Typography.Text>
          </Flex>
        ) : (
          <Bubble.List
            style={{ height: "100%" }}
            autoScroll
            role={{
              user: {
                placement: "end",
                variant: "filled",
              },
              ai: {
                placement: "start",
                variant: "outlined",
                avatar: <Icons.Ai size={20} />,
                typing: { effect: "fade-in" },
              },
            }}
            items={bubbleItems}
          />
        )}
      </div>

      <div
        style={{
          padding: "8px 12px",
          borderTop: "1px solid var(--ant-color-border)",
          flexShrink: 0,
        }}
      >
        <Sender
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSend}
          loading={isLoading}
          placeholder="Describe your policy..."
        />
      </div>
    </Flex>
  );
};

export default AgentChatPanel;
