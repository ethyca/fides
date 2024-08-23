import { Button, ButtonProps } from "fidesui";
import { ReactElement } from "react";

interface ActionButtonProps extends ButtonProps {
  title: string;
  icon?: ReactElement;
}

const ActionButton = ({
  title,
  icon,
  variant = "outline",
  ...props
}: ActionButtonProps) => (
  <Button
    size="xs"
    variant={variant}
    data-testid={`action-${title}`}
    loadingText={title}
    leftIcon={icon}
    {...props}
  >
    {title}
  </Button>
);
export default ActionButton;
