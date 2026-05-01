import { Alert, Button, Input, SparkleIcon } from "fidesui";
import { useEffect, useRef, useState } from "react";

import type { ChatMessage, Status } from "./useFormBuilder";

interface ChatPaneProps {
  messages: ChatMessage[];
  status: Status;
  error: string | null;
  onSend: (text: string) => void;
  onAbort: () => void;
  // TODO: propagation-ready — wire up via a useGetLlmStatusQuery (or similar)
  // from FormBuilderPage once that query exists.
  disabled?: boolean;
  disabledReason?: string;
}

const rootStyle: React.CSSProperties = {
  height: "100%",
  display: "flex",
  flexDirection: "column",
  padding: 12,
  gap: 8,
  minHeight: 0,
};

const messagesStyle: React.CSSProperties = {
  flex: 1,
  minHeight: 0,
  overflowY: "auto",
  padding: 4,
};

const composerStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  flexShrink: 0,
};

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
  const messagesRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = messagesRef.current;
    if (!node) {
      return;
    }
    node.scrollTop = node.scrollHeight;
  }, [messages, isStreaming]);

  const handleSubmit = () => {
    if (!draft.trim() || isStreaming) {
      return;
    }
    onSend(draft.trim());
    setDraft("");
  };

  return (
    <div style={rootStyle}>
      {disabled && (
        <Alert
          type="info"
          title={disabledReason ?? "LLM provider not configured."}
        />
      )}
      {error && <Alert type="error" title={error} closable />}
      <div ref={messagesRef} style={messagesStyle}>
        {messages.map((m, idx) => (
          // eslint-disable-next-line react/no-array-index-key
          <div key={idx} data-role={m.role} style={{ padding: 8 }}>
            <strong>{m.role}: </strong>
            {m.content}
          </div>
        ))}
      </div>
      <div style={composerStyle}>
        <Input.TextArea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          disabled={isStreaming || disabled}
          placeholder="Tell the builder what you want…"
          autoSize={{ minRows: 2, maxRows: 6 }}
        />
        {isStreaming ? (
          <Button onClick={onAbort}>Stop</Button>
        ) : (
          <Button
            type="primary"
            icon={<SparkleIcon size={14} />}
            onClick={handleSubmit}
            disabled={disabled}
          >
            Send
          </Button>
        )}
      </div>
    </div>
  );
};
