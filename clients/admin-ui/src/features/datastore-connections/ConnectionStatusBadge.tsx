import { Badge } from "@fidesui/react";

interface ConnectionBadgeProps {
  disabled: boolean;
}

const ConnectionStatusBadge: React.FC<ConnectionBadgeProps> = ({
  disabled,
}) => {
  const background = disabled ? "gray.500" : "green.500";
  const label = disabled ? "DISABLED" : "ACTIVE";
  return (
    <Badge
      color="white"
      bg={background}
      height="18px"
      lineHeight="18px"
      textAlign="center"
      borderRadius="2px"
      mr="4px"
    >
      {label}
    </Badge>
  );
};

export default ConnectionStatusBadge;
