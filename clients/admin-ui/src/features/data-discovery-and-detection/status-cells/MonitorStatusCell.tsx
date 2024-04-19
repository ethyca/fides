import { Badge } from "@fidesui/react";

import { BadgeCellContainer } from "~/features/common/table/v2/cells";
import { MonitorStatus } from "~/types/api";

const statusColorMap: { [key in MonitorStatus]: string } = {
  Monitored: "green",
  Muted: "gray",
};

const MonitorStatusBadge = ({ status }: { status?: MonitorStatus }) => {
  if (!status) {
    return <Badge colorScheme="yellow">Pending</Badge>;
  }
  return <Badge colorScheme={statusColorMap[status]}>{status}</Badge>;
};

const MonitorStatusCell = ({ status }: { status?: MonitorStatus }) => (
  <BadgeCellContainer>
    <MonitorStatusBadge status={status} />
  </BadgeCellContainer>
);

export default MonitorStatusCell;
