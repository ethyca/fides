import { AntButton, AntButtonProps } from "fidesui";
import { ReactElement } from "react";

interface ActionButtonProps extends AntButtonProps {
  title: string;
  icon?: ReactElement;
}

const ActionButton = ({ title, icon, type, ...props }: ActionButtonProps) => (
  <AntButton
    size="small"
    type={type}
    data-testid={`action-${title}`}
    icon={icon}
    iconPosition="start"
    {...props}
  >
    {title}
  </AntButton>
);
export default ActionButton;
