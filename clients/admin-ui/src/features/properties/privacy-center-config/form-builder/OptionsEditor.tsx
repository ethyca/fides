import { Button, Icons, Input, Space } from "fidesui";

interface OptionsEditorProps {
  value?: string[];
  onChange?: (next: string[]) => void;
  /** Minimum number of options to keep. Below this, remove is disabled. */
  minItems?: number;
}

/** Editor for a list of string options. Used by Select / MultiSelect / Location. */
export const OptionsEditor = ({
  value = [],
  onChange,
  minItems = 1,
}: OptionsEditorProps) => {
  const setItem = (idx: number, next: string) => {
    const copy = [...value];
    copy[idx] = next;
    onChange?.(copy);
  };
  const remove = (idx: number) => {
    onChange?.(value.filter((_, i) => i !== idx));
  };
  const append = () => {
    onChange?.([...value, `Option ${value.length + 1}`]);
  };
  return (
    <Space orientation="vertical" className="w-full">
      {value.map((opt, idx) => (
        <Space.Compact
          // eslint-disable-next-line react/no-array-index-key
          key={idx}
          className="w-full"
        >
          <Input
            value={opt}
            onChange={(e) => setItem(idx, e.target.value)}
            data-testid={`option-input-${idx}`}
          />
          <Button
            onClick={() => remove(idx)}
            disabled={value.length <= minItems}
            data-testid={`option-remove-${idx}`}
            icon={<Icons.TrashCan />}
            aria-label={`Remove option ${idx + 1}`}
          />
        </Space.Compact>
      ))}
      <Button onClick={append} block data-testid="option-add">
        + Add option
      </Button>
    </Space>
  );
};
