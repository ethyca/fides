import { Button, ButtonProps } from "fidesui";
import { ReactElement } from "react";

interface ActionButtonProps extends ButtonProps {
  title: string;
  icon?: ReactElement;
}

const ActionButton = ({
  title,
  icon,
  onClick,
  isDisabled,
  isLoading,
  variant = "outline",
  colorScheme = undefined,
}: ActionButtonProps) => (
  <Button
    size="xs"
    onClick={onClick}
    isDisabled={isDisabled}
    variant={variant}
    colorScheme={colorScheme}
    data-testid={`action-${title}`}
    isLoading={isLoading}
    loadingText={title}
    leftIcon={icon}
  >
    {title}
  </Button>
);
export default ActionButton;
