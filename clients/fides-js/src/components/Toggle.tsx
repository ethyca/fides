import { FidesEventTargetType } from "../lib/events";
import { useEvent } from "../lib/providers/event-context";

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
  onChange: (noticeKey: string) => void;
  disabled?: boolean;
  onLabel?: string;
  offLabel?: string;
}) => {
  const { setTrigger } = useEvent();
  const labelText = checked ? onLabel : offLabel;
  return (
    <div className="fides-toggle" data-testid={`toggle-${label}`}>
      <input
        type="checkbox"
        name={name}
        aria-label={label}
        className="fides-toggle-input"
        onChange={() => {
          setTrigger({
            type: FidesEventTargetType.TOGGLE,
            label,
            checked: !checked,
          });
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
