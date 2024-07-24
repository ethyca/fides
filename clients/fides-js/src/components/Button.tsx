import { FunctionComponent, h } from "preact";

import { ButtonType } from "../lib/consent-types";

interface ButtonProps {
  buttonType: ButtonType;
  label?: string;
  id?: string;
  onClick?: () => void;
  className?: string;
}

const Button: FunctionComponent<ButtonProps> = ({
  buttonType,
  label,
  id,
  onClick,
  className = "",
}) => (
  <button
    type="button"
    id={id}
    className={`fides-banner-button fides-banner-button-${buttonType.valueOf()} ${className}`}
    onClick={onClick}
    data-testid={`${label}-btn`}
  >
    {label || ""}
  </button>
);

export default Button;
