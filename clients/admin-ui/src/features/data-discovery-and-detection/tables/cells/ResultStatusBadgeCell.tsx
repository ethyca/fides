import { AntTag as Tag, AntTagProps as TagProps } from "fidesui";

import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

const ResultStatusBadge = ({ children, ...props }: TagProps) => {
  return <Tag {...props}>{children}</Tag>;
};

const ResultStatusBadgeCell = ({
  result,
  changeTypeOverride,
}: {
  result: StagedResource;
  changeTypeOverride?: ResourceChangeType;
}) => {
  if (result.user_assigned_data_categories?.length) {
    return <ResultStatusBadge color="success">Reviewed</ResultStatusBadge>;
  }
  const changeType = changeTypeOverride ?? findResourceChangeType(result);
  switch (changeType) {
    case ResourceChangeType.MUTED:
      return <ResultStatusBadge color="marble">Unmonitored</ResultStatusBadge>;
    case ResourceChangeType.MONITORED:
      return <ResultStatusBadge color="success">Monitoring</ResultStatusBadge>;
    case ResourceChangeType.IN_PROGRESS:
      return <ResultStatusBadge color="info">Classifying</ResultStatusBadge>;
    default:
      return (
        <ResultStatusBadge color="warning">Pending review</ResultStatusBadge>
      );
  }
};

export default ResultStatusBadgeCell;
