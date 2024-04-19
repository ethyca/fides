import { Badge } from "@fidesui/react";

import { BadgeCellContainer } from "~/features/common/table/v2/cells";
import { ClassificationStatus } from "~/types/api";

const statusColorMap: { [key in ClassificationStatus]: string } = {
  Created: "blue",
  Processing: "orange",
  Complete: "teal",
  Failed: "red",
  Reviewed: "green",
};

const ClassificationStatusBadge = ({
  status,
}: {
  status?: ClassificationStatus;
}) => {
  if (!status) {
    return <Badge colorScheme="gray">Not started</Badge>;
  }
  return <Badge colorScheme={statusColorMap[status]}>{status}</Badge>;
};

const ClassificationStatusCell = ({
  status,
}: {
  status?: ClassificationStatus;
}) => (
  <BadgeCellContainer>
    <ClassificationStatusBadge status={status} />
  </BadgeCellContainer>
);

export default ClassificationStatusCell;
