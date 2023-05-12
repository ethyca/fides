import { h, FunctionComponent } from "preact";
import { ButtonType } from "../lib/consent-types";

interface ButtonProps {
  buttonType: ButtonType;
  label?: string;
  onClick?: () => void;
}

const Button: FunctionComponent<ButtonProps> = ({
  buttonType,
  label,
  onClick,
}) => (
  <button
    type="button"
    id={`fides-consent-banner-button-${buttonType.valueOf()}`}
    className={`fides-consent-banner-button fides-consent-banner-button-${buttonType.valueOf()}`}
    onClick={onClick}
  >
    {label || ""}
  </button>
);

export default Button;
