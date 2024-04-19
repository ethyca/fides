import { Badge } from "@fidesui/react";

import { BadgeCellContainer } from "~/features/common/table/v2/cells";
import { DiffStatus } from "~/types/api";

const statusColorMap: { [key in DiffStatus]: string } = {
  Addition: "green",
  Removal: "red",
  Modification: "orange",
};

const DiffStatusBadge = ({ status }: { status?: DiffStatus }) => {
  if (!status) {
    return null;
  }
  return <Badge colorScheme={statusColorMap[status]}>{status}</Badge>;
};

const DiffStatusCell = ({ status }: { status?: DiffStatus }) => (
  <BadgeCellContainer>
    <DiffStatusBadge status={status} />
  </BadgeCellContainer>
);

export default DiffStatusCell;
