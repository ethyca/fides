import { Badge } from "@fidesui/react";

import { BadgeCellContainer } from "~/features/common/table/v2/cells";
import { ApprovalStatus } from "~/types/api";

const statusColorMap: { [key in ApprovalStatus]: string } = {
  Approved: "green",
  Rejected: "red",
};

const ApprovalStatusBadge = ({ status }: { status?: ApprovalStatus }) => {
  if (!status) {
    return <Badge colorScheme="gray">Pending</Badge>;
  }
  return <Badge colorScheme={statusColorMap[status]}>{status}</Badge>;
};

const ApprovalStatusCell = ({ status }: { status?: ApprovalStatus }) => (
  <BadgeCellContainer>
    <ApprovalStatusBadge status={status} />
  </BadgeCellContainer>
);

export default ApprovalStatusCell;
