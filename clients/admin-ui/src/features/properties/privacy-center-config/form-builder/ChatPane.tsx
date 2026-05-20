import type { BubbleItemType } from "fidesui";
import {
  Alert,
  Avatar,
  Bubble,
  Flex,
  Sender,
  SparkleIcon,
  Typography,
} from "fidesui";
import { useMemo, useState } from "react";

import EthycaLogo from "~/features/common/logos/EthycaLogo";

import styles from "./ChatPane.module.scss";
import type { ChatMessage, Status } from "./types";

interface ChatPaneProps {
  messages: ChatMessage[];
  status: Status;
  error: string | null;
  onSend: (text: string) => void;
  onAbort: () => void;
  disabled?: boolean;
  disabledReason?: string;
}

const BuilderAvatar = () => (
  <Avatar
    shape="square"
    size="medium"
    className={styles.builderAvatar}
    icon={<EthycaLogo size={15} />}
  />
);

export const ChatPane = ({
  messages,
  status,
  error,
  onSend,
  onAbort,
  disabled,
  disabledReason,
}: ChatPaneProps) => {
  const [draft, setDraft] = useState("");
  const isStreaming = status === "streaming";

  const handleSubmit = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isStreaming) {
      return;
    }
    onSend(trimmed);
    setDraft("");
  };

  const bubbleItems: BubbleItemType[] = useMemo(
    () =>
      messages.map((m, idx) => ({
        key: `${m.role}-${idx}`,
        role: m.role === "user" ? "user" : "ai",
        content: m.content,
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
        avatar: <BuilderAvatar />,
      },
    }),
    [],
  );

  return (
    <Flex vertical className={styles.panel} data-testid="chat-pane">
      {disabled && (
        <Alert
          type="info"
          message={disabledReason ?? "LLM provider not configured."}
        />
      )}
      {error && <Alert type="error" message={error} closable />}

      <div className={styles.body}>
        {messages.length === 0 ? (
          <Flex
            vertical
            align="center"
            justify="center"
            gap="small"
            className={styles.emptyState}
          >
            <SparkleIcon size={24} />
            <Typography.Text type="secondary">
              Describe the form you want and the builder will create it for you.
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
          value={draft}
          onChange={setDraft}
          onSubmit={handleSubmit}
          onCancel={onAbort}
          loading={isStreaming}
          disabled={disabled}
          placeholder="Tell the builder what you want…"
        />
      </div>
    </Flex>
  );
};
