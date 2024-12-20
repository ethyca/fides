import { Badge, BadgeProps } from "fidesui";

interface ResultStatusBadgeProps extends BadgeProps {
  colorScheme: string;
}

const ResultStatusBadge = ({ children, ...props }: ResultStatusBadgeProps) => {
  return (
    <Badge fontSize="xs" fontWeight="normal" textTransform="none" {...props}>
      {children}
    </Badge>
  );
};

export const DiscoveryStatusBadgeCell = ({
  withConsent,
}: {
  withConsent: boolean;
}) => {
  if (!withConsent) {
    return (
      <ResultStatusBadge colorScheme="red">Without consent</ResultStatusBadge>
    );
  }
  return (
    <ResultStatusBadge colorScheme="green">With consent</ResultStatusBadge>
  );
};
