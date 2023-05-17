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
}) => (
  <label className="toggle" htmlFor={name} data-testid={`toggle-${name}`}>
    <input
      type="checkbox"
      name={name}
      className="toggle-input"
      onChange={() => {
        onChange(id);
      }}
      checked={checked}
      role="switch"
    />
    {/* Mark as `hidden` so it will fall back to a regular checkbox if CSS is not available */}
    <span className="toggle-display" hidden />
  </label>
);

export default Toggle;
