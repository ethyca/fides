import { FunctionComponent, h } from "preact";

import { ButtonType } from "../lib/consent-types";
import { Spinner } from "./Spinner";

interface ButtonProps {
  buttonType: ButtonType;
  label?: string;
  id?: string;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  loading?: boolean;
}

const Button: FunctionComponent<ButtonProps> = ({
  buttonType,
  label,
  id,
  onClick,
  className = "",
  disabled,
  loading,
}) => (
  <button
    type="button"
    id={id}
    className={`fides-banner-button fides-banner-button-${buttonType.valueOf()} ${className}`}
    onClick={onClick}
    data-testid={`${label}-btn`}
    disabled={disabled || loading}
    style={{ cursor: disabled || loading ? "not-allowed" : "pointer" }}
  >
    {label || ""}
    {loading && <Spinner />}
  </button>
);

export default Button;
