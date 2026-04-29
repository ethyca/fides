import { Alert, Button, Input, Space } from "fidesui";
import { useState } from "react";

import type { ChatMessage, Status } from "./useFormBuilder";

interface ChatPaneProps {
  messages: ChatMessage[];
  status: Status;
  error: string | null;
  onSend: (text: string) => void;
  onAbort: () => void;
}

export const ChatPane: React.FC<ChatPaneProps> = ({
  messages,
  status,
  error,
  onSend,
  onAbort,
}) => {
  const [draft, setDraft] = useState("");
  const isStreaming = status === "streaming";

  const handleSubmit = () => {
    if (!draft.trim() || isStreaming) {
      return;
    }
    onSend(draft.trim());
    setDraft("");
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }}>
      {error && <Alert type="error" message={error} closable />}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {messages.map((m, idx) => (
          // eslint-disable-next-line react/no-array-index-key
          <div key={idx} data-role={m.role} style={{ padding: 8 }}>
            <strong>{m.role}: </strong>
            {m.content}
          </div>
        ))}
      </div>
      <Input.TextArea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onPressEnter={(e) => {
          if (!e.shiftKey) {
            e.preventDefault();
            handleSubmit();
          }
        }}
        disabled={isStreaming}
        placeholder="Tell the builder what you want…"
        autoSize={{ minRows: 2, maxRows: 6 }}
      />
      {isStreaming ? (
        <Button onClick={onAbort}>Stop</Button>
      ) : (
        <Button type="primary" onClick={handleSubmit} disabled={!draft.trim()}>
          Send
        </Button>
      )}
    </Space>
  );
};
