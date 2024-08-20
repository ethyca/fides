import { Badge } from "fidesui";

import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

const ResultStatusBadgeCell = ({
  result,
  changeTypeOverride,
}: {
  result: StagedResource;
  changeTypeOverride?: ResourceChangeType;
}) => {
  const changeType = changeTypeOverride ?? findResourceChangeType(result);
  switch (changeType) {
    case ResourceChangeType.MUTED:
      return (
        <Badge fontSize="xs" colorScheme="gray">
          Unmonitored
        </Badge>
      );
    case ResourceChangeType.MONITORED:
      return (
        <Badge fontSize="xs" colorScheme="green">
          Monitoring
        </Badge>
      );
    default:
      return (
        <Badge fontSize="xs" colorScheme="orange">
          Pending review
        </Badge>
      );
  }
};

export default ResultStatusBadgeCell;
