/** @jsx createElement */
import { createElement } from "react";

const Toggle = ({
  name,
  id,
  checked,
  onChange,
}: {
  name: string;
  id: string;
  checked: boolean;
  onChange: (noticeId: string) => void;
}) => {
  const labelId = `toggle-${id}`;
  return (
    <label
      className="toggle"
      htmlFor={name}
      data-testid={`toggle-${name}`}
      id={labelId}
    >
      <input
        type="checkbox"
        name={name}
        className="toggle-input"
        onChange={() => {
          onChange(id);
        }}
        defaultChecked={checked}
        role="switch"
        aria-labelledby={labelId}
      />
      {/* Mark as `hidden` so it will fall back to a regular checkbox if CSS is not available */}
      <span className="toggle-display" hidden />
    </label>
  );
};

export default Toggle;
