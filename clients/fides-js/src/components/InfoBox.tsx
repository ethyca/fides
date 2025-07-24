import { ComponentChild, ComponentChildren } from "preact";

const InfoBox = ({
  title,
  isError,
  children,
}: {
  title?: ComponentChild;
  isError?: boolean;
  children: ComponentChildren;
}) => (
  <div
    className="fides-info-box"
    style={{
      backgroundColor: isError
        ? "var(--fides-overlay-background-error-color)"
        : undefined,
    }}
  >
    {title ? <p className="fides-gpc-header">{title}</p> : null}
    {children}
  </div>
);

export default InfoBox;
