import { Button, Tooltip } from "fidesui";

interface RegexToggleProps {
  value?: boolean | null;
  onChange?: (value: boolean | null) => void;
}

const RegexToggle = ({ value, onChange }: RegexToggleProps) => {
  const isActive = !!value;

  return (
    <Tooltip
      title={
        isActive
          ? "Regex search enabled (matches name or URN)"
          : "Enable regex search"
      }
    >
      <Button
        aria-label="Toggle regex search"
        type={isActive ? "primary" : "default"}
        onClick={() => onChange?.(isActive ? null : true)}
        style={{ fontFamily: "monospace", fontWeight: "bold" }}
        data-testid="regex-toggle"
      >
        .*
      </Button>
    </Tooltip>
  );
};

export default RegexToggle;
