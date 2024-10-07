import { AntButton as Button, AntButtonProps as ButtonProps } from "fidesui";
import { ReactElement } from "react";

interface ActionButtonProps extends ButtonProps {
  title: string;
  icon?: ReactElement;
}

const ActionButton = ({ title, icon, type, ...props }: ActionButtonProps) => (
  <Button
    size="small"
    type={type}
    data-testid={`action-${title}`}
    icon={icon}
    iconPosition="start"
    {...props}
  >
    {title}
  </Button>
);
export default ActionButton;
