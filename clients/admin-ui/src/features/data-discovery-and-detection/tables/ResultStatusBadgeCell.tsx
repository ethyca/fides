import { Badge, BadgeProps } from "fidesui";

import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

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

const ResultStatusBadgeCell = ({
  result,
  changeTypeOverride,
}: {
  result: StagedResource;
  changeTypeOverride?: ResourceChangeType;
}) => {
  if (result.user_assigned_data_categories?.length) {
    return <ResultStatusBadge colorScheme="green">Reviewed</ResultStatusBadge>;
  }
  const changeType = changeTypeOverride ?? findResourceChangeType(result);
  switch (changeType) {
    case ResourceChangeType.MUTED:
      return (
        <ResultStatusBadge colorScheme="gray">Unmonitored</ResultStatusBadge>
      );
    case ResourceChangeType.MONITORED:
      return (
        <ResultStatusBadge colorScheme="green">Monitoring</ResultStatusBadge>
      );
    default:
      return (
        <ResultStatusBadge colorScheme="orange">
          Pending review
        </ResultStatusBadge>
      );
  }
};

export default ResultStatusBadgeCell;
