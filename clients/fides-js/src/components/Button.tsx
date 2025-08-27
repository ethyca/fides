import { FunctionComponent } from "preact";
import { useEffect } from "preact/hooks";

import { ButtonType } from "../lib/consent-types";
import { useAutoResetFlag } from "../lib/hooks";
import { CheckmarkFilledIcon } from "./CheckmarkFilledIcon";
import { Spinner } from "./Spinner";

interface ButtonProps {
  buttonType: ButtonType;
  label?: string;
  id?: string;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  loading?: boolean;
  complete?: boolean;
}

const Button: FunctionComponent<ButtonProps> = ({
  buttonType,
  label,
  id,
  onClick,
  className = "",
  disabled,
  loading,
  complete,
}) => {
  const { isActive: showComplete, activate, deactivate } = useAutoResetFlag();

  useEffect(() => {
    if (complete) {
      activate();
    } else {
      deactivate();
    }
  }, [activate, complete, deactivate]);

  return (
    <button
      type="button"
      id={id}
      className={`fides-banner-button fides-banner-button-${buttonType.valueOf()} ${className}`}
      onClick={onClick}
      data-testid={`${label}-btn`}
      disabled={disabled || loading}
      style={{ cursor: disabled || loading ? "not-allowed" : "pointer" }}
    >
      <span style={{ display: "flex", alignItems: "center", gap: "0.5em" }}>
        {label || ""}
        {loading && <Spinner />}
        {!loading && showComplete && (
          <span aria-hidden="true" style={{ width: "1em", height: "1em" }}>
            <CheckmarkFilledIcon />
          </span>
        )}
      </span>
    </button>
  );
};

export default Button;
