import React from "react";

import styles from "./AIChatPane.module.scss";

export interface ChatMessageData {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatMessageProps {
  message: ChatMessageData;
}

/**
 * Strip fenced JSON code blocks from assistant messages so users
 * don't see raw policy JSON (the policy is rendered on the canvas instead).
 */
const stripJsonBlocks = (text: string): string => {
  // Remove ```json ... ``` blocks (and optional trailing backslashes/whitespace)
  const stripped = text.replace(/```json[\s\S]*?```\\*/g, "").trim();
  // Collapse 3+ consecutive newlines down to 2
  return stripped.replace(/\n{3,}/g, "\n\n");
};

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === "user";
  const displayContent =
    isUser ? message.content : stripJsonBlocks(message.content);

  return (
    <div className={`${styles.message} ${isUser ? styles.user : styles.assistant}`}>
      <div className={styles.messageBubble}>
        {displayContent}
        <div className={styles.messageTime}>
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>
    </div>
  );
};
