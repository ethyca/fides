import { Alert, Input, Space, Tag } from "fidesui";
import { useState } from "react";

interface PathsEditorProps {
  value: string[];
  onChange: (next: string[]) => void;
}

export const PathsEditor: React.FC<PathsEditorProps> = ({
  value,
  onChange,
}) => {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleAdd = () => {
    const trimmed = draft.trim();
    if (!trimmed) {
      return;
    }
    if (value.includes(trimmed)) {
      setError(`"${trimmed}" already added`);
      return;
    }
    setError(null);
    onChange([...value, trimmed]);
    setDraft("");
  };

  const handleRemove = (path: string) => {
    onChange(value.filter((p) => p !== path));
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }}>
      <Space wrap>
        {value.map((path) => (
          <Tag key={path} closable onClose={() => handleRemove(path)}>
            {path}
          </Tag>
        ))}
      </Space>
      <Input
        placeholder="Add a path (e.g. /privacy)"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onPressEnter={(e) => {
          e.preventDefault();
          handleAdd();
        }}
      />
      {error && <Alert type="error" message={error} closable />}
    </Space>
  );
};
