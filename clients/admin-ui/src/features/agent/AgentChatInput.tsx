/**
 * Chat input component for sending messages.
 */

import {
  ChakraBox as Box,
  ChakraButton as Button,
  ChakraFlex as Flex,
  ChakraTextarea as Textarea,
} from "fidesui";
import { KeyboardEvent, useCallback, useRef, useState } from "react";

interface AgentChatInputProps {
  onSend: (content: string) => void;
  isDisabled?: boolean;
  onCancel?: () => void;
}

export default function AgentChatInput({
  onSend,
  isDisabled,
  onCancel,
}: AgentChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (trimmed && !isDisabled) {
      onSend(trimmed);
      setValue("");
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  }, [value, isDisabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setValue(e.target.value);
      // Auto-resize textarea
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
      }
    },
    []
  );

  return (
    <Flex gap={2}>
      <Box flex={1}>
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your data map, privacy posture, or compliance status..."
          resize="none"
          minH="44px"
          maxH="200px"
          isDisabled={isDisabled}
          rows={1}
        />
      </Box>
      {onCancel ? (
        <Button
          colorScheme="red"
          variant="outline"
          onClick={onCancel}
          flexShrink={0}
        >
          Stop
        </Button>
      ) : (
        <Button
          colorScheme="primary"
          onClick={handleSend}
          isDisabled={isDisabled || !value.trim()}
          flexShrink={0}
        >
          Send
        </Button>
      )}
    </Flex>
  );
}
