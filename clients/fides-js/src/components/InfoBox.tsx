import { h, ComponentChild, ComponentChildren } from "preact";

const InfoBox = ({
  title,
  children,
}: {
  title: ComponentChild;
  children: ComponentChildren;
}) => (
  <div className="fides-info-box">
    <p className="fides-gpc-header">{title}</p>
    {children}
  </div>
);

export default InfoBox;
