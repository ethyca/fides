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
  const labelId = `toggle-${id}`;
  const labelText = checked ? onLabel : offLabel;
  return (
    <label
      className="fides-toggle"
      htmlFor={name}
      data-testid={`toggle-${name}`}
      id={labelId}
    >
      <input
        type="checkbox"
        name={name}
        className="fides-toggle-input"
        onChange={() => {
          onChange(id);
        }}
        checked={checked}
        role="switch"
        aria-labelledby={labelId}
        disabled={disabled}
      />
      <span className="fides-toggle-display">{labelText}</span>
    </label>
  );
};

export default Toggle;
