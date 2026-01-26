import React, { useCallback, useRef, useEffect } from "react";
import { Button } from "fidesui";

import styles from "./AIChatPane.module.scss";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  isLoading?: boolean;
}

export const ChatInput = ({
  value,
  onChange,
  onSend,
  disabled,
  isLoading,
}: ChatInputProps) => {
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textArea = textAreaRef.current;
    if (textArea) {
      textArea.style.height = "auto";
      textArea.style.height = `${Math.min(textArea.scrollHeight, 100)}px`;
    }
  }, [value]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (value.trim() && !disabled && !isLoading) {
          onSend();
        }
      }
    },
    [value, disabled, isLoading, onSend]
  );

  return (
    <div className={styles.inputSection}>
      <div className={styles.inputWrapper}>
        <textarea
          ref={textAreaRef}
          className={styles.textArea}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want your policy to do..."
          disabled={disabled || isLoading}
          rows={1}
        />
        <Button
          className={styles.sendButton}
          type="primary"
          onClick={onSend}
          loading={isLoading}
          disabled={!value.trim() || disabled}
        >
          Send
        </Button>
      </div>
      <div className={styles.inputHint}>
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
};
