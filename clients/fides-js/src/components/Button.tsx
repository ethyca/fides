import { h, FunctionComponent } from "preact";
import { ButtonType } from "../lib/consent-types";

interface ButtonProps {
  buttonType: ButtonType;
  label?: string;
  onClick?: () => void;
  className?: string;
}

const Button: FunctionComponent<ButtonProps> = ({
  buttonType,
  label,
  onClick,
  className = "",
}) => (
  <button
    type="button"
    id={`fides-banner-button-${buttonType.valueOf()}`}
    className={`fides-banner-button fides-banner-button-${buttonType.valueOf()} ${className}`}
    onClick={onClick}
    data-testid={`${label}-btn`}
  >
    {label || ""}
  </button>
);

export default Button;
