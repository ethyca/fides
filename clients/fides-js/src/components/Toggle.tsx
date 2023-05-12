import { h } from "preact";

const Toggle = ({ name }: { name: string }) => (
  <label className="toggle" htmlFor={name}>
    <input type="checkbox" name={name} className="toggle-input" />
    {/* Mark as `hidden` so it will fall back to a regular checkbox if CSS is not available */}
    <span className="toggle-display" hidden />
  </label>
);

export default Toggle;
