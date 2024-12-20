import { AntTooltip as Tooltip, Badge, BadgeProps } from "fidesui";

import { formatDate } from "~/features/common/utils";

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

interface DiscoveryStatusBadgeCellProps {
  withConsent: boolean;
  dateDiscovered: string | null | undefined;
}

export const DiscoveryStatusBadgeCell = ({
  withConsent,
  dateDiscovered,
}: DiscoveryStatusBadgeCellProps) => {
  return (
    <Tooltip title={dateDiscovered ? formatDate(dateDiscovered) : undefined}>
      {withConsent ? (
        <ResultStatusBadge colorScheme="green">With consent</ResultStatusBadge>
      ) : (
        <ResultStatusBadge colorScheme="red">Without consent</ResultStatusBadge>
      )}
    </Tooltip>
  );
};
