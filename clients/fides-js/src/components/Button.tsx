import { FunctionComponent, h } from "preact";

import { ButtonType } from "../lib/consent-types";

interface ButtonProps {
  buttonType: ButtonType;
  label?: string;
  id?: string;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}

const Button: FunctionComponent<ButtonProps> = ({
  buttonType,
  label,
  id,
  onClick,
  className = "",
  disabled,
}) => (
  <button
    type="button"
    id={id}
    className={`fides-banner-button fides-banner-button-${buttonType.valueOf()} ${className}`}
    onClick={onClick}
    data-testid={`${label}-btn`}
    disabled={disabled}
  >
    {label || ""}
  </button>
);

export default Button;
