import { Button, Text } from "@fidesui/react";
import { ReactElement } from "react";

const ActionButton = ({
  title,
  icon,
  onClick,
  disabled,
}: {
  title: string;
  icon: ReactElement;
  onClick: () => void;
  disabled?: boolean;
}) => (
  <Button size="xs" variant="outline" onClick={onClick} disabled={disabled}>
    {icon}
    <Text marginLeft={1} fontWeight="semibold" fontSize={12}>
      {title}
    </Text>
  </Button>
);
export default ActionButton;
