import { Badge } from "fidesui";

interface ConnectionBadgeProps {
  disabled: boolean;
}

const ConnectionStatusBadge = ({ disabled }: ConnectionBadgeProps) => {
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
