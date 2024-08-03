import { ComponentChild, ComponentChildren, h } from "preact";

const InfoBox = ({
  title,
  children,
}: {
  title?: ComponentChild;
  children: ComponentChildren;
}) => (
  <div className="fides-info-box">
    {title ? <p className="fides-gpc-header">{title}</p> : null}
    {children}
  </div>
);

export default InfoBox;
