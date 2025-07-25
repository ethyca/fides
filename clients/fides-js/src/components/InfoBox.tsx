import { ComponentChild, ComponentChildren, ComponentProps } from "preact";

const InfoBox = ({
  title,
  children,
  ...props
}: {
  title?: ComponentChild;
  children: ComponentChildren;
} & ComponentProps<"div">) => (
  <div className="fides-info-box" {...props}>
    {!!title && <p className="fides-gpc-header">{title}</p>}
    {children}
  </div>
);

export default InfoBox;
