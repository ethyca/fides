import { Alert, Button, Input, Space, Tag } from "fidesui";
import { useState } from "react";

interface PathsEditorProps {
  value: string[];
  onChange: (next: string[]) => void;
}

export const PathsEditor = ({ value, onChange }: PathsEditorProps) => {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const commitDraft = () => {
    const trimmed = draft.trim();
    if (!trimmed) {
      return;
    }
    const normalized = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
    if (value.includes(normalized)) {
      setError(`"${normalized}" already added`);
      return;
    }
    setError(null);
    onChange([...value, normalized]);
    setDraft("");
  };

  const handleRemove = (path: string) => {
    onChange(value.filter((p) => p !== path));
  };

  return (
    <Space orientation="vertical" style={{ width: "100%" }}>
      <Space wrap>
        {value.map((path) => (
          <Tag key={path} closable onClose={() => handleRemove(path)}>
            {path}
          </Tag>
        ))}
      </Space>
      <Space.Compact className="w-full">
        <Input
          placeholder="Add a path (e.g. /privacy)"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onPressEnter={(e) => {
            e.preventDefault();
            commitDraft();
          }}
          onBlur={commitDraft}
        />
        <Button onClick={commitDraft} disabled={!draft.trim()}>
          Add
        </Button>
      </Space.Compact>
      {error && <Alert type="error" description={error} closable />}
    </Space>
  );
};
