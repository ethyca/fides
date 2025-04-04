import { h } from "preact";

import { FidesEventDetailsTrigger } from "../lib/events";

const Toggle = ({
  label,
  name,
  id,
  checked,
  onChange,
  disabled,
  onLabel,
  offLabel,
}: {
  label: string;
  name: string;
  id: string;
  checked: boolean;
  onChange: (
    noticeKey: string,
    triggerDetails: FidesEventDetailsTrigger,
  ) => void;
  disabled?: boolean;
  onLabel?: string;
  offLabel?: string;
}) => {
  const labelText = checked ? onLabel : offLabel;
  return (
    <div className="fides-toggle" data-testid={`toggle-${label}`}>
      <input
        type="checkbox"
        name={name}
        aria-label={label}
        className="fides-toggle-input"
        onChange={() => {
          onChange(id, {
            type: "toggle",
            label,
            checked: !checked,
          });
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
