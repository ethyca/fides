import { h } from "preact";

const Toggle = ({
  name,
  id,
  checked,
  onChange,
  disabled,
  onLabel,
  offLabel,
}: {
  name: string;
  id: string;
  checked: boolean;
  onChange: (noticeKey: string) => void;
  disabled?: boolean;
  onLabel?: string;
  offLabel?: string;
}) => {
  const labelText = checked ? onLabel : offLabel;
  return (
    <div className="fides-toggle" data-testid={`toggle-${name}`}>
      <input
        type="checkbox"
        aria-label={name}
        className="fides-toggle-input"
        onChange={() => {
          onChange(id);
        }}
        checked={checked}
        role="switch"
        disabled={disabled}
      />
      <span className="fides-toggle-display">{labelText}</span>
    </div>
  );
};

export default Toggle;
