import { Button, ButtonProps, Text } from "fidesui";
import { ReactElement } from "react";

const ActionButton = ({
  title,
  icon,
  onClick,
  disabled,
  variant = "outline",
  colorScheme = undefined,
}: {
  title: string;
  icon?: ReactElement;
  onClick: () => void;
  disabled?: boolean;
} & Pick<ButtonProps, "variant" | "colorScheme">) => (
  <Button
    size="xs"
    onClick={onClick}
    isDisabled={disabled}
    variant={variant}
    colorScheme={colorScheme}
    data-testid={`action-${title}`}
  >
    {icon}
    <Text marginLeft={icon && 1} fontWeight="semibold" fontSize={12}>
      {title}
    </Text>
  </Button>
);
export default ActionButton;
