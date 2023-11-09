import { h, FunctionComponent } from "preact";
import { ButtonType } from "../lib/consent-types";

interface ButtonProps {
  buttonType: ButtonType;
  label?: string;
  onClick?: () => void;
  id?: string;
}

const Button: FunctionComponent<ButtonProps> = ({
  buttonType,
  label,
  onClick,
  id,
}) => (
  <button
    type="button"
    id={id}
    className={`fides-banner-button fides-banner-button-${buttonType.valueOf()}`}
    onClick={onClick}
    data-testid={`${label}-btn`}
  >
    {label || ""}
  </button>
);

export default Button;
